"""크롤러 실행 노드."""

import asyncio
import logging

from agent.models import SearchPlan
from agent.state import AgentState
from crawlers import CrawlerError, JobKoreaCrawler, SaraminCrawler
from crawlers.utils import CRAWLER_TIMEOUT, crawler_semaphore

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
        async with asyncio.timeout(CRAWLER_TIMEOUT):
            async with crawler_semaphore:
                return await _execute_crawling(plan.search_keyword, plan.max_pages)
    except TimeoutError:
        logger.warning("Crawler semaphore timeout - server busy")
        return {
            "crawl_results": [],
            "crawl_error": SERVER_BUSY_MESSAGE,
        }


async def _execute_crawling(keyword: str, max_pages: int) -> dict:
    """실제 크롤링 수행 (사람인 + 잡코리아 병렬)."""
    try:
        saramin_crawler = SaraminCrawler()
        jobkorea_crawler = JobKoreaCrawler()

        saramin_results, jobkorea_results = await asyncio.gather(
            saramin_crawler.search(keyword, max_pages=max_pages),
            jobkorea_crawler.search(keyword, max_pages=max_pages),
            return_exceptions=True,
        )

        all_results = []

        if isinstance(saramin_results, Exception):
            logger.error(f"Saramin crawler error: {saramin_results}")
        else:
            all_results.extend(saramin_results)

        if isinstance(jobkorea_results, Exception):
            logger.error(f"JobKorea crawler error: {jobkorea_results}")
        else:
            all_results.extend(jobkorea_results)

        crawl_results = [job.model_dump() for job in all_results]

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
