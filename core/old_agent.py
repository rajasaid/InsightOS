"""
core/agent.py
Main RAG agent - orchestrates retrieval, tool execution, and Claude API calls
"""

from typing import List, Dict, Any, Optional
import anthropic

from core.rag_retriever import RAGRetriever
from core.conversation_memory import ConversationMemory
from core.tool_executor import ToolExecutor
from core.response_formatter import ResponseFormatter
from core.prompt_templates import (
    get_system_prompt,
    format_rag_context,
    format_rag_context_with_conversation,
    format_no_results_message
)
from security.config_manager import ConfigManager
from utils.logger import get_logger
from config.settings import CLAUDE_MODEL, CLAUDE_MAX_TOKENS, CLAUDE_TEMPERATURE

logger = get_logger(__name__)


class Agent:
    """
    Main RAG agent - orchestrates the entire query pipeline
    """
    
    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        retriever: Optional[RAGRetriever] = None,
        tool_executor: Optional[ToolExecutor] = None,
        use_tools: bool = True,
        use_conversation_memory: bool = True
    ):
        """
        Initialize agent
        
        Args:
            config_manager: Configuration manager
            retriever: RAG retriever
            tool_executor: Tool executor
            use_tools: Whether to enable tool use
            use_conversation_memory: Whether to maintain conversation history
        """
        self.config_manager = config_manager or ConfigManager()
        self.retriever = retriever or RAGRetriever()
        self.tool_executor = tool_executor or ToolExecutor()
        self.response_formatter = ResponseFormatter()
        
        # Conversation memory
        self.use_conversation_memory = use_conversation_memory
        self.conversation_memory = ConversationMemory() if use_conversation_memory else None
        
        # Tool use setting
        self.use_tools = use_tools
        
        # Claude client (initialized on first use)
        self._client: Optional[anthropic.Anthropic] = None
        
        logger.info(
            f"Agent initialized (tools={use_tools}, "
            f"memory={use_conversation_memory})"
        )
    
    # ========================================================================
    # Public API - Query Processing
    # ========================================================================
    
    def query(
        self,
        user_query: str,
        top_k: Optional[int] = None,
        include_conversation_history: bool = True
    ) -> Dict[str, Any]:
        """
        Process user query with RAG pipeline
        
        Args:
            user_query: User's question
            top_k: Number of chunks to retrieve (overrides default)
            include_conversation_history: Include conversation context
        
        Returns:
            Dictionary with response, citations, and metadata
        """
        logger.info(f"Processing query: {user_query[:100]}...")
        
        try:
            # Validate API key
            if not self._ensure_api_key():
                return {
                    'success': False,
                    'error': 'No API key configured. Please add your Claude API key in Settings.',
                    'text': 'No API key configured. Please add your Claude API key in Settings.',
                    'citations': []
                }
            
            # Add user message to memory
            if self.conversation_memory:
                self.conversation_memory.add_user_message(user_query)
            
            # Retrieve relevant context
            logger.debug("Retrieving context from documents...")
            retrieval_results = self.retriever.retrieve(user_query, top_k=top_k)
            
            # Check if we have results
            if not retrieval_results:
                logger.warning("No retrieval results found")
                return self._handle_no_results(user_query)
            
            # Format context
            context = self.retriever.format_context(retrieval_results)
            
            # Build prompt
            if include_conversation_history and self.conversation_memory:
                history = self.conversation_memory.get_messages_for_api(limit=6)
                prompt = format_rag_context_with_conversation(
                    query=user_query,
                    context=context,
                    num_chunks=len(retrieval_results),
                    conversation_history=history
                )
            else:
                prompt = format_rag_context(
                    query=user_query,
                    context=context,
                    num_chunks=len(retrieval_results)
                )
            
            # Call Claude API
            logger.debug("Calling Claude API...")
            api_response = self._call_claude(prompt)
            
            # Format response
            formatted_response = self.response_formatter.format_response(
                api_response,
                retrieval_results
            )
            
            # Add assistant message to memory
            if self.conversation_memory:
                self.conversation_memory.add_assistant_message(
                    formatted_response.text,
                    formatted_response.citations
                )
            
            # Return result
            return {
                'success': True,
                'text': formatted_response.text,
                'citations': formatted_response.citations,
                'metadata': {
                    **formatted_response.metadata,
                    'num_chunks_retrieved': len(retrieval_results),
                    'retrieval_stats': self.retriever.get_retrieval_stats(retrieval_results)
                }
            }
        
        except anthropic.AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            error_response = self.response_formatter.format_error(e, "Invalid API key")
            return {
                'success': False,
                'error': 'authentication',
                'text': error_response.text,
                'citations': []
            }
        
        except anthropic.RateLimitError as e:
            logger.error(f"Rate limit error: {e}")
            error_response = self.response_formatter.format_error(e, "Rate limit exceeded")
            return {
                'success': False,
                'error': 'rate_limit',
                'text': error_response.text,
                'citations': []
            }
        
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            error_response = self.response_formatter.format_error(e)
            return {
                'success': False,
                'error': str(e),
                'text': error_response.text,
                'citations': []
            }
    
    def query_with_tools(
        self,
        user_query: str,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Process query with tool use (agentic mode)
        
        Args:
            user_query: User's question
            max_iterations: Maximum tool-use iterations
        
        Returns:
            Dictionary with response, citations, and metadata
        """
        logger.info(f"Processing query with tools: {user_query[:100]}...")
        
        if not self.use_tools:
            logger.warning("Tool use disabled, falling back to regular query")
            return self.query(user_query)
        
        try:
            # Validate API key
            if not self._ensure_api_key():
                return {
                    'success': False,
                    'error': 'No API key configured',
                    'text': 'No API key configured. Please add your Claude API key in Settings.',
                    'citations': []
                }
            
            # Add user message to memory
            if self.conversation_memory:
                self.conversation_memory.add_user_message(user_query)
            
            # Build messages
            messages = [{"role": "user", "content": user_query}]
            
            # Get available tools
            tools = self.tool_executor.get_available_tools()
            
            # Agentic loop
            iteration = 0
            while iteration < max_iterations:
                iteration += 1
                logger.debug(f"Tool use iteration {iteration}/{max_iterations}")
                
                # Call Claude with tools
                api_response = self._call_claude_with_tools(messages, tools)
                
                # Check stop reason
                stop_reason = api_response.get('stop_reason')
                
                if stop_reason == 'end_turn':
                    # Claude is done
                    logger.info("Claude finished (end_turn)")
                    break
                
                elif stop_reason == 'tool_use':
                    # Extract tool uses
                    tool_uses = self._extract_tool_uses(api_response)
                    
                    if not tool_uses:
                        logger.warning("tool_use stop reason but no tools found")
                        break
                    
                    # Execute tools
                    tool_results = []
                    for tool_use in tool_uses:
                        result = self.tool_executor.execute_tool(
                            tool_use['name'],
                            tool_use['input']
                        )
                        tool_results.append({
                            'tool_use_id': tool_use['id'],
                            'result': result
                        })
                    
                    # Add assistant message with tool uses
                    messages.append({
                        "role": "assistant",
                        "content": api_response['content']
                    })
                    
                    # Add tool results
                    tool_result_content = []
                    for tr in tool_results:
                        tool_result_content.append({
                            "type": "tool_result",
                            "tool_use_id": tr['tool_use_id'],
                            "content": self.tool_executor.format_tool_result_for_claude(tr['result'])
                        })
                    
                    messages.append({
                        "role": "user",
                        "content": tool_result_content
                    })
                
                else:
                    # Unexpected stop reason
                    logger.warning(f"Unexpected stop reason: {stop_reason}")
                    break
            
            # Format final response
            formatted_response = self.response_formatter.format_response(api_response)
            
            # Add to memory
            if self.conversation_memory:
                self.conversation_memory.add_assistant_message(
                    formatted_response.text,
                    formatted_response.citations
                )
            
            return {
                'success': True,
                'text': formatted_response.text,
                'citations': formatted_response.citations,
                'metadata': {
                    **formatted_response.metadata,
                    'iterations': iteration,
                    'tools_used': iteration > 1
                }
            }
        
        except Exception as e:
            logger.error(f"Error in query_with_tools: {e}", exc_info=True)
            error_response = self.response_formatter.format_error(e)
            return {
                'success': False,
                'error': str(e),
                'text': error_response.text,
                'citations': []
            }
    
    # ========================================================================
    # Conversation Management
    # ========================================================================
    
    def clear_conversation(self):
        """Clear conversation history"""
        if self.conversation_memory:
            self.conversation_memory.clear()
            logger.info("Conversation cleared")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get conversation history
        
        Returns:
            List of messages with metadata
        """
        if self.conversation_memory:
            return self.conversation_memory.get_messages(include_metadata=True)
        return []
    
    def export_conversation(self) -> Dict[str, Any]:
        """
        Export conversation for saving
        
        Returns:
            Conversation data
        """
        if self.conversation_memory:
            return self.conversation_memory.export_conversation()
        return {}
    
    # ========================================================================
    # Configuration
    # ========================================================================
    
    def update_settings(self, settings: Dict[str, Any]):
        """
        Update agent settings
        
        Args:
            settings: Settings dictionary (top_k, chunk_size, etc.)
        """
        if 'top_k' in settings:
            self.retriever.set_top_k(settings['top_k'])
            logger.info(f"Updated top_k to: {settings['top_k']}")
        
        if 'similarity_threshold' in settings:
            self.retriever.set_similarity_threshold(settings['similarity_threshold'])
            logger.info(f"Updated similarity_threshold to: {settings['similarity_threshold']}")
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _ensure_api_key(self) -> bool:
        """
        Ensure API key is available
        
        Returns:
            True if API key exists, False otherwise
        """
        if self._client is not None:
            return True
        
        api_key = self.config_manager.get_api_key()
        
        if not api_key:
            logger.error("No API key configured")
            return False
        
        try:
            self._client = anthropic.Anthropic(api_key=api_key)
            logger.info("Claude client initialized")
            
            # Clear API key from memory
            del api_key
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            return False
    
    def _call_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call Claude API
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt override
        
        Returns:
            API response
        """
        if not self._client:
            raise RuntimeError("Claude client not initialized")
        
        # Get system prompt
        if system_prompt is None:
            system_prompt = get_system_prompt(use_tools=False)
        
        # Build messages
        messages = [{"role": "user", "content": prompt}]
        
        # Add conversation history if available
        if self.conversation_memory and not self.conversation_memory.is_empty():
            history = self.conversation_memory.get_context_window(max_tokens=4000)
            # Insert history before current message
            messages = history[:-1] + messages  # Exclude last message (already in prompt)
        
        # Call API
        response = self._client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            temperature=CLAUDE_TEMPERATURE,
            system=system_prompt,
            messages=messages
        )
        
        # Convert to dict
        return response.model_dump()
    
    def _call_claude_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Call Claude API with tools
        
        Args:
            messages: Message history
            tools: Available tools
        
        Returns:
            API response
        """
        if not self._client:
            raise RuntimeError("Claude client not initialized")
        
        # Get system prompt
        system_prompt = get_system_prompt(use_tools=True)
        
        # Call API with tools
        response = self._client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            temperature=CLAUDE_TEMPERATURE,
            system=system_prompt,
            messages=messages,
            tools=tools
        )
        
        return response.model_dump()
    
    def _extract_tool_uses(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tool uses from API response
        
        Args:
            api_response: API response
        
        Returns:
            List of tool use dicts
        """
        tool_uses = []
        
        content = api_response.get('content', [])
        
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                tool_uses.append({
                    'id': block.get('id'),
                    'name': block.get('name'),
                    'input': block.get('input', {})
                })
        
        return tool_uses
    
    @property
    def tools_enabled(self) -> bool:
        """Check if tools are enabled"""
        return self.use_tools

    def _handle_no_results(self, query: str) -> Dict[str, Any]:
        """
        Handle case when no retrieval results found
        
        Args:
            query: User query
        
        Returns:
            Response dictionary
        """
        # Get number of indexed files
        stats = self.retriever.chromadb_client.get_stats()
        num_files = stats.get('unique_files_sampled', 0)
        
        # Format message
        message = format_no_results_message(query, num_files)
        
        return {
            'success': True,
            'text': message,
            'citations': [],
            'metadata': {
                'no_results': True,
                'num_indexed_files': num_files
            }
        }


# ============================================================================
# Testing/Debug
# ============================================================================

def test_agent():
    """Test agent"""
    logger.info("Testing Agent...")
    
    agent = Agent(use_tools=False)
    
    # Test query
    result = agent.query("What is machine learning?")
    
    logger.info(f"Result: {result['success']}")
    logger.info(f"Text: {result['text'][:200]}...")
    logger.info(f"Citations: {len(result.get('citations', []))}")


if __name__ == "__main__":
    test_agent()
