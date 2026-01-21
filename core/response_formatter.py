"""
core/response_formatter.py
Formats Claude API responses for UI display
"""

import re
from typing import List, Dict, Any, Optional, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)


class FormattedResponse:
    """Represents a formatted response from Claude"""
    
    def __init__(
        self,
        text: str,
        citations: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize formatted response
        
        Args:
            text: Response text for display
            citations: List of citation dictionaries
            metadata: Optional metadata (usage stats, etc.)
        """
        self.text = text
        self.citations = citations
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'citations': self.citations,
            'metadata': self.metadata
        }
    
    def __repr__(self):
        return f"FormattedResponse(text_len={len(self.text)}, citations={len(self.citations)})"


class ResponseFormatter:
    """
    Formats Claude API responses for UI display
    """
    
    def __init__(self):
        """Initialize response formatter"""
        logger.debug("ResponseFormatter initialized")
    
    # ========================================================================
    # Public API - Main Formatting
    # ========================================================================
    
    def format_response(
        self,
        api_response: Dict[str, Any],
        retrieval_results: Optional[List[Any]] = None
    ) -> FormattedResponse:
        """
        Format Claude API response for UI
        
        Args:
            api_response: Raw response from Claude API
            retrieval_results: Optional retrieval results for citations
        
        Returns:
            FormattedResponse object
        """
        try:
            # Extract content from API response
            content = self._extract_content(api_response)
            
            # Extract citations from content
            text, extracted_citations = self._extract_citations(content)
            
            # Merge with retrieval results if available
            citations = self._merge_citations(extracted_citations, retrieval_results)
            
            # Extract metadata
            metadata = self._extract_metadata(api_response)
            
            logger.debug(
                f"Formatted response: {len(text)} chars, {len(citations)} citations"
            )
            
            return FormattedResponse(
                text=text,
                citations=citations,
                metadata=metadata
            )
        
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            # Return safe fallback
            return FormattedResponse(
                text="Error formatting response. Please try again.",
                citations=[],
                metadata={'error': str(e)}
            )
    
    def format_error(
        self,
        error: Exception,
        context: Optional[str] = None
    ) -> FormattedResponse:
        """
        Format error as a response
        
        Args:
            error: Exception that occurred
            context: Optional context about the error
        
        Returns:
            FormattedResponse with error message
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Create user-friendly error message
        text = self._create_error_message(error_type, error_message, context)
        
        return FormattedResponse(
            text=text,
            citations=[],
            metadata={
                'error': True,
                'error_type': error_type,
                'error_message': error_message
            }
        )
    
    # ========================================================================
    # Content Extraction
    # ========================================================================
    
    def _extract_content(self, api_response: Dict[str, Any]) -> str:
        """
        Extract text content from API response
        
        Args:
            api_response: Raw API response
        
        Returns:
            Extracted text content
        """
        try:
            # Handle different response structures
            if 'content' in api_response:
                content = api_response['content']
                
                # Handle list of content blocks
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                    return '\n\n'.join(text_parts)
                
                # Handle direct string
                elif isinstance(content, str):
                    return content
            
            # Fallback: try to get message content
            if 'message' in api_response:
                return self._extract_content(api_response['message'])
            
            logger.warning("Could not extract content from API response")
            return ""
        
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return ""
    
    def _extract_metadata(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from API response
        
        Args:
            api_response: Raw API response
        
        Returns:
            Metadata dictionary
        """
        metadata = {}
        
        try:
            # Extract usage stats
            if 'usage' in api_response:
                metadata['usage'] = api_response['usage']
            
            # Extract model info
            if 'model' in api_response:
                metadata['model'] = api_response['model']
            
            # Extract stop reason
            if 'stop_reason' in api_response:
                metadata['stop_reason'] = api_response['stop_reason']
            
            # Extract role
            if 'role' in api_response:
                metadata['role'] = api_response['role']
        
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
        
        return metadata
    
    # ========================================================================
    # Citation Extraction
    # ========================================================================
    
    def _extract_citations(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract citation references from text
        
        Args:
            text: Response text
        
        Returns:
            Tuple of (cleaned_text, citations)
        """
        citations = []
        
        # Pattern 1: Numbered citations [1], [2], etc.
        numbered_pattern = r'\[(\d+)\]'
        numbered_refs = re.findall(numbered_pattern, text)
        
        # Pattern 2: Source list at end (e.g., "Sources:\n[1] filename.pdf")
        source_pattern = r'(?:Sources?|References?):\s*\n((?:\[\d+\].*\n?)+)'
        source_match = re.search(source_pattern, text, re.MULTILINE | re.IGNORECASE)
        
        if source_match:
            # Extract source list
            source_list = source_match.group(1)
            
            # Parse individual sources
            source_items = re.findall(
                r'\[(\d+)\]\s*([^\n\-]+?)(?:\s*-\s*(.+?))?(?:\n|$)',
                source_list
            )
            
            for num, filename, filepath in source_items:
                citations.append({
                    'number': int(num),
                    'filename': filename.strip(),
                    'filepath': filepath.strip() if filepath else '',
                    'excerpt': ''
                })
            
            # Remove source list from text
            text = text[:source_match.start()].strip()
        
        return text, citations
    
    def _merge_citations(
        self,
        extracted_citations: List[Dict[str, Any]],
        retrieval_results: Optional[List[Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge extracted citations with retrieval results
        
        Args:
            extracted_citations: Citations extracted from response
            retrieval_results: Retrieval results from RAG
        
        Returns:
            Merged citation list
        """
        if not retrieval_results:
            return extracted_citations
        
        # Convert retrieval results to citation format
        citations = []
        
        for i, result in enumerate(retrieval_results):
            # Check if result has to_dict method (RetrievalResult)
            if hasattr(result, 'metadata'):
                metadata = result.metadata
                text = result.text if hasattr(result, 'text') else ''
                relevance = result.relevance_score if hasattr(result, 'relevance_score') else 0.0
            elif isinstance(result, dict):
                metadata = result.get('metadata', {})
                text = result.get('document', '')
                relevance = result.get('relevance_score', 0.0)
            else:
                continue
            
            citation = {
                'number': i + 1,
                'filename': metadata.get('filename', 'Unknown'),
                'filepath': metadata.get('filepath', ''),
                'excerpt': self._truncate_text(text, max_length=200),
                'chunk_index': metadata.get('chunk_index', 0),
                'relevance_score': relevance,
                'file_type': metadata.get('file_type', '')
            }
            
            citations.append(citation)
        
        # If extracted citations exist, try to match them
        if extracted_citations:
            # Match by number or filename
            for ext_cit in extracted_citations:
                num = ext_cit.get('number', 0)
                if 0 < num <= len(citations):
                    # Update filename/filepath if provided
                    if ext_cit.get('filename'):
                        citations[num - 1]['filename'] = ext_cit['filename']
                    if ext_cit.get('filepath'):
                        citations[num - 1]['filepath'] = ext_cit['filepath']
        
        return citations
    
    # ========================================================================
    # Text Processing
    # ========================================================================
    
    def _truncate_text(self, text: str, max_length: int = 200) -> str:
        """
        Truncate text to max length with ellipsis
        
        Args:
            text: Text to truncate
            max_length: Maximum length
        
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length].strip() + "..."
    
    def _clean_text(self, text: str) -> str:
        """
        Clean up text formatting
        
        Args:
            text: Text to clean
        
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Trim whitespace
        text = text.strip()
        
        return text
    
    # ========================================================================
    # Error Formatting
    # ========================================================================
    
    def _create_error_message(
        self,
        error_type: str,
        error_message: str,
        context: Optional[str]
    ) -> str:
        """
        Create user-friendly error message
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Optional context
        
        Returns:
            Formatted error message
        """
        # Map error types to user-friendly messages
        error_map = {
            'AuthenticationError': (
                "❌ API Key Error\n\n"
                "Your API key appears to be invalid or expired. "
                "Please check your API key in Settings."
            ),
            'RateLimitError': (
                "⏱️ Rate Limit Exceeded\n\n"
                "You've sent too many requests. Please wait a moment and try again."
            ),
            'InvalidRequestError': (
                "⚠️ Invalid Request\n\n"
                "There was an error with the request format. This is likely a bug. "
                "Please try again or contact support."
            ),
            'APIConnectionError': (
                "🌐 Connection Error\n\n"
                "Could not connect to the AI service. Please check your internet connection."
            ),
            'TimeoutError': (
                "⏰ Timeout\n\n"
                "The request took too long. Please try again with a simpler query."
            ),
        }
        
        # Get base message
        base_message = error_map.get(
            error_type,
            f"❌ Error\n\nAn unexpected error occurred: {error_message}"
        )
        
        # Add context if provided
        if context:
            base_message += f"\n\nContext: {context}"
        
        return base_message
    
    # ========================================================================
    # Formatting Utilities
    # ========================================================================
    
    def format_thinking_response(self, thinking_text: str) -> str:
        """
        Format extended thinking/reasoning text
        
        Args:
            thinking_text: Thinking/reasoning text
        
        Returns:
            Formatted text
        """
        return f"💭 **Thinking:**\n\n{thinking_text}"
    
    def format_tool_use_response(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_result: str
    ) -> str:
        """
        Format tool use information for display
        
        Args:
            tool_name: Name of tool used
            tool_input: Tool input parameters
            tool_result: Tool result
        
        Returns:
            Formatted text
        """
        return f"""🔧 **Tool Used:** {tool_name}

**Input:** {tool_input}

**Result:**
{tool_result}"""
    
    def strip_markdown(self, text: str) -> str:
        """
        Strip markdown formatting for plain text display
        
        Args:
            text: Text with markdown
        
        Returns:
            Plain text
        """
        # Remove bold/italic
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'`(.+?)`', r'\1', text)
        
        # Remove headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        return text


# ============================================================================
# Convenience Functions
# ============================================================================

def format_response(
    api_response: Dict[str, Any],
    retrieval_results: Optional[List[Any]] = None
) -> FormattedResponse:
    """
    Convenience function to format response
    
    Args:
        api_response: API response
        retrieval_results: Optional retrieval results
    
    Returns:
        FormattedResponse
    """
    formatter = ResponseFormatter()
    return formatter.format_response(api_response, retrieval_results)


def format_error(error: Exception, context: Optional[str] = None) -> FormattedResponse:
    """
    Convenience function to format error
    
    Args:
        error: Exception
        context: Optional context
    
    Returns:
        FormattedResponse with error
    """
    formatter = ResponseFormatter()
    return formatter.format_error(error, context)


# ============================================================================
# Testing/Debug
# ============================================================================

def test_response_formatter():
    """Test response formatter"""
    logger.info("Testing ResponseFormatter...")
    
    formatter = ResponseFormatter()
    
    # Test basic response
    api_response = {
        'content': [
            {
                'type': 'text',
                'text': 'This is a test response with a citation [1].\n\nSources:\n[1] test.pdf - /path/to/test.pdf'
            }
        ],
        'usage': {
            'input_tokens': 100,
            'output_tokens': 50
        }
    }
    
    result = formatter.format_response(api_response)
    logger.info(f"Formatted: {result}")
    logger.info(f"Text: {result.text}")
    logger.info(f"Citations: {result.citations}")
    
    # Test error formatting
    error = Exception("Test error")
    error_result = formatter.format_error(error, context="Testing")
    logger.info(f"Error formatted: {error_result.text}")


if __name__ == "__main__":
    test_response_formatter()