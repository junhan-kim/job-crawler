"""검색 API Serializer."""
from rest_framework import serializers

from .common import JobPostingSerializer, validate_query_field


class ParsedConditionsSerializer(serializers.Serializer):
    """파싱된 검색 조건."""

    role = serializers.CharField(allow_null=True)
    experience = serializers.IntegerField(allow_null=True)
    skills = serializers.ListField(child=serializers.CharField(), default=list)
    location = serializers.CharField(allow_null=True)


class SearchRequestSerializer(serializers.Serializer):
    """검색 요청."""

    query = serializers.CharField()

    def validate_query(self, value):
        return validate_query_field(value)


class SearchResponseSerializer(serializers.Serializer):
    """검색 응답."""

    query = serializers.CharField()
    parsed_conditions = ParsedConditionsSerializer(allow_null=True)
    response = serializers.CharField()
    results = JobPostingSerializer(many=True)
    total_count = serializers.IntegerField()
    search_time_ms = serializers.IntegerField()
