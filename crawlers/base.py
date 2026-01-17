"""크롤러 추상 베이스 클래스."""

from abc import ABC, abstractmethod

from django.conf import settings
from playwright.async_api import Browser, BrowserContext, Page
from playwright_stealth import Stealth

from .models import JobPosting, JobSource
from .utils import get_random_user_agent

VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080


class BaseCrawler(ABC):
    """크롤러 추상 베이스 클래스."""

    @property
    @abstractmethod
    def source(self) -> JobSource:
        """크롤러 소스."""
        pass

    @property
    def source_name(self) -> str:
        """크롤러 소스 이름."""
        return self.source.value

    @abstractmethod
    async def search(self, keyword: str, max_pages: int = 1) -> list[JobPosting]:
        """
        키워드로 채용 공고 검색.

        Args:
            keyword: 검색 키워드
            max_pages: 크롤링할 최대 페이지 수

        Returns:
            JobPosting 리스트
        """
        pass

    async def _launch_browser(self, playwright) -> Browser:
        """브라우저 실행."""
        return await playwright.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )

    async def _create_context(self, browser: Browser) -> BrowserContext:
        """브라우저 컨텍스트 생성."""
        return await browser.new_context(
            user_agent=get_random_user_agent(),
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
            locale=settings.CRAWLER_LOCALE,
            timezone_id=settings.CRAWLER_TIMEZONE,
        )

    async def _apply_stealth(self, page: Page) -> None:
        """Stealth 모드 적용."""
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
