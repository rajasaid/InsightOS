"""
agent/tools.py
Tool definitions and schemas for Claude API tool use
"""

from typing import Dict, List, Any
from pathlib import Path
from mcp_servers import get_mcp_config
from utils.logger import get_logger

logger = get_logger(__name__)


class ToolDefinitions:
    """
    Defines tools available to Claude when agentic mode is enabled
    """
    
    @staticmethod
    def get_filesystem_tools() -> List[Dict[str, Any]]:
        """
        Get filesystem tool definitions for Claude API
        
        Returns:
            List of tool definition dictionaries
        """
        mcp_config = get_mcp_config()
        output_dir = mcp_config.get_output_dir()
        
        return [
            {
                "name": "create_file",
                "description": (
                    f"Create a new file with specified content in the generated files directory. "
                    f"Available subdirectories: summaries/, reports/, extracts/, templates/. "
                    f"Files are saved to: {output_dir}/<subdirectory>/<filename>"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Name of the file to create (e.g., 'summary.txt', 'report.md')"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        },
                        "subdirectory": {
                            "type": "string",
                            "enum": ["summaries", "reports", "extracts", "templates"],
                            "description": "Subdirectory to save the file in. Choose based on content type."
                        }
                    },
                    "required": ["filename", "content", "subdirectory"]
                }
            },
            {
                "name": "read_document",
                "description": (
                    "Read the full contents of a document from the user's indexed files. "
                    "Use this when you need more context than what's in the RAG chunks. "
                    "The filepath should come from the RAG search results."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Full path to the document to read"
                        }
                    },
                    "required": ["filepath"]
                }
            },
            {
                "name": "list_generated_files",
                "description": (
                    "List all files that have been generated in the output directory. "
                    "Useful for checking what files exist before creating new ones."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subdirectory": {
                            "type": "string",
                            "enum": ["summaries", "reports", "extracts", "templates", "all"],
                            "description": "Which subdirectory to list, or 'all' for all files"
                        }
                    },
                    "required": ["subdirectory"]
                }
            }
        ]
    
    @staticmethod
    def get_search_tools() -> List[Dict[str, Any]]:
        """
        Get search tool definitions (Brave Search if enabled)
        
        Returns:
            List of tool definition dictionaries
        """
        mcp_config = get_mcp_config()
        
        # Only include if Brave Search is enabled
        if "brave-search" not in mcp_config.get_enabled_servers():
            return []
        
        return [
            {
                "name": "web_search",
                "description": (
                    "Search the web using Brave Search. Use this when you need information "
                    "that's not available in the user's documents or when current data is needed."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of results to return (1-10)",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    
    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        """
        Get all available tool definitions based on enabled MCP servers
        
        Returns:
            Complete list of tool definitions
        """
        tools = []
        
        mcp_config = get_mcp_config()
        enabled_servers = mcp_config.get_enabled_servers()
        
        # Add filesystem tools if filesystem server is enabled
        if "filesystem" in enabled_servers:
            tools.extend(ToolDefinitions.get_filesystem_tools())
            logger.info("Added filesystem tools (create_file, read_document, list_generated_files)")
        
        # Add search tools if Brave Search is enabled
        if "brave-search" in enabled_servers:
            tools.extend(ToolDefinitions.get_search_tools())
            logger.info("Added web search tools")
        
        logger.info(f"Total tools available: {len(tools)}")
        
        return tools
    
    @staticmethod
    def get_tool_names() -> List[str]:
        """
        Get names of all available tools
        
        Returns:
            List of tool names
        """
        tools = ToolDefinitions.get_all_tools()
        return [tool["name"] for tool in tools]


# Convenience function
def get_tools_for_claude() -> List[Dict[str, Any]]:
    """
    Get tool definitions for Claude API
    
    Returns:
        List of tool definitions, or empty list if agentic mode disabled
    """
    from security.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Only return tools if agentic mode is enabled
    if not config.get('agentic_mode_enabled', False):
        logger.info("Agentic mode disabled - no tools provided")
        return []
    
    tools = ToolDefinitions.get_all_tools()
    logger.info(f"Providing {len(tools)} tools to Claude (agentic mode enabled)")
    
    return tools