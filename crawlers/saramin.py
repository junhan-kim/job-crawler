"""사람인 크롤러 구현."""

import logging
import time
from urllib.parse import quote

from .base import BaseCrawler
from .browser import get_browser_pool
from .exceptions import CrawlerBlockedError
from .models import JobPosting, JobSource
from .utils import rate_limiter, retry_on_timeout

logger = logging.getLogger(__name__)


class SaraminCrawler(BaseCrawler):
    """사람인 채용공고 크롤러."""

    BASE_URL = "https://www.saramin.co.kr"
    SEARCH_URL = f"{BASE_URL}/zf_user/search/recruit"

    TIMEOUT_MS = 60000
    PAGE_LOAD_WAIT_MS = 2000
    MAX_SKILLS_COUNT = 5

    SELECTORS = {
        "job_card": ".item_recruit",
        "title": ".job_tit a",
        "company": ".corp_name a",
        "conditions": ".job_condition span",
        "skills": ".job_sector span",
        "deadline": ".job_date .date",
    }

    BLOCK_INDICATORS = [
        "captcha",
        "자동화된 접근",
        "접근이 차단",
        "access denied",
        "please verify",
    ]

    LOCATIONS = [
        "서울", "경기", "부산", "대구", "인천", "광주", "대전", "울산",
        "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
    ]

    SKILL_EXCLUDE_KEYWORDS = ["등록일", "수정일", "외", "/"]
    EXPERIENCE_KEYWORDS = ["년", "신입", "경력"]

    @property
    def source(self) -> JobSource:
        return JobSource.SARAMIN

    @retry_on_timeout
    async def search(self, keyword: str, page: int = 1) -> list[JobPosting]:
        """
        사람인에서 채용공고 검색.

        Args:
            keyword: 검색 키워드
            page: 크롤링할 페이지 번호

        Returns:
            JobPosting 리스트

        Raises:
            CrawlerBlockedError: 차단 감지 시
        """
        t0 = time.perf_counter()
        pool = await get_browser_pool()
        logger.debug(f"[TIMING] get_browser_pool: {time.perf_counter() - t0:.2f}s")

        t1 = time.perf_counter()
        context = await pool.get_context()
        logger.debug(f"[TIMING] get_context: {time.perf_counter() - t1:.2f}s")

        try:
            t2 = time.perf_counter()
            browser_page = await context.new_page()
            logger.debug(f"[TIMING] new_page: {time.perf_counter() - t2:.2f}s")

            t3 = time.perf_counter()
            await self._apply_stealth(browser_page)
            logger.debug(f"[TIMING] apply_stealth: {time.perf_counter() - t3:.2f}s")

            async with rate_limiter:
                jobs = await self._crawl_single_page(browser_page, keyword, page)
        finally:
            await context.close()

        logger.info(f"Total jobs collected: {len(jobs)}")
        return jobs

    async def _crawl_single_page(
        self, browser_page, keyword: str, page: int
    ) -> list[JobPosting]:
        """단일 페이지 크롤링."""
        url = f"{self.SEARCH_URL}?searchword={quote(keyword)}&recruitPage={page}"
        logger.info(f"Crawling page {page}: {url}")

        t0 = time.perf_counter()
        await browser_page.goto(url, timeout=self.TIMEOUT_MS, wait_until="domcontentloaded")
        logger.debug(f"[TIMING] page.goto: {time.perf_counter() - t0:.2f}s")

        t1 = time.perf_counter()
        await browser_page.wait_for_selector(
            self.SELECTORS["job_card"], timeout=self.PAGE_LOAD_WAIT_MS
        )
        logger.debug(f"[TIMING] wait_for_selector: {time.perf_counter() - t1:.2f}s")

        t2 = time.perf_counter()
        await self._check_blocked(browser_page)
        logger.debug(f"[TIMING] check_blocked: {time.perf_counter() - t2:.2f}s")

        t3 = time.perf_counter()
        items = await browser_page.query_selector_all(self.SELECTORS["job_card"])
        logger.debug(f"[TIMING] query_selector_all: {time.perf_counter() - t3:.2f}s")
        logger.info(f"Found {len(items)} job cards")

        jobs = []
        for item in items:
            job = await self._extract_job(item)
            if job and job.title:
                jobs.append(job)

        return jobs

    async def _check_blocked(self, browser_page) -> None:
        """차단 여부 확인."""
        content = await browser_page.content()
        content_lower = content.lower()

        for indicator in self.BLOCK_INDICATORS:
            if indicator in content_lower:
                logger.warning(f"Block indicator detected: {indicator}")
                raise CrawlerBlockedError(self.source_name, f"Detected: {indicator}")

    async def _extract_job(self, item) -> JobPosting | None:
        """채용공고 카드에서 정보 추출."""
        try:
            title, url = await self._extract_title_and_url(item)
            company = await self._extract_company(item)
            location, experience = await self._extract_conditions(item)
            skills = await self._extract_skills(item)
            deadline = await self._extract_deadline(item)

            return JobPosting(
                title=title,
                company=company,
                location=location,
                experience=experience,
                skills=skills[:self.MAX_SKILLS_COUNT],
                deadline=deadline,
                url=url,
                source=self.source,
            )
        except Exception as e:
            logger.warning(f"Failed to extract job: {e}")
            return None

    async def _extract_title_and_url(self, item) -> tuple[str, str]:
        """제목과 URL 추출."""
        title_el = await item.query_selector(self.SELECTORS["title"])
        title = (await title_el.inner_text()).strip() if title_el else ""
        url = await title_el.get_attribute("href") if title_el else ""
        if url and not url.startswith("http"):
            url = self.BASE_URL + url
        return title, url

    async def _extract_company(self, item) -> str:
        """회사명 추출."""
        company_el = await item.query_selector(self.SELECTORS["company"])
        return (await company_el.inner_text()).strip() if company_el else ""

    async def _extract_conditions(self, item) -> tuple[str, str]:
        """지역과 경력 추출."""
        location = ""
        experience = ""
        conditions = await item.query_selector_all(self.SELECTORS["conditions"])

        for cond in conditions:
            text = (await cond.inner_text()).strip()
            if any(loc in text for loc in self.LOCATIONS):
                location = text
            elif any(kw in text for kw in self.EXPERIENCE_KEYWORDS):
                experience = text

        return location, experience

    async def _extract_skills(self, item) -> list[str]:
        """스킬 목록 추출."""
        skills = []
        skill_els = await item.query_selector_all(self.SELECTORS["skills"])

        for el in skill_els:
            skill = (await el.inner_text()).strip()
            if skill and not any(x in skill for x in self.SKILL_EXCLUDE_KEYWORDS):
                skills.append(skill)

        return skills

    async def _extract_deadline(self, item) -> str:
        """마감일 추출."""
        deadline_el = await item.query_selector(self.SELECTORS["deadline"])
        return (await deadline_el.inner_text()).strip() if deadline_el else ""
