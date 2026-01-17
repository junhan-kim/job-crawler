import json
from enum import StrEnum
from typing import TypedDict
from langgraph.graph import StateGraph, END
from llm import OllamaProvider
from .models import ParsedQuery
from .formatter import ResponseFormatter
from .prompts import ParsePrompt


class NodeName(StrEnum):
    PARSE = "parse"
    RESPOND = "respond"


class StateKey(StrEnum):
    QUERY = "query"
    PARSED = "parsed"
    RESPONSE = "response"


class AgentState(TypedDict):
    query: str
    parsed: dict | None
    response: str | None


async def parse_node(state: AgentState) -> dict:
    llm = OllamaProvider()
    prompt = ParsePrompt.format(query=state[StateKey.QUERY])
    llm_response = await llm.chat(prompt)
    data = json.loads(llm_response.content)
    parsed = ParsedQuery(**data)
    return {StateKey.PARSED: parsed.model_dump()}


async def respond_node(state: AgentState) -> dict:
    data = state.get(StateKey.PARSED) or {}
    parsed = ParsedQuery(**data)
    return {StateKey.RESPONSE: ResponseFormatter.format(parsed)}


def create_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node(NodeName.PARSE, parse_node)
    workflow.add_node(NodeName.RESPOND, respond_node)
    workflow.add_edge(NodeName.PARSE, NodeName.RESPOND)
    workflow.add_edge(NodeName.RESPOND, END)
    workflow.set_entry_point(NodeName.PARSE)
    return workflow.compile()


graph = create_graph()


async def run_agent(query: str) -> dict:
    result = await graph.ainvoke({
        StateKey.QUERY: query,
        StateKey.PARSED: None,
        StateKey.RESPONSE: None,
    })
    return {
        StateKey.QUERY: query,
        StateKey.PARSED: result.get(StateKey.PARSED),
        StateKey.RESPONSE: result.get(StateKey.RESPONSE),
    }
