from adrf.views import APIView
from rest_framework.response import Response

from agent import run_agent
from .serializers import SearchRequestSerializer, SearchResponseSerializer, RequestField
from .exceptions import LLMError


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

        try:
            result = await run_agent(query)
        except Exception as e:
            raise LLMError(detail=str(e))

        response_serializer = SearchResponseSerializer(result)
        return Response(response_serializer.data)
