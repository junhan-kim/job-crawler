"""크롤러 서비스."""

import asyncio
import logging

from .jobkorea import JobKoreaCrawler
from .models import JobPosting
from .saramin import SaraminCrawler

logger = logging.getLogger(__name__)


class CrawlerService:
    """크롤러 서비스 - 여러 사이트 병렬 크롤링."""

    async def crawl_page(self, keyword: str, page: int = 1) -> list[JobPosting]:
        """
        단일 페이지 크롤링 (사람인 + 잡코리아 병렬).

        Args:
            keyword: 검색 키워드
            page: 페이지 번호

        Returns:
            크롤링된 채용 공고 목록
        """
        saramin_crawler = SaraminCrawler()
        jobkorea_crawler = JobKoreaCrawler()

        saramin_results, jobkorea_results = await asyncio.gather(
            saramin_crawler.search(keyword, page=page),
            jobkorea_crawler.search(keyword, page=page),
            return_exceptions=True,
        )

        all_results: list[JobPosting] = []

        if isinstance(saramin_results, Exception):
            logger.error(f"Saramin crawler error: {saramin_results}")
        else:
            all_results.extend(saramin_results)

        if isinstance(jobkorea_results, Exception):
            logger.error(f"JobKorea crawler error: {jobkorea_results}")
        else:
            all_results.extend(jobkorea_results)

        return all_results
