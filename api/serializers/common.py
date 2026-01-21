"""공통 Serializer 및 상수."""
from django.conf import settings
from rest_framework import serializers

from ..exceptions import QueryRequiredError, QueryTooLongError


class RequestField:
    """요청 필드명 상수."""

    QUERY = "query"
    KEYWORD = "keyword"
    PAGE = "page"


class JobPostingSerializer(serializers.Serializer):
    """채용 공고."""

    title = serializers.CharField()
    company = serializers.CharField()
    location = serializers.CharField(allow_blank=True)
    url = serializers.URLField()
    source = serializers.CharField()
    experience = serializers.CharField(allow_null=True, allow_blank=True)
    salary = serializers.CharField(allow_null=True, allow_blank=True)
    skills = serializers.ListField(child=serializers.CharField(), default=list)
    deadline = serializers.CharField(allow_null=True, allow_blank=True)
    posted_at = serializers.CharField(allow_null=True, allow_blank=True)


def validate_query_field(value: str) -> str:
    """쿼리/키워드 필드 공통 유효성 검사."""
    value = value.strip()
    if not value:
        raise QueryRequiredError()
    if len(value) > settings.SEARCH_QUERY_MAX_LENGTH:
        raise QueryTooLongError()
    return value
