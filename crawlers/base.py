"""크롤러 추상 베이스 클래스."""

from abc import ABC, abstractmethod

from playwright.async_api import Page
from playwright_stealth import Stealth

from .models import JobPosting, JobSource


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
    async def search(self, keyword: str, page: int = 1) -> list[JobPosting]:
        """
        키워드로 채용 공고 검색.

        Args:
            keyword: 검색 키워드
            page: 크롤링할 페이지 번호

        Returns:
            JobPosting 리스트
        """
        pass

    async def _apply_stealth(self, page: Page) -> None:
        """Stealth 모드 적용."""
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
