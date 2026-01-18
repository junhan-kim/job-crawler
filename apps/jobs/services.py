import hashlib
import logging
import os

from crawlers.models import JobPosting as CrawlerJobPosting

from .models import JobPosting
from .types import JobAction, SaveResult, SaveResultKey

logger = logging.getLogger(__name__)

EMBEDDING_ENABLED = bool(os.getenv("DB_HOST"))


class JobService:
    """채용공고 저장 및 관리 서비스."""

    def __init__(self):
        self._embedding_service = None

    def _get_embedding_service(self):
        """EmbeddingService lazy init."""
        if self._embedding_service is None and EMBEDDING_ENABLED:
            from core.embedding_service import EmbeddingService

            self._embedding_service = EmbeddingService()
        return self._embedding_service

    def _generate_source_id(self, job_input: CrawlerJobPosting) -> str:
        """
        source_id 생성.

        URL 기반 해시로 고유 ID 생성.
        MD5 해시 사용 이유: 같은 공고 재크롤링 시 동일 ID 보장 (멱등성).
        """
        return hashlib.md5(job_input.url.encode()).hexdigest()[:16]

    async def save_job(
        self,
        job_input: CrawlerJobPosting,
    ) -> tuple[JobPosting, bool]:
        """
        크롤링 결과를 DB에 저장.

        Args:
            job_input: 크롤링된 채용공고 데이터

        Returns:
            (JobPosting, created) 튜플
        """
        source_id = self._generate_source_id(job_input)

        job, created = await JobPosting.objects.aupdate_or_create(
            source=job_input.source,
            source_id=source_id,
            defaults=job_input.to_django_defaults(),
        )

        if created or job.embedding is None:
            await self._generate_embedding(job)

        action = JobAction.CREATED if created else JobAction.UPDATED
        logger.debug(f"{action} job: [{job_input.source}] {job.company} - {job.title}")

        return job, created

    async def _generate_embedding(self, job: JobPosting) -> None:
        """임베딩 생성 및 저장."""
        embedding_service = self._get_embedding_service()
        if embedding_service is None:
            return

        try:
            text = embedding_service.create_job_text(job)
            job.embedding = await embedding_service.embed_text(text)
            await job.asave(update_fields=["embedding"])
            logger.debug(f"Generated embedding for job: {job.id}")
        except Exception as error:
            logger.warning(f"Failed to generate embedding for job {job.id}: {error}")

    async def save_batch(
        self,
        job_inputs: list[CrawlerJobPosting],
    ) -> SaveResult:
        """
        배치로 채용공고 저장.

        Returns:
            SaveResult 객체
        """
        created_count = 0
        updated_count = 0

        for job_input in job_inputs:
            _, created = await self.save_job(job_input)
            if created:
                created_count += 1
            else:
                updated_count += 1

        logger.info(
            f"Batch save completed: {created_count} {SaveResultKey.CREATED}, {updated_count} {SaveResultKey.UPDATED}"
        )
        return SaveResult(created=created_count, updated=updated_count)
