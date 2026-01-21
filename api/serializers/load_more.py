"""무한 스크롤 추가 로드 API Serializer."""
from rest_framework import serializers

from .common import JobPostingSerializer, validate_query_field


class LoadMoreRequestSerializer(serializers.Serializer):
    """무한 스크롤 추가 로드 요청."""

    keyword = serializers.CharField()
    page = serializers.IntegerField(min_value=1)

    def validate_keyword(self, value):
        return validate_query_field(value)


class LoadMoreResponseSerializer(serializers.Serializer):
    """무한 스크롤 추가 로드 응답."""

    results = JobPostingSerializer(many=True)
    total_count = serializers.IntegerField()
    page = serializers.IntegerField()
    has_more = serializers.BooleanField()
