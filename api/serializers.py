from django.conf import settings
from rest_framework import serializers

from .exceptions import QueryRequiredError, QueryTooLongError


class RequestField:
    QUERY = "query"


class ResponseField:
    QUERY = "query"
    PARSED = "parsed"
    RESPONSE = "response"


class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField()

    def validate_query(self, value):
        value = value.strip()
        if not value:
            raise QueryRequiredError()
        if len(value) > settings.SEARCH_QUERY_MAX_LENGTH:
            raise QueryTooLongError()
        return value


class ParsedQuerySerializer(serializers.Serializer):
    role = serializers.CharField(allow_null=True)
    experience = serializers.IntegerField(allow_null=True)
    skills = serializers.ListField(child=serializers.CharField())
    location = serializers.CharField(allow_null=True)


class SearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    parsed = ParsedQuerySerializer()
    response = serializers.CharField()
