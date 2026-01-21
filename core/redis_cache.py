"""Redis 기반 캐싱."""

import hashlib
import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

CACHE_TTL = 3600


class SearchResultCache:
    """검색 결과 캐싱 서비스."""

    def __init__(self, redis_url: str | None = None, ttl: int = CACHE_TTL):
        self.redis_url = redis_url or settings.REDIS_URL
        self.ttl = ttl
        self._client = None

    async def _get_client(self):
        """Redis 클라이언트 반환 (lazy init)."""
        if self._client is None:
            import redis.asyncio as redis

            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def _make_key(self, query: str, filters: dict[str, Any] | None = None) -> str:
        """쿼리 + 필터를 해시하여 캐시 키 생성."""
        data = {
            "query": query.lower().strip(),
            "filters": filters or {},
        }
        hash_value = hashlib.md5(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        return f"search:{hash_value}"

    async def get(
        self, query: str, filters: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """캐시된 검색 응답 조회."""
        try:
            client = await self._get_client()
            key = self._make_key(query, filters)
            data = await client.get(key)

            if data:
                logger.debug(f"Cache hit for query: {query}")
                return json.loads(data)

            logger.debug(f"Cache miss for query: {query}")
            return None

        except Exception as e:
            logger.warning(f"Redis get error: {e}")
            return None

    async def set(
        self,
        query: str,
        response: dict[str, Any],
        filters: dict[str, Any] | None = None,
    ) -> bool:
        """검색 응답 캐싱."""
        try:
            client = await self._get_client()
            key = self._make_key(query, filters)
            await client.set(key, json.dumps(response), ex=self.ttl)
            logger.debug(f"Cached response for query: {query}")
            return True

        except Exception as e:
            logger.warning(f"Redis set error: {e}")
            return False

    async def delete(
        self, query: str, filters: dict[str, Any] | None = None
    ) -> bool:
        """캐시 삭제."""
        try:
            client = await self._get_client()
            key = self._make_key(query, filters)
            await client.delete(key)
            return True

        except Exception as e:
            logger.warning(f"Redis delete error: {e}")
            return False

    async def clear_all(self) -> int:
        """모든 검색 캐시 삭제."""
        try:
            client = await self._get_client()
            keys = []
            async for key in client.scan_iter("search:*"):
                keys.append(key)

            if keys:
                await client.delete(*keys)

            logger.info(f"Cleared {len(keys)} cached searches")
            return len(keys)

        except Exception as e:
            logger.warning(f"Redis clear error: {e}")
            return 0

    async def close(self):
        """Redis 연결 종료."""
        if self._client:
            await self._client.close()
            self._client = None


def init_llm_cache() -> None:
    """LangChain LLM 캐시 초기화 (Redis 기반)."""
    try:
        import redis
        from langchain_community.cache import RedisCache
        from langchain_core.globals import set_llm_cache

        redis_client = redis.from_url(settings.REDIS_URL)
        set_llm_cache(RedisCache(redis_=redis_client, ttl=settings.LLM_CACHE_TTL_SECONDS))
        logger.info("LLM cache initialized with Redis")

    except ImportError as error:
        logger.warning(f"LangChain cache not available: {error}")
    except Exception as error:
        logger.error(f"LLM cache initialization failed: {error}")
