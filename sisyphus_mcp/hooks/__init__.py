"""
Hooks module for Sisyphus MCP Server.
Contains keyword detection, todo continuation, and ralph loop logic.
"""

from sisyphus_mcp.hooks.keyword_detector import detect_keywords, KEYWORDS
from sisyphus_mcp.hooks.todo_continuation import should_continue, get_continuation_message

__all__ = [
    "detect_keywords",
    "KEYWORDS",
    "should_continue",
    "get_continuation_message"
]
