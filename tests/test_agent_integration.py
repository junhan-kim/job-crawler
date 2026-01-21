"""E2E 테스트 - 검색 전체 플로우."""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from django.test import AsyncClient

from agent.models import AgentResponse, ParsedQuery
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


@pytest.fixture
def mock_agent_response(mock_job_postings):
    """테스트용 AgentResponse."""
    return AgentResponse(
        query="서울 백엔드 개발자 3년차",
        parsed_conditions=ParsedQuery(
            role="백엔드 개발자",
            experience=3,
            skills=["Python"],
            location="서울",
        ),
        response="검색 완료",
        results=[
            {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "url": job.url,
                "source": job.source.value,
                "experience": job.experience,
                "skills": job.skills,
                "deadline": job.deadline,
            }
            for job in mock_job_postings
        ],
        total_count=len(mock_job_postings),
        search_time_ms=0,
    )


@pytest.fixture
def mock_cache():
    """Redis 캐시 모킹."""
    with patch("api.views.search.SearchResultCache") as mock_class:
        mock_instance = AsyncMock()
        mock_instance.get.return_value = None
        mock_instance.set.return_value = True
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.mark.django_db
class TestSearchE2E:
    """검색 E2E 테스트."""

    @patch("api.views.search.run_agent")
    async def test_full_search_flow(self, mock_run_agent, mock_cache, mock_agent_response):
        """검색 전체 플로우 테스트."""
        mock_run_agent.return_value = mock_agent_response

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

    @patch("api.views.search.run_agent")
    async def test_search_no_results(self, mock_run_agent, mock_cache):
        """검색 결과 없음 테스트."""
        mock_run_agent.return_value = AgentResponse(
            query="희귀한 직종",
            parsed_conditions=ParsedQuery(
                role="희귀직종",
                experience=None,
                skills=[],
                location=None,
            ),
            response="검색 결과가 없습니다.",
            results=[],
            total_count=0,
            search_time_ms=0,
        )

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

    @patch("api.views.search.run_agent")
    async def test_search_various_keywords(self, mock_run_agent, mock_cache, mock_agent_response):
        """다양한 검색어 테스트."""
        test_queries = [
            "프론트엔드 개발자",
            "데이터 엔지니어 신입",
            "판교 백엔드",
            "Python Django 개발",
        ]

        mock_run_agent.return_value = mock_agent_response

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
