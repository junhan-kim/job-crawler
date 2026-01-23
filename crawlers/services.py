"""크롤러 서비스."""

import asyncio
import logging

from django.conf import settings

from apps.jobs.services import JobService

from .jobkorea import JobKoreaCrawler
from .models import JobPosting, SearchFilters
from .saramin import SaraminCrawler

logger = logging.getLogger(__name__)


class CrawlerService:
    """
    크롤러 서비스.

    크롤링, 필터링, DB 저장을 담당하는 단일 진입점.
    """

    async def crawl_page(
        self,
        keyword: str,
        page: int = 1,
        filters: SearchFilters | None = None,
        save_to_db: bool = True,
    ) -> tuple[list[JobPosting], list[int]]:
        """
        단일 페이지 크롤링 (사람인 + 잡코리아 병렬).

        Args:
            keyword: 검색 키워드
            page: 페이지 번호
            filters: 검색 필터 (experience, location)
            save_to_db: DB 저장 여부

        Returns:
            (크롤링된 채용 공고 목록, 저장된 job ID 목록)
        """
        all_results = await self._crawl_from_sites(keyword, page)

        job_ids: list[int] = []
        if save_to_db and settings.DB_SAVE_ENABLED and all_results:
            job_ids = await self._save_to_db(all_results)

        if filters:
            all_results = self._apply_filters(all_results, filters)

        return all_results, job_ids

    async def _crawl_from_sites(self, keyword: str, page: int) -> list[JobPosting]:
        """사람인 + 잡코리아 병렬 크롤링."""
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

    async def _save_to_db(self, jobs: list[JobPosting]) -> list[int]:
        """크롤링 결과를 DB에 저장하고 저장된 job ID 반환."""
        job_service = JobService()

        try:
            _, job_ids = await job_service.save_batch(jobs, skip_embedding=True)
            return job_ids
        except Exception as error:
            logger.warning(f"Failed to save jobs to DB: {error}")
            return []

    def _apply_filters(
        self, jobs: list[JobPosting], filters: SearchFilters
    ) -> list[JobPosting]:
        """크롤링 결과에 필터 적용."""
        results = jobs

        if filters.location:
            results = [
                job for job in results
                if job.location and filters.location in job.location
            ]

        if filters.experience is not None:
            results = [
                job for job in results
                if SearchFilters.matches_experience(job.experience, filters.experience)
            ]

        return results
