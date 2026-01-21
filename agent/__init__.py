"""
Agent Layer for InsightOS
Handles Claude API integration with MCP support
"""

from .claude_client import ClaudeClient
from .file_generator import FileGenerator, get_file_generator
from .prompts import build_system_prompt
from .tools import ToolDefinitions
#from .tool_executor import ToolExecutor, get_tool_executor

__all__ = [
    "ClaudeClient",
    "FileGenerator",
    "get_file_generator",
    "build_system_prompt",
    "ToolDefinitions",
 #   "ToolExecutor",
  #  "get_tool_executor"
]