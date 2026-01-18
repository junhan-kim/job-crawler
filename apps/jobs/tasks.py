"""Celery 크롤링 태스크."""

import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.jobs.services import JobService
from apps.search.models import SearchHistory
from crawlers import JobKoreaCrawler, SaraminCrawler

from .constants import POPULAR_KEYWORDS, RECENT_SEARCH_HOURS, RECENT_SEARCH_LIMIT

logger = logging.getLogger(__name__)


@shared_task
def crawl_popular_keywords():
    """인기 키워드 크롤링 태스크."""
    logger.info("Starting popular keywords crawl")

    for keyword in POPULAR_KEYWORDS:
        crawl_and_save.delay(keyword)

    logger.info(f"Queued {len(POPULAR_KEYWORDS)} crawl tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def crawl_and_save(self, keyword: str, max_pages: int | None = None):
    """
    단일 키워드 크롤링 후 DB 저장.

    Celery task는 동기이므로 async 코드를 래핑.
    """
    try:
        async_to_sync(_crawl_and_save_async)(keyword, max_pages)
        logger.info(f"Completed crawl for: {keyword}")
    except Exception as error:
        logger.error(f"Crawl failed for {keyword}: {error}")
        raise self.retry(exc=error)


async def _crawl_and_save_async(keyword: str, max_pages: int | None):
    """실제 비동기 크롤링 로직."""
    job_service = JobService()
    pages = max_pages if max_pages is not None else settings.BATCH_CRAWL_MAX_PAGES

    crawlers = [SaraminCrawler(), JobKoreaCrawler()]

    for crawler in crawlers:
        try:
            results = await crawler.search(keyword, max_pages=pages)
            for job in results:
                await job_service.save_job(job)
            logger.info(f"{crawler.__class__.__name__}: {len(results)} jobs for '{keyword}'")
        except Exception as error:
            logger.error(f"{crawler.__class__.__name__} crawl failed for {keyword}: {error}")


@shared_task
def crawl_recent_search_keywords():
    """
    최근 검색 키워드 기반 크롤링.

    SearchHistory에서 최근 검색어를 추출하여 크롤링.
    """
    async_to_sync(_crawl_recent_keywords_async)()


async def _crawl_recent_keywords_async():
    """최근 검색어 크롤링."""
    since = timezone.now() - timedelta(hours=RECENT_SEARCH_HOURS)
    keywords = set()

    async for history in SearchHistory.objects.filter(
        created_at__gte=since
    ).values_list("query", flat=True)[:RECENT_SEARCH_LIMIT]:
        keywords.add(history)

    logger.info(f"Found {len(keywords)} recent search keywords")

    for keyword in keywords:
        if keyword not in POPULAR_KEYWORDS:  # 인기 키워드와 중복 방지
            crawl_and_save.delay(keyword)
