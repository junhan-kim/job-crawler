from django.conf import settings
from rest_framework import serializers

from .exceptions import QueryRequiredError, QueryTooLongError


class RequestField:
    QUERY = "query"


class ResponseField:
    QUERY = "query"
    PARSED_CONDITIONS = "parsed_conditions"
    RESPONSE = "response"
    RESULTS = "results"
    TOTAL_COUNT = "total_count"
    SEARCH_TIME_MS = "search_time_ms"


class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField()

    def validate_query(self, value):
        value = value.strip()
        if not value:
            raise QueryRequiredError()
        if len(value) > settings.SEARCH_QUERY_MAX_LENGTH:
            raise QueryTooLongError()
        return value


class ParsedConditionsSerializer(serializers.Serializer):
    """파싱된 검색 조건."""

    role = serializers.CharField(allow_null=True)
    experience = serializers.IntegerField(allow_null=True)
    skills = serializers.ListField(child=serializers.CharField(), default=list)
    location = serializers.CharField(allow_null=True)


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


class SearchResponseSerializer(serializers.Serializer):
    """검색 응답."""

    query = serializers.CharField()
    parsed_conditions = ParsedConditionsSerializer(allow_null=True)
    response = serializers.CharField()
    results = JobPostingSerializer(many=True)
    total_count = serializers.IntegerField()
    search_time_ms = serializers.IntegerField()
