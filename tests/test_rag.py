"""RAG 도구 테스트."""

import uuid

import pytest


class TestSearchJobsFromDB:
    """DB 기반 검색 테스트."""

    @pytest.mark.django_db
    async def test_search_by_keyword(self):
        """키워드 기반 검색 테스트."""
        from agent.tools.rag import search_jobs_from_db
        from apps.jobs.models import JobPosting

        test_id = uuid.uuid4().hex[:8]
        await JobPosting.objects.acreate(
            source="saramin",
            source_id=f"test-{test_id}-1",
            url=f"https://example.com/{test_id}/1",
            title="Python 백엔드 개발자",
            company="테스트 회사",
            location="서울",
            skills=["Python", "Django"],
        )
        await JobPosting.objects.acreate(
            source="saramin",
            source_id=f"test-{test_id}-2",
            url=f"https://example.com/{test_id}/2",
            title="Java 백엔드 개발자",
            company="다른 회사",
            location="판교",
            skills=["Java", "Spring"],
        )

        results = await search_jobs_from_db("Python")
        assert len(results) >= 1
        assert any("Python" in r.title for r in results)

    @pytest.mark.django_db
    async def test_search_with_location_filter(self):
        """위치 필터 테스트."""
        from agent.tools.rag import search_jobs_from_db
        from apps.jobs.models import JobPosting

        test_id = uuid.uuid4().hex[:8]
        await JobPosting.objects.acreate(
            source="saramin",
            source_id=f"loc-{test_id}-1",
            url=f"https://example.com/loc/{test_id}/1",
            title="프론트엔드 개발자",
            company="서울 회사",
            location="서울 강남구",
            skills=["React"],
        )
        await JobPosting.objects.acreate(
            source="saramin",
            source_id=f"loc-{test_id}-2",
            url=f"https://example.com/loc/{test_id}/2",
            title="프론트엔드 개발자",
            company="부산 회사",
            location="부산 해운대구",
            skills=["React"],
        )

        results = await search_jobs_from_db("프론트엔드", location="서울")
        assert all("서울" in r.location for r in results)

    @pytest.mark.django_db
    async def test_search_empty_result(self):
        """결과 없는 경우 테스트."""
        from agent.tools.rag import search_jobs_from_db

        results = await search_jobs_from_db("존재하지않는키워드12345")
        assert results == []


class TestRAGTool:
    """RAGTool 테스트."""

    @pytest.mark.django_db
    async def test_vector_search_with_filters(self):
        """필터가 적용된 벡터 검색 테스트."""
        from unittest.mock import AsyncMock, patch

        from agent.tools.rag import RAGTool
        from apps.jobs.models import JobPosting

        test_id = uuid.uuid4().hex[:8]
        await JobPosting.objects.acreate(
            source="saramin",
            source_id=f"rag-{test_id}-1",
            url=f"https://example.com/rag/{test_id}/1",
            title="Python 개발자",
            company="서울 회사",
            location="서울",
            skills=["Python"],
            embedding=[0.1] * 1024,
        )

        mock_embedding = [0.1] * 1024
        with patch("llama_index.core.Settings") as mock_settings:
            mock_settings.embed_model.aget_text_embedding = AsyncMock(
                return_value=mock_embedding
            )
            rag = RAGTool()
            results = await rag.search("Python", top_k=10, filters={"location": "서울"})

        assert all("서울" in r.location for r in results)
