"""크롤러 유틸리티 함수."""

import random

from .constants import (
    CRAWLER_TIMEOUT,
    DEFAULT_MAX_DELAY,
    DEFAULT_MIN_DELAY,
    USER_AGENTS,
)
from .singletons import crawler_semaphore, rate_limiter, retry_on_timeout

__all__ = [
    "CRAWLER_TIMEOUT",
    "crawler_semaphore",
    "get_random_delay",
    "get_random_user_agent",
    "rate_limiter",
    "retry_on_timeout",
]


def get_random_user_agent() -> str:
    """랜덤 User-Agent 반환."""
    return random.choice(USER_AGENTS)


def get_random_delay(
    min_delay: float = DEFAULT_MIN_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
) -> float:
    """랜덤 딜레이 값 반환."""
    return random.uniform(min_delay, max_delay)
