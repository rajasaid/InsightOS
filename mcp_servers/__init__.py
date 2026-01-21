"""
InsightOS MCP Servers Package

Manages Model Context Protocol server configurations for safe file writing
and knowledge synthesis capabilities.
"""

from .config import (
    MCPConfig,
    MCPServerConfig,
    get_mcp_config
)
from .client import MCPClient, get_mcp_client

__version__ = "0.1.0"
__all__ = [
    "MCPConfig",
    "MCPServerConfig", 
    "get_mcp_config",
    "MCPClient",
    "get_mcp_client"
]