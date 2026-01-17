"""결과 종합 및 응답 생성 노드."""

import logging

from agent.state import AgentState
from agent.models import ParsedQuery
from crawlers.models import JobPosting

logger = logging.getLogger(__name__)


async def synthesize_node(state: AgentState) -> dict:
    """
    검색 결과를 종합하고 최종 응답 생성.

    Input: parsed_conditions, crawl_results, crawl_error
    Output: response, final_results
    """
    conditions = ParsedQuery(**state["parsed_conditions"])
    results = state["crawl_results"] or []
    error = state["crawl_error"]

    logger.info(f"Synthesizing results: {len(results)} jobs, error={error}")

    if error:
        return _error_response(error)

    if not results:
        return _empty_response()

    filtered_results = _apply_filters(results, conditions)
    response = _generate_response(conditions, filtered_results)

    return {
        "response": response,
        "final_results": filtered_results,
    }


def _error_response(error: str) -> dict:
    """에러 응답 생성."""
    return {
        "response": f"검색 중 오류가 발생했습니다: {error}",
        "final_results": [],
    }


def _empty_response() -> dict:
    """빈 결과 응답 생성."""
    return {
        "response": "검색 조건에 맞는 채용공고를 찾지 못했습니다.",
        "final_results": [],
    }


def _apply_filters(results: list[dict], conditions: ParsedQuery) -> list[dict]:
    """조건에 따라 결과 필터링."""
    jobs = [JobPosting(**r) for r in results]

    if conditions.location:
        jobs = [j for j in jobs if conditions.location in (j.location or "")]

    return [j.model_dump() for j in jobs]


def _generate_response(conditions: ParsedQuery, results: list[dict]) -> str:
    """응답 메시지 생성."""
    parts = []

    if conditions.role:
        parts.append(conditions.role)
    if conditions.skills:
        parts.append(", ".join(conditions.skills))
    if conditions.location:
        parts.append(conditions.location)

    condition_str = " / ".join(parts) if parts else "전체"

    return f"'{condition_str}' 조건으로 {len(results)}개의 채용공고를 찾았습니다."
