"""에이전트 워크플로우 정의."""

from enum import StrEnum

from langgraph.graph import END, StateGraph

from core.performance import PerformanceTracker

from .constants import HAS_MORE_THRESHOLD, START_NODE
from .exceptions import AgentError
from .models import AgentResponse, ParsedQuery, SearchPlan
from .nodes import execute_node, parse_node, plan_node, synthesize_node
from .state import AgentState


class NodeName(StrEnum):
    PARSE = "parse"
    PLAN = "plan"
    EXECUTE = "execute"
    SYNTHESIZE = "synthesize"


def _route_start(state: AgentState) -> str:
    """시작 노드 라우팅: page > 1이면 execute로 직행."""
    if state.get("page", 1) > 1:
        return NodeName.EXECUTE
    return NodeName.PARSE


def create_graph():
    """워크플로우 그래프 생성."""
    workflow = StateGraph(AgentState)

    workflow.add_node(NodeName.PARSE, parse_node)
    workflow.add_node(NodeName.PLAN, plan_node)
    workflow.add_node(NodeName.EXECUTE, execute_node)
    workflow.add_node(NodeName.SYNTHESIZE, synthesize_node)

    workflow.add_conditional_edges(
        START_NODE,
        _route_start,
        {
            NodeName.PARSE: NodeName.PARSE,
            NodeName.EXECUTE: NodeName.EXECUTE,
        },
    )

    workflow.add_edge(NodeName.PARSE, NodeName.PLAN)
    workflow.add_edge(NodeName.PLAN, NodeName.EXECUTE)
    workflow.add_edge(NodeName.EXECUTE, NodeName.SYNTHESIZE)
    workflow.add_edge(NodeName.SYNTHESIZE, END)

    return workflow.compile()


graph = create_graph()


async def run_agent(
    query: str,
    page: int = 1,
    parsed_conditions: dict | None = None,
    search_plan: dict | None = None,
) -> AgentResponse:
    """
    에이전트 실행.

    Args:
        query: 검색 쿼리
        page: 페이지 번호 (1이면 첫 검색, 2 이상이면 load more)
        parsed_conditions: 이전에 파싱된 조건 (page > 1일 때 필수)
        search_plan: 이전 검색 계획 (page > 1일 때 필수)
    """
    tracker = PerformanceTracker("agent").start()

    initial_state: AgentState = {
        "query": query,
        "page": page,
        "parsed_conditions": parsed_conditions,
        "search_plan": search_plan,
        "crawl_results": None,
        "crawl_error": None,
        "recommendations": None,
        "response": None,
        "final_results": None,
    }

    result = await graph.ainvoke(initial_state)

    response = result.get("response")
    if not response:
        raise AgentError("Failed to generate LLM response")

    final_results = result.get("final_results") or []
    tracker.stop()
    result_parsed_conditions = result.get("parsed_conditions")
    result_search_plan = result.get("search_plan")

    return AgentResponse(
        query=query,
        page=page,
        parsed_conditions=ParsedQuery(**result_parsed_conditions) if result_parsed_conditions else None,
        search_plan=SearchPlan(**result_search_plan) if result_search_plan else None,
        response=response,
        results=final_results,
        recommendations=result.get("recommendations") or [],
        total_count=len(final_results),
        has_more=len(final_results) >= HAS_MORE_THRESHOLD,
        search_time_ms=int(tracker.elapsed_ms),
    )
