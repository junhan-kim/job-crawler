"""사용자 쿼리 파싱 노드."""

import json
import logging

from agent.exceptions import AgentError
from agent.models import ParsedQuery
from agent.prompts import ParsePrompt
from agent.state import AgentState
from llm import OllamaProvider

logger = logging.getLogger(__name__)


async def parse_node(state: AgentState) -> dict:
    """
    사용자 쿼리를 파싱하여 구조화된 검색 조건 추출.

    Input: query
    Output: parsed_conditions
    """
    query = state.get("query")
    if not query:
        raise AgentError("Query is empty")
    logger.info(f"Parsing query: {query}")

    llm = OllamaProvider()
    prompt = ParsePrompt.format(query=query)

    try:
        llm_response = await llm.chat(prompt)
        data = json.loads(llm_response.content)
        parsed = ParsedQuery(**data)
        logger.info(f"Parsed conditions: {parsed.model_dump()}")
        return {"parsed_conditions": parsed.model_dump()}
    except Exception as e:
        logger.error(f"Parse error: {e}")
        return {"parsed_conditions": ParsedQuery().model_dump()}
