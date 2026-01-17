"""사람인 크롤러 단위 테스트."""

from unittest.mock import AsyncMock

import pytest

from crawlers.exceptions import CrawlerBlockedError
from crawlers.models import JobPosting, JobSource
from crawlers.saramin import SaraminCrawler


class TestSaraminCrawlerParsing:
    """사람인 크롤러 파싱 로직 테스트."""

    @pytest.fixture
    def crawler(self):
        """SaraminCrawler 인스턴스."""
        return SaraminCrawler()

    @pytest.fixture
    def mock_job_card(self):
        """Mock 채용공고 카드 요소."""
        async def create_mock_card(
            title="테스트 개발자",
            company="테스트회사",
            url="/job/123",
            location="서울",
            experience="3년",
            skills=None,
            deadline="~12/31",
        ):
            if skills is None:
                skills = ["Python", "Django"]

            mock_card = AsyncMock()

            title_el = AsyncMock()
            title_el.inner_text = AsyncMock(return_value=title)
            title_el.get_attribute = AsyncMock(return_value=url)

            company_el = AsyncMock()
            company_el.inner_text = AsyncMock(return_value=company)

            location_el = AsyncMock()
            location_el.inner_text = AsyncMock(return_value=location)

            experience_el = AsyncMock()
            experience_el.inner_text = AsyncMock(return_value=experience)

            skill_els = [AsyncMock() for _ in skills]
            for skill_el, skill in zip(skill_els, skills, strict=True):
                skill_el.inner_text = AsyncMock(return_value=skill)

            deadline_el = AsyncMock()
            deadline_el.inner_text = AsyncMock(return_value=deadline)

            mock_card.query_selector = AsyncMock(
                side_effect=lambda sel: {
                    ".job_tit a": title_el,
                    ".corp_name a": company_el,
                    ".job_date .date": deadline_el,
                }.get(sel)
            )

            mock_card.query_selector_all = AsyncMock(
                side_effect=lambda sel: {
                    ".job_condition span": [location_el, experience_el],
                    ".job_sector span": skill_els,
                }.get(sel, [])
            )

            return mock_card

        return create_mock_card

    async def test_extract_job_success(self, crawler, mock_job_card):
        """채용공고 추출 성공 테스트."""
        card = await mock_job_card()
        job = await crawler._extract_job(card)

        assert job is not None
        assert isinstance(job, JobPosting)
        assert job.title == "테스트 개발자"
        assert job.company == "테스트회사"
        assert job.source == JobSource.SARAMIN
        assert "Python" in job.skills

    async def test_extract_job_with_full_url(self, crawler, mock_job_card):
        """전체 URL 채용공고 추출 테스트."""
        card = await mock_job_card(url="https://www.saramin.co.kr/job/456")
        job = await crawler._extract_job(card)

        assert job.url == "https://www.saramin.co.kr/job/456"

    async def test_extract_job_with_relative_url(self, crawler, mock_job_card):
        """상대 URL 채용공고 추출 테스트."""
        card = await mock_job_card(url="/job/789")
        job = await crawler._extract_job(card)

        assert job.url == "https://www.saramin.co.kr/job/789"

    async def test_extract_job_skill_limit(self, crawler, mock_job_card):
        """스킬 개수 제한 테스트."""
        many_skills = ["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "Docker", "K8s"]
        card = await mock_job_card(skills=many_skills)
        job = await crawler._extract_job(card)

        assert len(job.skills) <= crawler.MAX_SKILLS_COUNT

    async def test_check_blocked_captcha(self, crawler):
        """CAPTCHA 차단 감지 테스트."""
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html>captcha required</html>")

        with pytest.raises(CrawlerBlockedError):
            await crawler._check_blocked(mock_page)

    async def test_check_blocked_access_denied(self, crawler):
        """접근 차단 감지 테스트."""
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html>access denied</html>")

        with pytest.raises(CrawlerBlockedError):
            await crawler._check_blocked(mock_page)

    async def test_check_blocked_normal_page(self, crawler):
        """정상 페이지 차단 미감지 테스트."""
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html>normal job listing page</html>")

        await crawler._check_blocked(mock_page)
