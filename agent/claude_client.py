"""
agent/claude_client.py
Claude API Client with Traditional Tools + Real MCP Support
"""

import anthropic
from typing import List, Dict, Optional, Any

from core.tool_executor import ToolExecutor
from mcp_servers import get_mcp_config
from mcp_servers.client import get_mcp_client
from security.config_manager import get_config_manager
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
            config_manager = get_config_manager()
        
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
        
        started_count = 0
        for server_name in enabled_servers.keys():
            try:
                success = self.mcp_client.start_server(server_name)
                if success:
                    logger.info(f"  ✓ MCP server started: {server_name}")
                    started_count += 1
                else:
                    # Only warn for optional servers (memory, brave-search)
                    if server_name in ["memory", "brave-search"]:
                        logger.info(f"  ○ MCP server {server_name} not available (optional)")
                    else:
                        # Filesystem is critical
                        logger.warning(f"  ✗ Failed to start MCP server: {server_name}")
            except Exception as e:
                logger.error(f"  ✗ Error starting {server_name}: {e}")
        
        if started_count == 0:
            logger.warning("No MCP servers started successfully")
        else:
            logger.info(f"Started {started_count}/{len(enabled_servers)} MCP servers")
    
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
        Build system prompt with RAG context (using core/prompt_templates.py)
        
        Args:
            rag_context: Retrieved context from ChromaDB (optional)
            
        Returns:
            Complete system prompt string
        """
        from core.prompt_templates import get_system_prompt as get_base_prompt
        
        # Get base system prompt (prevents hallucination)
        system_prompt = get_base_prompt(use_tools=self.agentic_mode_enabled)
        
        # Add RAG context if provided
        if rag_context:
            system_prompt += f"""

====================
RETRIEVED CONTEXT (ALREADY SEARCHED - DO NOT SEARCH AGAIN)
====================

I have already searched your indexed documents and retrieved the most relevant information.
Here is what I found:

<context>
{rag_context}
</context>

====================
CRITICAL INSTRUCTIONS
====================

1. The context above is the RESULT of the search - it has already been performed
2. Do NOT output <search> tags or mention that you will search
3. Do NOT say "I'll search" or "Let me search" - the search is already done
4. Base your answer ONLY on the context above
5. If the context doesn't contain the answer, say: "I don't have that information in your indexed documents"
6. Do NOT use general knowledge or make assumptions
7. Always cite specific documents when providing information
8. If you're unsure, state what information is missing from the context

**CRITICAL - FILE WRITING:**
When using write_file tool:
- ONLY use RELATIVE paths like "summaries/filename.txt"
- DO NOT use absolute paths like "/Users/.../filename.txt"
- The file will automatically be saved to the Generated directory
- Example: Use "summaries/chosen_file_name.csv" NOT "/Users/.../chosen_file_name.csv"

The search has ALREADY been performed. Just answer based on the context provided."""
        
        return system_prompt
    
    def _clean_response_text(self, text: str) -> str:
        """
        Clean up response text - remove excessive whitespace
        
        Args:
            text: Raw response text
            
        Returns:
            Cleaned text
        """
        import re
        
        # Remove excessive blank lines (max 1 blank line between content)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove lines with only whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)
        
        # Clean up bullet points with too much spacing
        text = re.sub(r'\n\n•', '\n•', text)
        text = re.sub(r'\n\n-', '\n-', text)
        text = re.sub(r'\n\n\*', '\n*', text)
        
        # Remove trailing whitespace from each line
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        text = '\n'.join(lines)
        
        # Trim overall whitespace
        text = text.strip()
        
        return text
    
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
        #logger.info(f"RAW tool_input: {tool_input}")
        
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
                        tools=tools,
                        temperature=0.1
                    )
                else:
                    response = self.client.messages.create(
                        model=model,
                        max_tokens=4096,
                        system=system_prompt,
                        messages=messages,
                        temperature=0.1
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
                    # NEW: Check for MCP success differently
                    is_success = False
                    content = ""

                    if isinstance(result, dict):
                        # Check various success indicators
                        if result.get("success") is True:
                            is_success = True
                            content = result.get("result", result.get("message", "Success"))
                        elif "content" in result:
                            # MCP server response format
                            mcp_content = result.get("content", [])
                            if isinstance(mcp_content, list) and len(mcp_content) > 0:
                                first_item = mcp_content[0]
                                if isinstance(first_item, dict):
                                    content = first_item.get("text", "")
                                    # Check if it's an error
                                    is_success = not result.get("isError", False)
                                else:
                                    content = str(mcp_content)
                                    is_success = True
                        else:
                            content = str(result)
                            is_success = True

                    if is_success:
                        logger.info(f"    ✓ Tool succeeded")
                    else:
                        logger.error(f"    ✗ Tool failed: {content}")
                        content = f"Error: {content}"
                    
                    # # Format result content
                    # if result.get("success"):
                    #     logger.info(f"    ✓ Tool succeeded")
                    #     content = result.get("result", result.get("message", "Success"))
                    #     if isinstance(content, dict):
                    #         import json
                    #         content = json.dumps(content, indent=2)
                    # else:
                    #     logger.error(f"    ✗ Tool failed: {result.get('error')}")
                    #     content = f"Error: {result.get('error')}"
                    
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
                
                # Clean up the response text (remove excessive whitespace)
                final_text = self._clean_response_text(final_text)
                
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
        
        error_message = (
            "I apologize, but I've reached the maximum number of tool use iterations. "
            "Please try rephrasing your request or breaking it into smaller steps."
        )
        
        return {
            "content": error_message,
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