"""크롤러 예외 클래스."""


class CrawlerError(Exception):
    """크롤러 기본 예외."""
    pass


class CrawlerBlockedError(CrawlerError):
    """크롤러 차단 감지 예외."""

    def __init__(self, site: str, reason: str = "Unknown"):
        self.site = site
        self.reason = reason
        super().__init__(f"{site} blocked: {reason}")


class CrawlerTimeoutError(CrawlerError):
    """크롤러 타임아웃 예외."""

    def __init__(self, site: str, url: str):
        self.site = site
        self.url = url
        super().__init__(f"{site} timeout: {url}")


class CrawlerParseError(CrawlerError):
    """크롤러 파싱 예외."""

    def __init__(self, site: str, message: str):
        self.site = site
        super().__init__(f"{site} parse error: {message}")
