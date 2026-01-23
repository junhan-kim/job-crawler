"""검색 API Serializer."""
from rest_framework import serializers

from .common import JobPostingSerializer, validate_query_field


class ParsedConditionsSerializer(serializers.Serializer):
    """파싱된 검색 조건."""

    role = serializers.CharField(allow_null=True)
    experience = serializers.IntegerField(allow_null=True)
    skills = serializers.ListField(child=serializers.CharField(), default=list)
    location = serializers.CharField(allow_null=True)


class SearchFiltersSerializer(serializers.Serializer):
    """검색 필터."""

    experience = serializers.IntegerField(allow_null=True)
    location = serializers.CharField(allow_null=True)


class SearchPlanSerializer(serializers.Serializer):
    """검색 계획."""

    keywords = serializers.ListField(child=serializers.CharField(), default=list)
    search_keyword = serializers.CharField()
    filters = SearchFiltersSerializer()


class SearchRequestSerializer(serializers.Serializer):
    """검색 요청."""

    query = serializers.CharField()
    page = serializers.IntegerField(min_value=1, default=1)
    parsed_conditions = ParsedConditionsSerializer(required=False, allow_null=True)
    search_plan = SearchPlanSerializer(required=False, allow_null=True)

    def validate_query(self, value):
        return validate_query_field(value)

    def validate(self, data):
        """page > 1일 때 parsed_conditions와 search_plan 필수 검증."""
        page = data.get("page", 1)
        if page > 1:
            if not data.get("parsed_conditions"):
                raise serializers.ValidationError(
                    {"parsed_conditions": "Required for page > 1"}
                )
            if not data.get("search_plan"):
                raise serializers.ValidationError(
                    {"search_plan": "Required for page > 1"}
                )
        return data


class SearchResponseSerializer(serializers.Serializer):
    """검색 응답."""

    query = serializers.CharField()
    page = serializers.IntegerField()
    parsed_conditions = ParsedConditionsSerializer(allow_null=True)
    search_plan = SearchPlanSerializer(allow_null=True)
    response = serializers.CharField()
    results = JobPostingSerializer(many=True)
    total_count = serializers.IntegerField()
    has_more = serializers.BooleanField()
    search_time_ms = serializers.IntegerField()
