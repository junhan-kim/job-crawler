"""크롤러 싱글톤 인스턴스."""

import asyncio

from aiolimiter import AsyncLimiter
from playwright._impl._errors import TimeoutError as PlaywrightTimeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .constants import (
    CRAWLER_CONCURRENCY_LIMIT,
    RATE_LIMIT_PERIOD_SECONDS,
    REQUESTS_PER_MINUTE,
    RETRY_MAX_ATTEMPTS,
    RETRY_WAIT_MAX_SECONDS,
    RETRY_WAIT_MIN_SECONDS,
    RETRY_WAIT_MULTIPLIER,
)

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
