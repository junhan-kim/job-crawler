import asyncio

from adrf.views import APIView
from rest_framework.response import Response

from agent import run_agent
from agent.models import AgentResponse, HistoryListResponse
from apps.search.services import SearchHistoryService
from core.performance import PerformanceTracker
from core.redis_cache import SearchResultCache
from crawlers import CrawlerService
from crawlers.utils import CRAWLER_TIMEOUT, crawler_semaphore

from .exceptions import LLMError, ServerBusyError
from .serializers import (
    LoadMoreRequestSerializer,
    LoadMoreResponseSerializer,
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


class LoadMoreView(APIView):
    """무한 스크롤 추가 로드 API."""

    MIN_RESULTS_FOR_MORE = 1

    async def post(self, request):
        """
        추가 페이지 크롤링.

        Request:
            keyword: 검색 키워드
            page: 페이지 번호 (2부터 시작)

        Response:
            results: 채용 공고 목록
            total_count: 이번 요청의 결과 수
            page: 현재 페이지
            has_more: 다음 페이지 존재 여부
        """
        serializer = LoadMoreRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        keyword = serializer.validated_data[RequestField.KEYWORD]
        page = serializer.validated_data[RequestField.PAGE]

        try:
            async with asyncio.timeout(CRAWLER_TIMEOUT):
                async with crawler_semaphore:
                    crawler_service = CrawlerService()
                    job_postings = await crawler_service.crawl_page(keyword, page)
        except TimeoutError as error:
            raise ServerBusyError() from error

        results = [job.model_dump() for job in job_postings]
        has_more = len(results) >= self.MIN_RESULTS_FOR_MORE

        response_data = {
            "results": results,
            "total_count": len(results),
            "page": page,
            "has_more": has_more,
        }
        response_serializer = LoadMoreResponseSerializer(response_data)
        return Response(response_serializer.data)
