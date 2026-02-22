"""Web search tool for research agent to fetch external context using DuckDuckGo."""

import logging
import re

import requests
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import Tool
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WebSearchInput(BaseModel):
    """Input schema for web search operations."""

    query: str


def web_search(query: str) -> str:
    """Execute a web search using DuckDuckGo and return results as text. Uses langchain_community's DuckDuckGoSearchRun to perform the search, returning a formatted string of top results. Query is logged at INFO level."""
    try:
        logger.info(f"Executing web search for query: {query}")
        search_tool = DuckDuckGoSearchRun()
        results = search_tool.run(query)
        logger.info(f"Web search returned {len(results)} characters")
        return results
    except Exception as e:
        logger.warning(f"Web search failed for '{query}': {str(e)}")
        return f"Web search error: {str(e)}"


def fetch_url_content(url: str) -> str:
    """Fetch and extract text content from a URL with 10 second timeout. Strips HTML tags and caps output at 3000 characters, appending truncation notice if needed. Network errors are caught and returned as error messages."""
    try:
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        content = response.text
        # Simple HTML tag stripping
        content = re.sub(r"<[^>]+>", " ", content)
        # Collapse whitespace
        content = re.sub(r"\s+", " ", content).strip()
        
        if len(content) > 3000:
            content = content[:3000] + "\n[Content truncated at 3000 characters]"
        
        logger.info(f"Extracted {len(content)} characters from {url}")
        return content
    except requests.Timeout:
        error_msg = f"URL fetch timeout (10s): {url}"
        logger.warning(error_msg)
        return error_msg
    except requests.RequestException as e:
        error_msg = f"Failed to fetch URL {url}: {str(e)}"
        logger.warning(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error fetching {url}: {str(e)}"
        logger.warning(error_msg)
        return error_msg


def get_web_search_tool() -> Tool:
    """Return a configured LangChain Tool wrapping the web_search function for use in agent chains."""
    return Tool.from_function(
        func=web_search,
        name="web_search",
        description="Search the web using DuckDuckGo for real-time information on a topic",
        args_schema=WebSearchInput,
    )
