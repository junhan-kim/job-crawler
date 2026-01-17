"""에이전트 워크플로우 정의."""

import time
from enum import StrEnum

from langgraph.graph import END, StateGraph

from .exceptions import AgentError
from .nodes import execute_node, parse_node, plan_node, synthesize_node
from .state import AgentState


class NodeName(StrEnum):
    PARSE = "parse"
    PLAN = "plan"
    EXECUTE = "execute"
    SYNTHESIZE = "synthesize"


def create_graph():
    """워크플로우 그래프 생성."""
    workflow = StateGraph(AgentState)

    workflow.add_node(NodeName.PARSE, parse_node)
    workflow.add_node(NodeName.PLAN, plan_node)
    workflow.add_node(NodeName.EXECUTE, execute_node)
    workflow.add_node(NodeName.SYNTHESIZE, synthesize_node)

    workflow.add_edge(NodeName.PARSE, NodeName.PLAN)
    workflow.add_edge(NodeName.PLAN, NodeName.EXECUTE)
    workflow.add_edge(NodeName.EXECUTE, NodeName.SYNTHESIZE)
    workflow.add_edge(NodeName.SYNTHESIZE, END)

    workflow.set_entry_point(NodeName.PARSE)

    return workflow.compile()


graph = create_graph()


async def run_agent(query: str) -> dict:
    """에이전트 실행."""
    start_time = time.perf_counter()

    initial_state = {
        "query": query,
        "parsed_conditions": None,
        "search_plan": None,
        "crawl_results": None,
        "crawl_error": None,
        "response": None,
        "final_results": None,
    }

    result = await graph.ainvoke(initial_state)

    response = result.get("response")
    if not response:
        raise AgentError("Failed to generate LLM response")

    final_results = result.get("final_results") or []
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    return {
        "query": query,
        "parsed_conditions": result.get("parsed_conditions"),
        "response": response,
        "results": final_results,
        "total_count": len(final_results),
        "search_time_ms": elapsed_ms,
    }
