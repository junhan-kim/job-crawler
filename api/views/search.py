"""검색 API 뷰."""
from adrf.views import APIView
from rest_framework.response import Response

from agent import run_agent
from agent.models import AgentResponse
from apps.search.services import SearchHistoryService
from core.performance import PerformanceTracker
from core.redis_cache import SearchResultCache

from ..exceptions import LLMError
from ..serializers import (
    RequestField,
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
            page: 페이지 번호 (기본값 1, load more 시 2 이상)
            parsed_conditions: 이전 파싱 결과 (page > 1일 때 필수)
            search_plan: 이전 검색 계획 (page > 1일 때 필수)

        Response:
            query: 원본 쿼리
            page: 현재 페이지
            parsed_conditions: 파싱된 검색 조건
            search_plan: 검색 계획
            response: LLM 생성 응답
            results: 채용 공고 목록
            total_count: 검색 결과 수
            has_more: 다음 페이지 존재 여부
        """
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data[RequestField.QUERY]
        page = serializer.validated_data.get("page", 1)
        parsed_conditions = serializer.validated_data.get("parsed_conditions")
        search_plan = serializer.validated_data.get("search_plan")

        cache = SearchResultCache()
        tracker = PerformanceTracker("search").start()

        if page == 1:
            cached_response = await cache.get(query)
            if cached_response:
                cached = AgentResponse(**cached_response)
                tracker.stop()
                cached.search_time_ms = int(tracker.elapsed_ms)
                return Response(cached.model_dump())

        try:
            result = await run_agent(
                query=query,
                page=page,
                parsed_conditions=parsed_conditions,
                search_plan=search_plan,
            )
        except Exception as error:
            raise LLMError(detail=str(error)) from error

        tracker.stop()
        result.search_time_ms = int(tracker.elapsed_ms)

        if page == 1:
            history_service = SearchHistoryService()
            await history_service.save(
                query=query,
                result_count=result.total_count,
                search_time_ms=result.search_time_ms,
                parsed_conditions=result.parsed_conditions.model_dump() if result.parsed_conditions else None,
            )

        response_serializer = SearchResponseSerializer(result.model_dump())
        response_data = response_serializer.data

        if page == 1:
            await cache.set(query, response_data)

        return Response(response_data)
