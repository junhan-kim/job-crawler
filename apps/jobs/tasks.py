"""Celery 크롤링 태스크."""

import asyncio
import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.jobs.services import JobService
from apps.search.models import SearchHistory
from crawlers.services import CrawlerService
from crawlers.utils import get_random_delay

from .constants import JOB_RETENTION_DAYS, POPULAR_KEYWORDS, RECENT_SEARCH_HOURS, RECENT_SEARCH_LIMIT
from .models import JobPosting

logger = logging.getLogger(__name__)


@shared_task
def crawl_popular_keywords():
    """인기 키워드 크롤링 태스크."""
    logger.info("Starting popular keywords crawl")

    for keyword in POPULAR_KEYWORDS:
        crawl_and_save.delay(keyword)

    logger.info(f"Queued {len(POPULAR_KEYWORDS)} crawl tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def crawl_and_save(self, keyword: str):
    """
    단일 키워드 크롤링 후 DB 저장.

    Celery task는 동기이므로 async 코드를 래핑.
    """
    try:
        async_to_sync(_crawl_and_save_async)(keyword)
        logger.info(f"Completed crawl for: {keyword}")
    except Exception as error:
        logger.error(f"Crawl failed for {keyword}: {error}")
        raise self.retry(exc=error) from error


async def _crawl_and_save_async(keyword: str):
    """실제 비동기 크롤링 로직."""
    max_pages = settings.BATCH_CRAWL_MAX_PAGES
    crawler_service = CrawlerService()

    total_jobs = 0
    for page_num in range(1, max_pages + 1):
        try:
            results, job_ids = await crawler_service.crawl_page(
                keyword, page=page_num, filters=None, save_to_db=True
            )
            total_jobs += len(results)

            if job_ids:
                generate_embeddings_task.delay(job_ids)

            if page_num < max_pages:
                delay = get_random_delay()
                await asyncio.sleep(delay)
        except Exception as error:
            logger.error(f"Crawl failed for {keyword} page {page_num}: {error}")

    logger.info(f"Batch crawl completed: {total_jobs} jobs for '{keyword}'")


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
        if keyword not in POPULAR_KEYWORDS:
            crawl_and_save.delay(keyword)


@shared_task
def cleanup_old_job_postings():
    """오래된 채용 공고 삭제."""
    cutoff = timezone.now() - timedelta(days=JOB_RETENTION_DAYS)
    deleted_count, _ = JobPosting.objects.filter(crawled_at__lt=cutoff).delete()
    logger.info(f"Deleted {deleted_count} job postings older than {JOB_RETENTION_DAYS} days")


@shared_task
def generate_embeddings_task(job_ids: list[int]):
    """
    백그라운드에서 임베딩 생성.

    크롤링 결과 저장 후 비동기로 임베딩 생성하여 응답 속도 향상.
    """
    if not job_ids:
        return

    async_to_sync(_generate_embeddings_async)(job_ids)


async def _generate_embeddings_async(job_ids: list[int]):
    """실제 임베딩 생성 로직."""
    job_service = JobService()
    count = await job_service.generate_embeddings_for_jobs(job_ids)
    logger.info(f"Background embedding generation completed: {count} jobs")
