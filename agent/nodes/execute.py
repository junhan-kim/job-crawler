"""크롤러 실행 노드."""

import asyncio
import logging

from crawlers import SaraminCrawler, CrawlerError
from crawlers.utils import crawler_semaphore, CRAWLER_WAIT_TIMEOUT_SECONDS
from agent.state import AgentState
from agent.models import SearchPlan

logger = logging.getLogger(__name__)

SERVER_BUSY_MESSAGE = "Server is busy. Please try again later."


async def execute_node(state: AgentState) -> dict:
    """
    크롤러를 실행하여 실제 검색 수행.

    Input: search_plan
    Output: crawl_results, crawl_error
    """
    plan = SearchPlan(**state["search_plan"])

    logger.info(f"Executing search: keyword='{plan.search_keyword}', max_pages={plan.max_pages}")

    try:
        async with asyncio.timeout(CRAWLER_WAIT_TIMEOUT_SECONDS):
            async with crawler_semaphore:
                return await _execute_crawling(plan.search_keyword, plan.max_pages)
    except TimeoutError:
        logger.warning("Crawler semaphore timeout - server busy")
        return {
            "crawl_results": [],
            "crawl_error": SERVER_BUSY_MESSAGE,
        }


async def _execute_crawling(keyword: str, max_pages: int) -> dict:
    """실제 크롤링 수행."""
    try:
        crawler = SaraminCrawler()
        results = await crawler.search(keyword, max_pages=max_pages)

        crawl_results = [job.model_dump() for job in results]

        logger.info(f"Crawling completed: {len(crawl_results)} jobs found")
        return {
            "crawl_results": crawl_results,
            "crawl_error": None,
        }

    except CrawlerError as e:
        logger.error(f"Crawler error: {e}")
        return {
            "crawl_results": [],
            "crawl_error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "crawl_results": [],
            "crawl_error": f"Crawling error: {str(e)}",
        }
