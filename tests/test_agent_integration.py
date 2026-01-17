"""E2E 테스트 - 검색 전체 플로우."""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from django.test import AsyncClient

from crawlers.models import JobPosting, JobSource


@pytest.fixture
def mock_job_postings():
    """테스트용 채용공고 목록."""
    return [
        JobPosting(
            title="백엔드 개발자",
            company="테스트회사",
            location="서울",
            url="https://example.com/job/1",
            source=JobSource.SARAMIN,
            experience="3년",
            skills=["Python", "Django"],
            deadline="~12/31",
        ),
        JobPosting(
            title="서버 개발자",
            company="좋은회사",
            location="경기",
            url="https://example.com/job/2",
            source=JobSource.SARAMIN,
            experience="5년",
            skills=["Java", "Spring"],
            deadline="~01/15",
        ),
    ]


@pytest.mark.django_db
class TestSearchE2E:
    """검색 E2E 테스트."""

    @patch("agent.nodes.execute.SaraminCrawler")
    @patch("agent.nodes.parse.OllamaProvider")
    async def test_full_search_flow(self, mock_ollama_class, mock_crawler_class, mock_job_postings):
        """검색 전체 플로우 테스트."""
        mock_ollama = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = '{"role": "백엔드 개발자", "experience": 3, "skills": ["Python"], "location": "서울"}'
        mock_ollama.chat.return_value = mock_response
        mock_ollama_class.return_value = mock_ollama

        mock_crawler = AsyncMock()
        mock_crawler.search.return_value = mock_job_postings
        mock_crawler_class.return_value = mock_crawler

        client = AsyncClient()
        response = await client.post(
            "/api/search/",
            data={"query": "서울 백엔드 개발자 3년차"},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()

        assert data["query"] == "서울 백엔드 개발자 3년차"
        assert data["parsed_conditions"] is not None
        assert "results" in data
        assert "total_count" in data
        assert "search_time_ms" in data
        assert data["search_time_ms"] >= 0

    @patch("agent.nodes.execute.SaraminCrawler")
    @patch("agent.nodes.parse.OllamaProvider")
    async def test_search_no_results(self, mock_ollama_class, mock_crawler_class):
        """검색 결과 없음 테스트."""
        mock_ollama = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = '{"role": "희귀직종", "experience": null, "skills": [], "location": null}'
        mock_ollama.chat.return_value = mock_response
        mock_ollama_class.return_value = mock_ollama

        mock_crawler = AsyncMock()
        mock_crawler.search.return_value = []
        mock_crawler_class.return_value = mock_crawler

        client = AsyncClient()
        response = await client.post(
            "/api/search/",
            data={"query": "희귀한 직종"},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["total_count"] == 0
        assert data["results"] == []

    async def test_search_empty_query(self):
        """빈 쿼리 에러 테스트."""
        client = AsyncClient()
        response = await client.post(
            "/api/search/",
            data={"query": ""},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    async def test_search_missing_query(self):
        """쿼리 없음 에러 테스트."""
        client = AsyncClient()
        response = await client.post(
            "/api/search/",
            data={},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    @patch("agent.nodes.execute.SaraminCrawler")
    @patch("agent.nodes.parse.OllamaProvider")
    async def test_search_various_keywords(self, mock_ollama_class, mock_crawler_class, mock_job_postings):
        """다양한 검색어 테스트."""
        test_queries = [
            "프론트엔드 개발자",
            "데이터 엔지니어 신입",
            "판교 백엔드",
            "Python Django 개발",
        ]

        mock_ollama = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = '{"role": "개발자", "experience": null, "skills": [], "location": null}'
        mock_ollama.chat.return_value = mock_response
        mock_ollama_class.return_value = mock_ollama

        mock_crawler = AsyncMock()
        mock_crawler.search.return_value = mock_job_postings
        mock_crawler_class.return_value = mock_crawler

        client = AsyncClient()

        for query in test_queries:
            response = await client.post(
                "/api/search/",
                data={"query": query},
                content_type="application/json",
            )

            assert response.status_code == HTTPStatus.OK, f"Failed for query: {query}"
            data = response.json()
            assert "results" in data
