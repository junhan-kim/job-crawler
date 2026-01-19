"""크롤러 상수 정의."""

from django.conf import settings

REQUESTS_PER_MINUTE = 20
RATE_LIMIT_PERIOD_SECONDS = 60

RETRY_MAX_ATTEMPTS = 3
RETRY_WAIT_MULTIPLIER = 1
RETRY_WAIT_MIN_SECONDS = 2
RETRY_WAIT_MAX_SECONDS = 10

DEFAULT_MIN_DELAY = 2.0
DEFAULT_MAX_DELAY = 4.0

CRAWLER_CONCURRENCY_LIMIT = 1
CRAWLER_TIMEOUT = settings.CRAWLER_TIMEOUT

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]
