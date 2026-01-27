"""크롤러 실행 노드."""

import asyncio
import logging

from agent.constants import SERVER_BUSY_MESSAGE
from agent.models import ExecuteResult, SearchPlan
from agent.state import AgentState
from agent.tools.rag import RAGTool
from apps.jobs.tasks import generate_embeddings_task
from core.performance import PerformanceTracker
from crawlers import CrawlerError, SearchFilters
from crawlers.services import CrawlerService
from crawlers.utils import CRAWLER_TIMEOUT, crawler_semaphore

logger = logging.getLogger(__name__)


async def execute_node(state: AgentState) -> dict:
    """
    크롤링 수행 및 RAG 추천 (page==1일 때만).

    Input: search_plan, page (optional)
    Output: crawl_results, crawl_error, recommendations
    """
    plan = SearchPlan(**state["search_plan"])
    page = state.get("page", 1)
    filters = SearchFilters(
        experience=plan.filters.experience,
        location=plan.filters.location,
    )

    logger.info(f"Executing search: keyword='{plan.search_keyword}', page={page}")

    try:
        async with asyncio.timeout(CRAWLER_TIMEOUT):
            async with crawler_semaphore:
                if page == 1:
                    crawl_task = _execute_crawling(plan.search_keyword, page, filters)
                    rag_task = _search_from_rag(plan.search_keyword, filters)
                    crawl_result, recommendations = await asyncio.gather(
                        crawl_task, rag_task
                    )
                    crawl_result["recommendations"] = recommendations
                    return crawl_result
                return await _execute_crawling(plan.search_keyword, page, filters)
    except TimeoutError:
        logger.warning("Crawler semaphore timeout - server busy")
        return ExecuteResult(crawl_error=SERVER_BUSY_MESSAGE).model_dump()


async def _execute_crawling(keyword: str, page: int, filters: SearchFilters) -> dict:
    """실제 크롤링 수행."""
    tracker = PerformanceTracker("crawling").start()

    try:
        crawler_service = CrawlerService()
        results, job_ids = await crawler_service.crawl_page(
            keyword, page=page, filters=filters
        )
        crawl_results = [job.model_dump() for job in results]

        if job_ids:
            generate_embeddings_task.delay(job_ids)

        tracker.stop()
        logger.info(f"Crawling completed: {len(crawl_results)} jobs found")
        return ExecuteResult(crawl_results=crawl_results).model_dump()

    except CrawlerError as error:
        logger.error(f"Crawler error: {error}")
        return ExecuteResult(crawl_error=str(error)).model_dump()

    except Exception as error:
        logger.error(f"Unexpected error: {error}")
        return ExecuteResult(crawl_error=f"Crawling error: {str(error)}").model_dump()


async def _search_from_rag(keyword: str, filters: SearchFilters) -> list[dict]:
    """RAG 벡터 검색."""
    try:
        rag_tool = RAGTool()
        rag_filters = {"location": filters.location} if filters.location else None
        results = await rag_tool.search(keyword, filters=rag_filters)

        if filters.experience is not None:
            results = [
                result for result in results
                if SearchFilters.matches_experience(result.experience, filters.experience)
            ]

        return [result.model_dump() for result in results]

    except Exception as error:
        logger.warning(f"RAG search failed, falling back to crawling: {error}")
        return []
