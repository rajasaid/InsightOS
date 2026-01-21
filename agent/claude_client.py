"""
agent/claude_client.py
Claude API Client with Traditional Tools + Real MCP Support
"""

import anthropic
from typing import List, Dict, Optional, Any

from core.tool_executor import ToolExecutor
from mcp_servers import get_mcp_config
from mcp_servers.client import get_mcp_client
from agent.prompts import build_system_prompt
from utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeClient:
    """
    Claude API client with traditional tools + real MCP servers
    
    This integrates:
    - Traditional tools (search_documents, read_file, etc.) from core/tool_executor.py
    - Real MCP servers (filesystem, memory, brave-search) via subprocess communication
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize Claude client
        
        Args:
            config_manager: ConfigManager instance for API key retrieval
        """
        # Get ConfigManager
        if config_manager is None:
            from security.config_manager import ConfigManager
            config_manager = ConfigManager()
        
        self.config_manager = config_manager
        
        # Get API key
        if not config_manager.has_api_key():
            raise ValueError(
                "No API key configured. Please add your Claude API key in Settings."
            )
        
        self.api_key = config_manager.get_api_key()
        if not self.api_key:
            raise ValueError("Failed to retrieve API key from ConfigManager")
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Get MCP configuration
        self.mcp_config = get_mcp_config()
        
        # Get config settings
        config = config_manager.get_config()
        self.agentic_mode_enabled = config.get('agentic_mode_enabled', False)
        
        # Initialize traditional tool executor
        self.tool_executor = ToolExecutor()
        
        # Initialize MCP client
        self.mcp_client = get_mcp_client() if self.agentic_mode_enabled else None
        
        # Start MCP servers if agentic mode is enabled
        if self.agentic_mode_enabled and self.mcp_client:
            self._start_mcp_servers()
        
        logger.info(f"ClaudeClient initialized:")
        logger.info(f"  Agentic mode: {'ENABLED' if self.agentic_mode_enabled else 'DISABLED'}")
        logger.info(f"  Output directory: {self.mcp_config.get_output_dir()}")
    
    def _start_mcp_servers(self):
        """Start enabled MCP server subprocesses"""
        enabled_servers = self.mcp_config.get_enabled_servers()
        
        for server_name in enabled_servers.keys():
            try:
                success = self.mcp_client.start_server(server_name)
                if success:
                    logger.info(f"  ✓ MCP server started: {server_name}")
                else:
                    logger.warning(f"  ✗ Failed to start MCP server: {server_name}")
            except Exception as e:
                logger.error(f"  ✗ Error starting {server_name}: {e}")
    
    def get_tools(self) -> List[Dict]:
        """
        Get all available tool definitions (traditional + MCP)
        
        Returns:
            List of tool definitions for Claude API
        """
        if not self.agentic_mode_enabled:
            return []
        
        tools = []
        
        # Get traditional tools
        traditional_tools = self.tool_executor.get_available_tools()
        tools.extend(traditional_tools)
        
        logger.info(f"Added {len(traditional_tools)} traditional tools")
        
        # Get MCP tools if available
        if self.mcp_client:
            for server_name in self.mcp_config.get_enabled_servers().keys():
                try:
                    mcp_tools = self.mcp_client.list_tools(server_name)
                    
                    # Convert MCP tool schema to Claude format
                    for mcp_tool in mcp_tools:
                        claude_tool = {
                            "name": f"mcp_{server_name}_{mcp_tool['name']}",
                            "description": f"[MCP {server_name}] {mcp_tool['description']}",
                            "input_schema": mcp_tool.get('inputSchema', {})
                        }
                        tools.append(claude_tool)
                    
                    logger.info(f"Added {len(mcp_tools)} MCP tools from {server_name}")
                
                except Exception as e:
                    logger.error(f"Failed to get MCP tools from {server_name}: {e}")
        
        logger.info(f"Total tools available: {len(tools)}")
        return tools
    
    def get_system_prompt(self, rag_context: Optional[str] = None) -> str:
        """
        Build system prompt with RAG context
        
        Args:
            rag_context: Retrieved context from ChromaDB (optional)
            
        Returns:
            Complete system prompt string
        """
        return build_system_prompt(
            mcp_config=self.mcp_config,
            rag_context=rag_context,
            tools_enabled=self.agentic_mode_enabled
        )
    
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool (traditional or MCP)
        
        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            
        Returns:
            Tool result dict
        """
        logger.info(f"Executing tool: {tool_name}")
        
        try:
            # Check if it's an MCP tool
            if tool_name.startswith("mcp_"):
                # Extract server name and actual tool name
                # Format: mcp_<server>_<tool>
                parts = tool_name.split("_", 2)
                if len(parts) >= 3:
                    server_name = parts[1]
                    actual_tool_name = parts[2]
                    
                    logger.info(f"  MCP tool: {server_name}.{actual_tool_name}")
                    
                    result = self.mcp_client.call_tool(
                        server_name,
                        actual_tool_name,
                        tool_input
                    )
                    
                    return result
                else:
                    return {"success": False, "error": f"Invalid MCP tool name: {tool_name}"}
            
            # Traditional tool
            else:
                logger.info(f"  Traditional tool: {tool_name}")
                
                result = self.tool_executor.execute_tool(tool_name, tool_input)
                
                # Convert ToolResult to dict
                if hasattr(result, 'to_dict'):
                    return result.to_dict()
                else:
                    return {"success": result.success, "result": result.result, "error": result.error}
        
        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def chat(
        self,
        message: str,
        conversation_history: List[Dict] = None,
        rag_context: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tool_turns: int = 10
    ) -> Dict:
        """
        Send message to Claude with RAG context and tool use support
        
        Args:
            message: User's message
            conversation_history: Previous messages in conversation
            rag_context: Retrieved context from RAG system
            model: Claude model to use
            max_tool_turns: Maximum tool use iterations
            
        Returns:
            Response dict with content and metadata
        """
        if conversation_history is None:
            conversation_history = []
        
        # Build messages with history
        messages = conversation_history + [
            {"role": "user", "content": message}
        ]
        
        # Get system prompt with RAG context
        system_prompt = self.get_system_prompt(rag_context)
        
        # Get tools
        tools = self.get_tools()
        
        if tools:
            logger.info(f"Chat with {len(tools)} tools available")
        else:
            logger.info("Chat without tools (agentic mode disabled)")
        
        # Tool use loop
        turn_count = 0
        total_input_tokens = 0
        total_output_tokens = 0
        
        while turn_count < max_tool_turns:
            turn_count += 1
            
            logger.info(f"API call - Turn {turn_count}/{max_tool_turns}")
            
            try:
                # Call Claude API
                if tools:
                    response = self.client.messages.create(
                        model=model,
                        max_tokens=4096,
                        system=system_prompt,
                        messages=messages,
                        tools=tools
                    )
                else:
                    response = self.client.messages.create(
                        model=model,
                        max_tokens=4096,
                        system=system_prompt,
                        messages=messages
                    )
                
                # Track tokens
                total_input_tokens += response.usage.input_tokens
                total_output_tokens += response.usage.output_tokens
                
                logger.info(f"  Stop reason: {response.stop_reason}")
                logger.info(f"  Tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
                
            except anthropic.APIError as e:
                logger.error(f"Anthropic API error: {e}")
                return {
                    "content": f"API Error: {str(e)}",
                    "model": model,
                    "tokens_used": {
                        "input": total_input_tokens,
                        "output": total_output_tokens
                    },
                    "stop_reason": "error",
                    "turns": turn_count
                }
            
            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Extract tool use blocks
                tool_uses = [block for block in response.content if block.type == "tool_use"]
                
                logger.info(f"  Claude requesting {len(tool_uses)} tool call(s)")
                
                # Add assistant message (with tool use) to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # Execute each tool and collect results
                tool_results = []
                
                for tool_use in tool_uses:
                    tool_name = tool_use.name
                    tool_input = tool_use.input
                    
                    logger.info(f"    Tool: {tool_name}")
                    
                    # Execute tool
                    result = self.execute_tool(tool_name, tool_input)
                    
                    # Format result content
                    if result.get("success"):
                        logger.info(f"    ✓ Tool succeeded")
                        content = result.get("result", result.get("message", "Success"))
                        if isinstance(content, dict):
                            import json
                            content = json.dumps(content, indent=2)
                    else:
                        logger.error(f"    ✗ Tool failed: {result.get('error')}")
                        content = f"Error: {result.get('error')}"
                    
                    # Add tool result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(content)
                    })
                
                # Add tool results to conversation
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
                # Continue loop to get Claude's final response
                continue
            
            else:
                # No more tools to use - extract final response
                final_text = ""
                
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text
                
                logger.info(f"Final response: {len(final_text)} chars, {turn_count} turns")
                
                return {
                    "content": final_text,
                    "model": model,
                    "tokens_used": {
                        "input": total_input_tokens,
                        "output": total_output_tokens
                    },
                    "stop_reason": response.stop_reason,
                    "turns": turn_count
                }
        
        # Max turns reached
        logger.warning(f"Max tool use turns ({max_tool_turns}) reached")
        
        return {
            "content": (
                "I apologize, but I've reached the maximum number of tool use iterations. "
                "Please try rephrasing your request or breaking it into smaller steps."
            ),
            "model": model,
            "tokens_used": {
                "input": total_input_tokens,
                "output": total_output_tokens
            },
            "stop_reason": "max_turns",
            "turns": turn_count
        }
    
    def get_output_directory(self):
        """Get the directory where agent generates files"""
        return self.mcp_config.get_output_dir()
    
    def get_mcp_status(self) -> Dict:
        """Get MCP configuration status for UI display"""
        status = {
            "enabled_servers": list(self.mcp_config.get_enabled_servers().keys()),
            "output_dir": str(self.mcp_config.get_output_dir()),
            "security_validated": self.mcp_config.validate_filesystem_access(),
            "config_file": str(self.mcp_config.config_file),
            "agentic_mode": self.agentic_mode_enabled,
        }
        
        # Add tool counts
        if self.agentic_mode_enabled:
            tools = self.get_tools()
            status["tools_available"] = len(tools)
            status["tool_names"] = [t["name"] for t in tools]
        else:
            status["tools_available"] = 0
            status["tool_names"] = []
        
        return status
    
    def __del__(self):
        """Cleanup MCP servers on deletion"""
        if hasattr(self, 'mcp_client') and self.mcp_client:
            try:
                self.mcp_client.stop_all_servers()
            except:
                pass


class SecurityError(Exception):
    """Raised when MCP security validation fails"""
    pass