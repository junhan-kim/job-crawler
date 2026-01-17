from adrf.views import APIView
from rest_framework.response import Response

from agent import run_agent
from .serializers import SearchRequestSerializer, SearchResponseSerializer, RequestField
from .exceptions import LLMError


class SearchView(APIView):
    async def post(self, request):
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data[RequestField.QUERY]

        try:
            result = await run_agent(query)
        except Exception as e:
            raise LLMError(detail=str(e))

        response_serializer = SearchResponseSerializer(result)
        return Response(response_serializer.data)
