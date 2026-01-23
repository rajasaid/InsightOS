"""
Agent Layer for InsightOS
Handles Claude API integration with MCP support
"""

from .claude_client import ClaudeClient

__all__ = [
    "ClaudeClient",
]