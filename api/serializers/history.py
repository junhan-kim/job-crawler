"""검색 히스토리 API Serializer."""
from rest_framework import serializers


class SearchHistorySerializer(serializers.Serializer):
    """검색 히스토리."""

    id = serializers.IntegerField()
    query = serializers.CharField()
    result_count = serializers.IntegerField()
    search_time_ms = serializers.IntegerField()
    created_at = serializers.DateTimeField()
