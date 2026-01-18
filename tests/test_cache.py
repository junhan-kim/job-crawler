"""캐시 테스트."""

from unittest.mock import AsyncMock


class TestSearchResultCache:
    """SearchResultCache 테스트."""

    def test_make_key_consistent(self):
        """동일 쿼리는 동일 키 생성."""
        from core.redis_cache import SearchResultCache

        cache = SearchResultCache()

        key1 = cache._make_key("Python 백엔드")
        key2 = cache._make_key("Python 백엔드")
        key3 = cache._make_key("python 백엔드")

        assert key1 == key2
        assert key1 == key3

    def test_make_key_with_filters(self):
        """필터 포함 키 생성."""
        from core.redis_cache import SearchResultCache

        cache = SearchResultCache()

        key1 = cache._make_key("Python", {"location": "서울"})
        key2 = cache._make_key("Python", {"location": "부산"})
        key3 = cache._make_key("Python")

        assert key1 != key2
        assert key1 != key3

    def test_make_key_prefix(self):
        """캐시 키 prefix 확인."""
        from core.redis_cache import SearchResultCache

        cache = SearchResultCache()
        key = cache._make_key("test query")

        assert key.startswith("search:")

    async def test_get_set_integration(self):
        """get/set 통합 테스트 (mocked)."""
        from core.redis_cache import SearchResultCache

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)

        cache = SearchResultCache()
        cache._client = mock_redis

        result = await cache.get("test query")
        assert result is None

        test_data = {"query": "test", "results": [{"title": "Python 개발자"}]}
        success = await cache.set("test query", test_data)
        assert success is True

        mock_redis.set.assert_called_once()

    async def test_get_cache_hit(self):
        """캐시 히트 테스트."""
        import json

        from core.redis_cache import SearchResultCache

        test_data = {
            "query": "test",
            "results": [{"title": "Python 개발자"}],
            "total_count": 1,
            "search_time_ms": 100,
        }
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(test_data))

        cache = SearchResultCache()
        cache._client = mock_redis

        result = await cache.get("test query")
        assert result == test_data

    async def test_error_handling(self):
        """에러 처리 테스트."""
        from core.redis_cache import SearchResultCache

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Connection error"))

        cache = SearchResultCache()
        cache._client = mock_redis

        result = await cache.get("test query")
        assert result is None
