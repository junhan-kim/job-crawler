"""pgvector 기반 시맨틱 검색 도구."""

import logging
from typing import Any

from django.conf import settings
from django.db.models import Q
from llama_index.core import Settings
from pgvector.django import CosineDistance

from agent.models import JobSearchResult
from apps.jobs.models import JobPosting

logger = logging.getLogger(__name__)


class RAGTool:
    """pgvector 기반 벡터 검색 도구."""

    async def search(
        self,
        query: str,
        top_k: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> list[JobSearchResult]:
        """
        벡터 유사도 기반 검색.

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            filters: 필터 (location, source, company)

        Returns:
            검색 결과 리스트
        """
        try:
            query_embedding = await Settings.embed_model.aget_text_embedding(query)
            results = await self._vector_search(query_embedding, top_k, filters)

            logger.info(f"Vector search completed: {len(results)} results for '{query}'")
            return results

        except Exception as error:
            logger.error(f"Vector search error: {error}")
            return []

    async def _vector_search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> list[JobSearchResult]:
        """pgvector ORM으로 벡터 검색 수행."""
        queryset = JobPosting.objects.annotate(
            distance=CosineDistance("embedding", query_embedding)
        ).filter(
            is_active=True,
            embedding__isnull=False,
        )

        if filters:
            if location := filters.get("location"):
                queryset = queryset.filter(location__icontains=location)

            if source := filters.get("source"):
                queryset = queryset.filter(source=source)

            if company := filters.get("company"):
                queryset = queryset.filter(company__icontains=company)

        queryset = queryset.filter(
            distance__lt=settings.VECTOR_SEARCH_DISTANCE_THRESHOLD
        ).order_by("distance")[:top_k]

        results = []
        async for job in queryset:
            results.append(self._to_search_result(job))

        return results

    def _to_search_result(self, job: JobPosting) -> JobSearchResult:
        """JobPosting 모델을 JobSearchResult로 변환."""
        return JobSearchResult(
            title=job.title,
            company=job.company,
            location=job.location or "",
            url=job.url,
            skills=job.skills,
            experience=job.experience,
            salary=job.salary,
            source=job.source,
            score=1 - job.distance if hasattr(job, "distance") else None,
            posted_at=job.posted_at.isoformat() if job.posted_at else None,
        )


async def search_jobs_from_db(
    keyword: str,
    location: str | None = None,
    limit: int = 20,
) -> list[JobSearchResult]:
    """
    DB에서 키워드 기반 채용공고 검색 (벡터 검색 없이).

    임베딩 인덱스가 구축되기 전 또는 fallback용.
    """
    queryset = JobPosting.objects.filter(is_active=True)

    if keyword:
        queryset = queryset.filter(
            Q(title__icontains=keyword)
            | Q(company__icontains=keyword)
            | Q(skills__icontains=keyword)
        )

    if location:
        queryset = queryset.filter(location__icontains=location)

    queryset = queryset.order_by("-crawled_at")[:limit]

    results = []
    async for job in queryset:
        results.append(
            JobSearchResult(
                title=job.title,
                company=job.company,
                location=job.location or "",
                url=job.url,
                skills=job.skills,
                experience=job.experience,
                salary=job.salary,
                source=job.source,
                posted_at=job.posted_at.isoformat() if job.posted_at else None,
            )
        )

    logger.info(f"DB search completed: {len(results)} results for '{keyword}'")
    return results
