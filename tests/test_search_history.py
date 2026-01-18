"""검색 히스토리 테스트."""

import uuid

import pytest


class TestSearchHistoryService:
    """SearchHistoryService 테스트."""

    @pytest.mark.django_db
    async def test_save_history(self):
        """히스토리 저장 테스트."""
        from apps.search.services import SearchHistoryService

        service = SearchHistoryService()

        history = await service.save(
            query="Python 백엔드",
            result_count=10,
            search_time_ms=500,
            parsed_conditions={"skill": "Python", "role": "백엔드"},
        )

        assert history.id is not None
        assert history.query == "Python 백엔드"
        assert history.result_count == 10
        assert history.search_time_ms == 500
        assert history.parsed_conditions["skill"] == "Python"

    @pytest.mark.django_db
    async def test_get_recent(self):
        """최근 히스토리 조회 테스트."""
        from apps.search.services import SearchHistoryService

        service = SearchHistoryService()
        unique_id = uuid.uuid4().hex[:8]

        for i in range(5):
            await service.save(
                query=f"test-{unique_id}-{i}",
                result_count=i,
                search_time_ms=100,
            )

        histories = await service.get_recent(limit=5)

        assert len(histories) >= 5
        assert histories[0].query.startswith(f"test-{unique_id}")


class TestSearchHistoryModel:
    """SearchHistory 모델 테스트."""

    @pytest.mark.django_db
    async def test_str_representation(self):
        """문자열 표현 테스트."""
        from apps.search.models import SearchHistory

        history = await SearchHistory.objects.acreate(
            query="테스트 쿼리",
            result_count=5,
            search_time_ms=200,
        )

        assert str(history) == "테스트 쿼리 (5건)"

    @pytest.mark.django_db
    async def test_ordering(self):
        """정렬 순서 테스트 (최신순)."""
        from apps.search.models import SearchHistory

        unique_id = uuid.uuid4().hex[:8]

        await SearchHistory.objects.acreate(
            query=f"first-{unique_id}",
            result_count=1,
        )
        await SearchHistory.objects.acreate(
            query=f"second-{unique_id}",
            result_count=2,
        )

        histories = []
        async for h in SearchHistory.objects.filter(query__contains=unique_id):
            histories.append(h)

        assert histories[0].query == f"second-{unique_id}"
