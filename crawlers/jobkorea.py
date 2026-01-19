"""잡코리아 크롤러 구현."""

import logging
import re
from urllib.parse import quote

from .base import BaseCrawler
from .browser import get_browser_pool
from .exceptions import CrawlerBlockedError
from .models import JobPosting, JobSource
from .utils import rate_limiter, retry_on_timeout

logger = logging.getLogger(__name__)


class JobKoreaCrawler(BaseCrawler):
    """잡코리아 채용공고 크롤러."""

    BASE_URL = "https://www.jobkorea.co.kr"
    SEARCH_URL = f"{BASE_URL}/Search/"

    TIMEOUT_MS = 90000
    PAGE_LOAD_WAIT_MS = 3000

    MIN_TITLE_LENGTH = 5
    RAW_TEXT_MAX_LENGTH = 500

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

    COMPANY_PREFIXES = ["㈜", "(주)", "주식회사"]
    DEADLINE_PATTERN = re.compile(r"(\d{2}/\d{2})\([월화수목금토일]\)")
    EXPERIENCE_YEAR_PATTERN = re.compile(r"경력\s*(\d+)년")

    JS_EXTRACT_JOBS = """
        () => {
            const jobs = [];
            const seen = new Set();
            const links = document.querySelectorAll('a[href*="/Recruit/GI_Read/"]');

            links.forEach(link => {
                const href = link.href;
                const match = href.match(/GI_Read\\/([0-9]+)/);
                if (!match) return;

                const jobId = match[1];
                if (seen.has(jobId)) return;

                const title = link.innerText?.trim() || '';
                if (!title || title.length < 5) return;
                if (title.startsWith('㈜') || title.startsWith('(주)') || title.startsWith('주식회사')) return;

                seen.add(jobId);

                let container = link.parentElement;
                for (let i = 0; i < 5 && container; i++) {
                    container = container.parentElement;
                }

                const allText = container?.innerText || '';

                let company = '';
                const companyLink = container?.querySelector('a[href*="/company/"]');
                if (companyLink) {
                    company = companyLink.innerText?.trim() || '';
                }

                jobs.push({
                    title: title,
                    company: company,
                    url: href,
                    rawText: allText.substring(0, 500)
                });
            });

            return jobs;
        }
    """

    @property
    def source(self) -> JobSource:
        return JobSource.JOBKOREA

    @retry_on_timeout
    async def search(self, keyword: str, page: int = 1) -> list[JobPosting]:
        """
        잡코리아에서 채용공고 검색.

        Args:
            keyword: 검색 키워드
            page: 크롤링할 페이지 번호

        Returns:
            JobPosting 리스트

        Raises:
            CrawlerBlockedError: 차단 감지 시
        """
        pool = await get_browser_pool()
        context = await pool.get_context()

        try:
            browser_page = await context.new_page()
            await self._apply_stealth(browser_page)

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
        url = f"{self.SEARCH_URL}?stext={quote(keyword)}&Page_No={page}"
        logger.info(f"Crawling page {page}: {url}")

        await browser_page.goto(url, timeout=self.TIMEOUT_MS, wait_until="domcontentloaded")
        await browser_page.wait_for_timeout(self.PAGE_LOAD_WAIT_MS)

        await self._check_blocked(browser_page)

        job_data_list = await browser_page.evaluate(self.JS_EXTRACT_JOBS)
        logger.info(f"Found {len(job_data_list)} job cards")

        jobs = []
        for data in job_data_list:
            job = self._parse_job_data(data)
            if job:
                jobs.append(job)

        return jobs

    async def _check_blocked(self, browser_page) -> None:
        """차단 여부 확인."""
        content = await browser_page.content()
        content_lower = content.lower()

        for indicator in self.BLOCK_INDICATORS:
            if indicator in content_lower:
                logger.warning(f"Block indicator detected: {indicator}")
                raise CrawlerBlockedError(self.source.value, f"Detected: {indicator}")

    def _parse_job_data(self, data: dict) -> JobPosting | None:
        """JS에서 추출한 데이터를 JobPosting으로 변환."""
        try:
            raw = data.get("rawText", "")

            location = self._extract_location(raw)
            experience = self._extract_experience(raw)
            deadline = self._extract_deadline(raw)

            return JobPosting(
                title=data.get("title", ""),
                company=data.get("company", ""),
                location=location,
                experience=experience,
                skills=[],
                deadline=deadline,
                url=data.get("url", ""),
                source=self.source,
            )
        except Exception as e:
            logger.warning(f"Failed to parse job: {e}")
            return None

    def _extract_location(self, raw: str) -> str:
        """지역 추출."""
        for loc in self.LOCATIONS:
            if loc in raw:
                return loc
        return ""

    def _extract_experience(self, raw: str) -> str:
        """경력 추출."""
        if "신입" in raw and "경력" in raw:
            return "신입/경력"
        if "신입" in raw:
            return "신입"
        if "경력" in raw:
            match = self.EXPERIENCE_YEAR_PATTERN.search(raw)
            if match:
                return f"경력 {match.group(1)}년↑"
            return "경력"
        return ""

    def _extract_deadline(self, raw: str) -> str:
        """마감일 추출."""
        match = self.DEADLINE_PATTERN.search(raw)
        if match:
            return f"~ {match.group(0)}"
        return ""
