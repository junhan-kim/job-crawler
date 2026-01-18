from adrf.views import APIView
from rest_framework.response import Response

from agent import run_agent
from agent.models import AgentResponse, HistoryListResponse
from apps.search.services import SearchHistoryService
from core.performance import PerformanceTracker
from core.redis_cache import SearchResultCache

from .exceptions import LLMError
from .serializers import (
    RequestField,
    SearchHistorySerializer,
    SearchRequestSerializer,
    SearchResponseSerializer,
)


class SearchView(APIView):
    """채용 공고 검색 API."""

    async def post(self, request):
        """
        자연어 쿼리로 채용 공고 검색.

        Request:
            query: 검색 쿼리 (예: "백엔드 개발자 3년차")

        Response:
            query: 원본 쿼리
            parsed_conditions: 파싱된 검색 조건
            response: LLM 생성 응답
            results: 채용 공고 목록
            total_count: 검색 결과 수
        """
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data[RequestField.QUERY]
        cache = SearchResultCache()
        tracker = PerformanceTracker("search").start()

        cached_response = await cache.get(query)
        if cached_response:
            cached = AgentResponse(**cached_response)
            tracker.stop()
            cached.search_time_ms = int(tracker.elapsed_ms)
            return Response(cached.model_dump())

        try:
            result = await run_agent(query)
        except Exception as error:
            raise LLMError(detail=str(error)) from error

        tracker.stop()
        result.search_time_ms = int(tracker.elapsed_ms)

        history_service = SearchHistoryService()
        await history_service.save(
            query=query,
            result_count=result.total_count,
            search_time_ms=result.search_time_ms,
            parsed_conditions=result.parsed_conditions.model_dump() if result.parsed_conditions else None,
        )

        response_serializer = SearchResponseSerializer(result.model_dump())
        response_data = response_serializer.data

        await cache.set(query, response_data)

        return Response(response_data)


class SearchHistoryView(APIView):
    """검색 히스토리 API."""

    async def get(self, request):
        """
        최근 검색 히스토리 조회.

        Response:
            histories: 검색 히스토리 목록
        """
        history_service = SearchHistoryService()
        histories = await history_service.get_recent()
        serializer = SearchHistorySerializer(histories, many=True)
        response = HistoryListResponse(histories=serializer.data)
        return Response(response.model_dump())
