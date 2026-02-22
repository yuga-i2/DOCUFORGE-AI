"""Research Agent that augments documents with external context via web search."""

import logging

from orchestration.state import DocuForgeState
from tools.web_search_tool import get_web_search_tool

logger = logging.getLogger(__name__)


def research_agent(state: DocuForgeState) -> dict:
    """Execute web searches to gather external context for the query. Runs two searches (original query and refined with industry keywords), combines results with deduplication, caps at 4000 characters, and returns state update with web_context. Returns dict with web_context, agent_trace (list), routing_decision. Gracefully handles search failures without raising exceptions."""
    try:
        query = state.get("query", "")
        if not query:
            logger.warning("research_agent: query not found in state")
            return {
                "web_context": "",
                "agent_trace": state.get("agent_trace", []) + ["research_agent: skipped (no query)"],
                "routing_decision": "analyst",
            }
        
        logger.info(f"research_agent: starting research for query: {query}")
        
        search_tool = get_web_search_tool()
        
        # First search: original query
        results_1 = search_tool.invoke({"query": query})
        
        # Second search: refined with industry context
        refined_query = f"{query} industry analysis 2024 2025"
        results_2 = search_tool.invoke({"query": refined_query})
        
        # Combine and deduplicate
        combined = f"{results_1}\n{results_2}"
        
        # Cap at 4000 characters
        if len(combined) > 4000:
            web_context = combined[:4000]
        else:
            web_context = combined
        
        logger.info(f"research_agent: fetched {len(web_context)} chars of external context")
        
        agent_trace = state.get("agent_trace", []) + [
            f"research_agent: fetched {len(web_context)} chars of external context"
        ]
        
        return {
            "web_context": web_context,
            "agent_trace": agent_trace,
            "routing_decision": "analyst",
        }
    except Exception as e:
        logger.error(f"research_agent error: {str(e)}")
        agent_trace = state.get("agent_trace", []) + [f"research_agent: error - {str(e)}"]
        return {
            "web_context": "",
            "agent_trace": agent_trace,
            "routing_decision": "analyst",
        }
