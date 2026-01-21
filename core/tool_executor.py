"""
core/tool_executor.py
Executes tools (built-in and MCP) requested by Claude
"""

from typing import List, Dict, Any, Optional, Callable
import json

from indexing.chromadb_client import ChromaDBClient
from utils.logger import get_logger
from utils.file_utils import read_text_file, list_files_in_directory

logger = get_logger(__name__)


class ToolResult:
    """Represents the result of a tool execution"""
    
    def __init__(
        self,
        tool_name: str,
        success: bool,
        result: Any,
        error: Optional[str] = None
    ):
        """
        Initialize tool result
        
        Args:
            tool_name: Name of the tool
            success: Whether execution succeeded
            result: Tool result (any type)
            error: Error message if failed
        """
        self.tool_name = tool_name
        self.success = success
        self.result = result
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'tool_name': self.tool_name,
            'success': self.success,
            'result': self.result,
            'error': self.error
        }
    
    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"ToolResult({self.tool_name}, {status})"


class ToolExecutor:
    """
    Executes tools requested by Claude (built-in and MCP)
    """
    
    def __init__(
        self,
        chromadb_client: Optional[ChromaDBClient] = None,
        mcp_client: Optional[Any] = None
    ):
        """
        Initialize tool executor
        
        Args:
            chromadb_client: ChromaDB client for search_documents
            mcp_client: MCP client for MCP server tools
        """
        self.chromadb_client = chromadb_client or ChromaDBClient()
        self.mcp_client = mcp_client
        
        # Register built-in tools
        self._builtin_tools = {
            'search_documents': self._search_documents,
            'list_indexed_files': self._list_indexed_files,
            'get_file_content': self._get_file_content,
            'get_file_info': self._get_file_info,
        }
        
        logger.info(f"ToolExecutor initialized with {len(self._builtin_tools)} built-in tools")
    
    # ========================================================================
    # Public API - Tool Execution
    # ========================================================================
    
    def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute a tool by name
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters
        
        Returns:
            ToolResult with execution result
        """
        logger.info(f"Executing tool: {tool_name}")
        logger.debug(f"Tool input: {tool_input}")
        
        try:
            # Check if it's a built-in tool
            if tool_name in self._builtin_tools:
                result = self._execute_builtin_tool(tool_name, tool_input)
                return ToolResult(
                    tool_name=tool_name,
                    success=True,
                    result=result
                )
            
            # Check if it's an MCP tool
            elif self.mcp_client and self._is_mcp_tool(tool_name):
                result = self._execute_mcp_tool(tool_name, tool_input)
                return ToolResult(
                    tool_name=tool_name,
                    success=True,
                    result=result
                )
            
            # Tool not found
            else:
                error_msg = f"Unknown tool: {tool_name}"
                logger.error(error_msg)
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    result=None,
                    error=error_msg
                )
        
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e)
            )
    
    def execute_tools(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[ToolResult]:
        """
        Execute multiple tools
        
        Args:
            tool_calls: List of tool call dicts with 'name' and 'input'
        
        Returns:
            List of ToolResult objects
        """
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get('name')
            tool_input = tool_call.get('input', {})
            
            result = self.execute_tool(tool_name, tool_input)
            results.append(result)
        
        return results
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of all available tools (built-in + MCP)
        
        Returns:
            List of tool definitions
        """
        tools = []
        
        # Add built-in tools
        tools.extend(self._get_builtin_tool_definitions())
        
        # Add MCP tools if available
        if self.mcp_client:
            tools.extend(self._get_mcp_tool_definitions())
        
        return tools
    
    # ========================================================================
    # Built-in Tools
    # ========================================================================
    
    def _execute_builtin_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> Any:
        """
        Execute a built-in tool
        
        Args:
            tool_name: Tool name
            tool_input: Tool input
        
        Returns:
            Tool result
        """
        tool_func = self._builtin_tools.get(tool_name)
        
        if not tool_func:
            raise ValueError(f"Built-in tool not found: {tool_name}")
        
        return tool_func(**tool_input)
    
    def _search_documents(
        self,
        query: str,
        top_k: int = 5,
        file_type_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search indexed documents
        
        Args:
            query: Search query
            top_k: Number of results
            file_type_filter: Optional file type filter (e.g., ".pdf")
        
        Returns:
            Search results
        """
        logger.info(f"Searching documents: {query}")
        
        # Build metadata filter
        where = None
        if file_type_filter:
            where = {"file_type": file_type_filter}
        
        # Query ChromaDB
        results = self.chromadb_client.query(
            query_text=query,
            top_k=top_k,
            where=where
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'content': result['document'],
                'metadata': result['metadata'],
                'relevance': 1.0 - (result.get('distance', 0) / 2.0)  # Normalize to 0-1
            })
        
        return {
            'query': query,
            'num_results': len(formatted_results),
            'results': formatted_results
        }
    
    def _list_indexed_files(
        self,
        file_type_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List all indexed files
        
        Args:
            file_type_filter: Optional file type filter
            limit: Optional limit on number of files
        
        Returns:
            List of indexed files
        """
        logger.info("Listing indexed files")
        
        # Get all indexed files
        all_files = self.chromadb_client.get_indexed_files()
        
        # Apply file type filter
        if file_type_filter:
            all_files = [
                f for f in all_files
                if f.endswith(file_type_filter)
            ]
        
        # Apply limit
        if limit:
            all_files = all_files[:limit]
        
        return {
            'total_files': len(all_files),
            'files': all_files
        }
    
    def _get_file_content(
        self,
        filepath: str,
        max_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get content of a specific file
        
        Args:
            filepath: Path to file
            max_length: Optional max length to return
        
        Returns:
            File content and metadata
        """
        logger.info(f"Getting file content: {filepath}")
        
        try:
            # Check if file is indexed
            if not self.chromadb_client.file_is_indexed(filepath):
                return {
                    'success': False,
                    'error': f"File not indexed: {filepath}"
                }
            
            # Get all chunks for this file
            results = self.chromadb_client.get_documents_by_file(filepath)
            
            if not results or not results['documents']:
                return {
                    'success': False,
                    'error': f"No content found for file: {filepath}"
                }
            
            # Combine all chunks
            content = '\n\n'.join(results['documents'])
            
            # Apply max length
            if max_length and len(content) > max_length:
                content = content[:max_length] + "... [truncated]"
            
            # Get metadata from first chunk
            metadata = results['metadatas'][0] if results['metadatas'] else {}
            
            return {
                'success': True,
                'filepath': filepath,
                'content': content,
                'num_chunks': len(results['documents']),
                'metadata': metadata
            }
        
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_file_info(
        self,
        filepath: str
    ) -> Dict[str, Any]:
        """
        Get metadata about a file
        
        Args:
            filepath: Path to file
        
        Returns:
            File metadata
        """
        logger.info(f"Getting file info: {filepath}")
        
        try:
            # Get file from ChromaDB
            results = self.chromadb_client.get_documents_by_file(filepath)
            
            if not results or not results['metadatas']:
                return {
                    'success': False,
                    'error': f"File not found in index: {filepath}"
                }
            
            # Get metadata from first chunk
            metadata = results['metadatas'][0]
            
            return {
                'success': True,
                'filepath': filepath,
                'filename': metadata.get('filename'),
                'file_type': metadata.get('file_type'),
                'file_size': metadata.get('file_size'),
                'num_chunks': len(results['documents']),
                'timestamp': metadata.get('timestamp')
            }
        
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========================================================================
    # Built-in Tool Definitions
    # ========================================================================
    
    def _get_builtin_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get definitions for built-in tools
        
        Returns:
            List of tool definitions in Claude format
        """
        return [
            {
                "name": "search_documents",
                "description": "Search through indexed documents using semantic search. Returns relevant chunks of text from the user's documents.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5
                        },
                        "file_type_filter": {
                            "type": "string",
                            "description": "Optional file type filter (e.g., '.pdf', '.txt')"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_indexed_files",
                "description": "List all files currently in the document index.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_type_filter": {
                            "type": "string",
                            "description": "Optional file type filter (e.g., '.pdf')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of files to return"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_file_content",
                "description": "Get the full content of a specific indexed file.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Full path to the file"
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum length of content to return"
                        }
                    },
                    "required": ["filepath"]
                }
            },
            {
                "name": "get_file_info",
                "description": "Get metadata about a specific file (size, type, chunks, etc.).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Full path to the file"
                        }
                    },
                    "required": ["filepath"]
                }
            }
        ]
    
    # ========================================================================
    # MCP Tool Integration
    # ========================================================================
    
    def _is_mcp_tool(self, tool_name: str) -> bool:
        """
        Check if tool is an MCP tool
        
        Args:
            tool_name: Tool name
        
        Returns:
            True if MCP tool, False otherwise
        """
        if not self.mcp_client:
            return False
        
        # Check if tool is in MCP client's available tools
        try:
            mcp_tools = self.mcp_client.list_tools()
            return tool_name in [t['name'] for t in mcp_tools]
        except Exception as e:
            logger.error(f"Error checking MCP tools: {e}")
            return False
    
    def _execute_mcp_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> Any:
        """
        Execute an MCP tool
        
        Args:
            tool_name: Tool name
            tool_input: Tool input
        
        Returns:
            Tool result
        """
        if not self.mcp_client:
            raise RuntimeError("MCP client not available")
        
        logger.info(f"Executing MCP tool: {tool_name}")
        
        # Call MCP client
        result = self.mcp_client.call_tool(tool_name, tool_input)
        
        return result
    
    def _get_mcp_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions from MCP servers
        
        Returns:
            List of MCP tool definitions
        """
        if not self.mcp_client:
            return []
        
        try:
            return self.mcp_client.list_tools()
        except Exception as e:
            logger.error(f"Error getting MCP tool definitions: {e}")
            return []
    
    # ========================================================================
    # Utilities
    # ========================================================================
    
    def format_tool_result_for_claude(self, result: ToolResult) -> str:
        """
        Format tool result for Claude's consumption
        
        Args:
            result: ToolResult
        
        Returns:
            Formatted string
        """
        if result.success:
            # Format successful result
            if isinstance(result.result, dict):
                formatted = json.dumps(result.result, indent=2)
            else:
                formatted = str(result.result)
            
            return f"Tool '{result.tool_name}' executed successfully:\n\n{formatted}"
        else:
            # Format error
            return f"Tool '{result.tool_name}' failed: {result.error}"


# ============================================================================
# Testing/Debug
# ============================================================================

def test_tool_executor():
    """Test tool executor"""
    logger.info("Testing ToolExecutor...")
    
    executor = ToolExecutor()
    
    # Test search_documents
    result = executor.execute_tool(
        'search_documents',
        {'query': 'machine learning', 'top_k': 3}
    )
    logger.info(f"Search result: {result}")
    
    # Test list_indexed_files
    result = executor.execute_tool(
        'list_indexed_files',
        {'limit': 10}
    )
    logger.info(f"List result: {result}")
    
    # Test available tools
    tools = executor.get_available_tools()
    logger.info(f"Available tools: {len(tools)}")
    for tool in tools:
        logger.info(f"  - {tool['name']}: {tool['description']}")


if __name__ == "__main__":
    test_tool_executor()