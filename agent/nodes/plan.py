"""검색 전략 수립 노드."""

import logging

from django.conf import settings

from agent.models import ParsedQuery, SearchFilters, SearchPlan
from agent.state import AgentState

logger = logging.getLogger(__name__)


async def plan_node(state: AgentState) -> dict:
    """
    파싱된 조건을 바탕으로 검색 전략 수립.

    Input: parsed_conditions, query
    Output: search_plan
    """
    conditions = ParsedQuery(**state["parsed_conditions"])
    original_query = state.get("query", "")
    logger.info(f"Planning search with conditions: {conditions}")

    keywords = _build_keywords(conditions)
    search_plan = _create_search_plan(keywords, conditions, original_query)

    logger.info(f"Search plan: {search_plan.model_dump()}")
    return {"search_plan": search_plan.model_dump()}


def _build_keywords(conditions: ParsedQuery) -> list[str]:
    """검색 키워드 목록 생성."""
    keywords = []

    if conditions.role:
        keywords.append(conditions.role)

    if conditions.skills:
        keywords.extend(conditions.skills)

    return keywords


def _create_search_plan(
    keywords: list[str], conditions: ParsedQuery, original_query: str
) -> SearchPlan:
    """검색 계획 생성."""
    search_keyword = " ".join(keywords) if keywords else original_query

    return SearchPlan(
        keywords=keywords,
        search_keyword=search_keyword,
        filters=SearchFilters(
            experience=conditions.experience,
            location=conditions.location,
        ),
        max_pages=settings.AGENT_CRAWL_MAX_PAGES,
    )
