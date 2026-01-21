"""크롤러 실행 노드."""

import asyncio
import logging

from django.conf import settings

from agent.models import ExecuteResult, SearchPlan
from agent.state import AgentState
from agent.tools.rag import RAGTool
from apps.jobs.services import JobService
from apps.jobs.tasks import generate_embeddings_task
from core.performance import PerformanceTracker
from crawlers import CrawlerError, CrawlerService
from crawlers.models import JobPosting as CrawlerJobPosting
from crawlers.utils import CRAWLER_TIMEOUT, crawler_semaphore

logger = logging.getLogger(__name__)
RAG_MIN_RESULTS = 5

SERVER_BUSY_MESSAGE = "Server is busy. Please try again later."


async def execute_node(state: AgentState) -> dict:
    """
    RAG 검색 후 결과 부족 시 크롤링 수행.

    Input: search_plan
    Output: crawl_results, crawl_error
    """
    plan = SearchPlan(**state["search_plan"])

    logger.info(f"Executing search: keyword='{plan.search_keyword}'")

    if settings.DB_SAVE_ENABLED:
        rag_results = await _search_from_rag(plan.search_keyword)
        if len(rag_results) >= RAG_MIN_RESULTS:
            logger.info(f"RAG search sufficient: {len(rag_results)} results")
            return ExecuteResult(crawl_results=rag_results).model_dump()

    try:
        async with asyncio.timeout(CRAWLER_TIMEOUT):
            async with crawler_semaphore:
                return await _execute_crawling(plan.search_keyword)
    except TimeoutError:
        logger.warning("Crawler semaphore timeout - server busy")
        return ExecuteResult(crawl_error=SERVER_BUSY_MESSAGE).model_dump()


async def _execute_crawling(keyword: str) -> dict:
    """실제 크롤링 수행 (사람인 + 잡코리아 병렬, 페이지 1만)."""
    tracker = PerformanceTracker("crawling").start()

    try:
        crawler_service = CrawlerService()
        all_results = await crawler_service.crawl_page(keyword, page=1)
        tracker.checkpoint("parallel_crawl")

        if settings.DB_SAVE_ENABLED and all_results:
            await _save_to_db(all_results)
            tracker.checkpoint("db_save")

        crawl_results = [job.model_dump() for job in all_results]

        tracker.stop()
        logger.info(f"Crawling completed: {len(crawl_results)} jobs found")
        return ExecuteResult(crawl_results=crawl_results).model_dump()

    except CrawlerError as error:
        logger.error(f"Crawler error: {error}")
        return ExecuteResult(crawl_error=str(error)).model_dump()

    except Exception as error:
        logger.error(f"Unexpected error: {error}")
        return ExecuteResult(crawl_error=f"Crawling error: {str(error)}").model_dump()


async def _save_to_db(jobs: list[CrawlerJobPosting]) -> None:
    """크롤링 결과를 DB에 저장 후 임베딩은 백그라운드 처리."""
    job_service = JobService()

    try:
        _, job_ids = await job_service.save_batch(jobs, skip_embedding=True)
        if job_ids:
            generate_embeddings_task.delay(job_ids)
    except Exception as error:
        logger.warning(f"Failed to save jobs to DB: {error}")


async def _search_from_rag(keyword: str) -> list[dict]:
    """RAG 벡터 검색."""
    try:
        rag_tool = RAGTool()
        results = await rag_tool.search(keyword)
        return [result.model_dump() for result in results]

    except Exception as error:
        logger.warning(f"RAG search failed, falling back to crawling: {error}")
        return []
