"""브라우저 풀 관리 - 싱글톤으로 브라우저 인스턴스 재사용."""

import asyncio
import logging

from django.conf import settings
from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright

from .utils import get_random_user_agent

logger = logging.getLogger(__name__)

VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080


class BrowserPool:
    """브라우저 풀 싱글톤."""

    _instance: "BrowserPool | None" = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self):
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._initialized = False

    @classmethod
    async def get_instance(cls) -> "BrowserPool":
        """싱글톤 인스턴스 반환."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """브라우저 초기화 (최초 1회)."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            logger.info("Initializing browser pool...")
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            self._initialized = True
            logger.info("Browser pool initialized")

    async def get_context(self) -> BrowserContext:
        """새 브라우저 컨텍스트 생성."""
        if not self._initialized:
            await self.initialize()

        return await self._browser.new_context(
            user_agent=get_random_user_agent(),
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
            locale=settings.CRAWLER_LOCALE,
            timezone_id=settings.CRAWLER_TIMEZONE,
        )

    async def close(self) -> None:
        """브라우저 종료."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._initialized = False
        logger.info("Browser pool closed")

    @property
    def is_initialized(self) -> bool:
        return self._initialized


async def get_browser_pool() -> BrowserPool:
    """브라우저 풀 인스턴스 반환."""
    pool = await BrowserPool.get_instance()
    await pool.initialize()
    return pool
