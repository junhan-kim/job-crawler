"""검색 히스토리 API 뷰."""
from adrf.views import APIView
from rest_framework.response import Response

from agent.models import HistoryListResponse
from apps.search.services import SearchHistoryService

from ..serializers import SearchHistorySerializer


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
