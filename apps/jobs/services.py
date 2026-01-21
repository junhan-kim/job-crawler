"""채용공고 저장 및 관리 서비스."""

import hashlib
import logging

from django.conf import settings

from crawlers.models import JobPosting as CrawlerJobPosting

from .models import JobPosting
from .types import JobAction, SaveResult, SaveResultKey

logger = logging.getLogger(__name__)


class JobService:
    """채용공고 저장 및 관리 서비스."""

    def __init__(self):
        self._embedding_service = None

    def _get_embedding_service(self):
        """EmbeddingService lazy init."""
        if self._embedding_service is None and settings.DB_SAVE_ENABLED:
            from core.embedding_service import EmbeddingService

            self._embedding_service = EmbeddingService()
        return self._embedding_service

    def _generate_source_id(self, job_input: CrawlerJobPosting) -> str:
        """
        source_id 생성.

        title + company 기반 해시로 고유 ID 생성.
        URL은 검색 파라미터에 따라 달라지므로 사용하지 않음.
        """
        key = f"{job_input.title}|{job_input.company or ''}"
        return hashlib.md5(key.encode()).hexdigest()[:16]

    async def save_job(
        self,
        job_input: CrawlerJobPosting,
        skip_embedding: bool = False,
    ) -> tuple[JobPosting, bool]:
        """
        크롤링 결과를 DB에 저장.

        Args:
            job_input: 크롤링된 채용공고 데이터
            skip_embedding: True면 임베딩 생성 건너뜀 (백그라운드 처리용)

        Returns:
            (JobPosting, created) 튜플
        """
        source_id = self._generate_source_id(job_input)

        job, created = await JobPosting.objects.aupdate_or_create(
            source=job_input.source,
            source_id=source_id,
            defaults=job_input.to_django_defaults(),
        )

        if not skip_embedding and (created or job.embedding is None):
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
        skip_embedding: bool = False,
    ) -> tuple[SaveResult, list[int]]:
        """
        배치로 채용공고 저장.

        Args:
            job_inputs: 크롤링된 채용공고 데이터 리스트
            skip_embedding: True면 임베딩 생성 건너뜀 (백그라운드 처리용)

        Returns:
            (SaveResult, job_ids) 튜플. job_ids는 임베딩 생성 필요한 ID 리스트.
        """
        created_count = 0
        updated_count = 0
        job_ids_for_embedding: list[int] = []

        for job_input in job_inputs:
            job, created = await self.save_job(job_input, skip_embedding=skip_embedding)
            if created:
                created_count += 1
            else:
                updated_count += 1

            if skip_embedding and (created or job.embedding is None):
                job_ids_for_embedding.append(job.id)

        logger.info(
            f"Batch save completed: {created_count} {SaveResultKey.CREATED}, {updated_count} {SaveResultKey.UPDATED}"
        )
        return SaveResult(created=created_count, updated=updated_count), job_ids_for_embedding

    async def generate_embeddings_for_jobs(self, job_ids: list[int]) -> int:
        """
        지정된 job들의 임베딩 생성.

        Args:
            job_ids: 임베딩 생성할 job ID 리스트

        Returns:
            성공적으로 임베딩 생성된 job 수
        """
        embedding_service = self._get_embedding_service()
        if embedding_service is None or not job_ids:
            return 0

        jobs = [job async for job in JobPosting.objects.filter(id__in=job_ids)]
        if not jobs:
            return 0

        texts = [embedding_service.create_job_text(job) for job in jobs]

        try:
            embeddings = await embedding_service.embed_batch(texts)

            for job, embedding in zip(jobs, embeddings, strict=True):
                job.embedding = embedding

            await JobPosting.objects.abulk_update(jobs, ["embedding"])
            logger.info(f"Generated embeddings for {len(jobs)} jobs")
            return len(jobs)
        except Exception as error:
            logger.error(f"Failed to generate batch embeddings: {error}")
            return 0
