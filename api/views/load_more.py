"""무한 스크롤 추가 로드 API 뷰."""
import asyncio

from adrf.views import APIView
from rest_framework.response import Response

from crawlers import CrawlerService
from crawlers.utils import CRAWLER_TIMEOUT, crawler_semaphore

from ..exceptions import ServerBusyError
from ..serializers import (
    LoadMoreRequestSerializer,
    LoadMoreResponseSerializer,
    RequestField,
)


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
