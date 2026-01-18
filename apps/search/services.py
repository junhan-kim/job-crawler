import logging
from typing import Any

from .models import SearchHistory

logger = logging.getLogger(__name__)


class SearchHistoryService:
    """검색 히스토리 서비스."""

    async def save(
        self,
        query: str,
        result_count: int,
        search_time_ms: int,
        parsed_conditions: dict[str, Any] | None = None,
    ) -> SearchHistory:
        """검색 히스토리 저장."""
        history = await SearchHistory.objects.acreate(
            query=query,
            result_count=result_count,
            search_time_ms=search_time_ms,
            parsed_conditions=parsed_conditions or {},
        )
        logger.debug(f"Saved search history: {query} ({result_count} results)")
        return history

    async def get_recent(self, limit: int = 20) -> list[SearchHistory]:
        """최근 검색 히스토리 조회."""
        return [h async for h in SearchHistory.objects.all()[:limit]]
