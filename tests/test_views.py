"""API 테스트."""

from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.test import AsyncClient

from agent.models import AgentResponse, ParsedQuery


@pytest.mark.django_db
class TestSearchAPI:
    """검색 API 테스트."""

    async def test_search_empty_query(self):
        """빈 쿼리 에러."""
        client = AsyncClient()
        response = await client.post(
            "/api/search/",
            data={"query": ""},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    async def test_search_missing_query(self):
        """쿼리 없음 에러."""
        client = AsyncClient()
        response = await client.post(
            "/api/search/",
            data={},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    @patch("api.views.run_agent")
    async def test_search_success(self, mock_run_agent):
        """검색 성공."""
        mock_run_agent.return_value = AgentResponse(
            query="백엔드 개발자",
            parsed_conditions=ParsedQuery(role="백엔드", experience=None, skills=[], location=None),
            response="검색 완료",
            results=[],
            total_count=0,
            search_time_ms=100,
        )

        client = AsyncClient()
        response = await client.post(
            "/api/search/",
            data={"query": "백엔드 개발자"},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["query"] == "백엔드 개발자"
        assert "search_time_ms" in data
        assert data["search_time_ms"] >= 0
