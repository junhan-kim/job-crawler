"""크롤러 유틸리티 - 재시도, Rate Limiting, User-Agent 관리."""

import asyncio
import random

from aiolimiter import AsyncLimiter
from playwright._impl._errors import TimeoutError as PlaywrightTimeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

REQUESTS_PER_MINUTE = 20
RATE_LIMIT_PERIOD_SECONDS = 60

RETRY_MAX_ATTEMPTS = 3
RETRY_WAIT_MULTIPLIER = 1
RETRY_WAIT_MIN_SECONDS = 2
RETRY_WAIT_MAX_SECONDS = 10

DEFAULT_MIN_DELAY = 2.0
DEFAULT_MAX_DELAY = 4.0

CRAWLER_CONCURRENCY_LIMIT = 1
CRAWLER_WAIT_TIMEOUT_SECONDS = 30

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

rate_limiter = AsyncLimiter(REQUESTS_PER_MINUTE, RATE_LIMIT_PERIOD_SECONDS)

crawler_semaphore = asyncio.Semaphore(CRAWLER_CONCURRENCY_LIMIT)

retry_on_timeout = retry(
    stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
    wait=wait_exponential(
        multiplier=RETRY_WAIT_MULTIPLIER,
        min=RETRY_WAIT_MIN_SECONDS,
        max=RETRY_WAIT_MAX_SECONDS,
    ),
    retry=retry_if_exception_type((PlaywrightTimeout, ConnectionError, TimeoutError)),
    reraise=True,
)


def get_random_user_agent() -> str:
    """랜덤 User-Agent 반환."""
    return random.choice(USER_AGENTS)


def get_random_delay(
    min_delay: float = DEFAULT_MIN_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
) -> float:
    """랜덤 딜레이 값 반환."""
    return random.uniform(min_delay, max_delay)
