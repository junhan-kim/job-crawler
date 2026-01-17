"""에이전트 상태 정의."""

from typing import TypedDict


class AgentState(TypedDict):
    """에이전트 상태."""

    query: str
    parsed_conditions: dict | None
    search_plan: dict | None
    crawl_results: list[dict] | None
    crawl_error: str | None
    response: str | None
    final_results: list[dict] | None
