"""
core/conversation_memory.py
Manages conversation history for context continuity
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque

from utils.logger import get_logger
from config.settings import MAX_MESSAGE_HISTORY

logger = get_logger(__name__)


class Message:
    """Represents a single message in the conversation"""
    
    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize message
        
        Args:
            role: Message role ("user" or "assistant")
            content: Message content
            timestamp: Message timestamp (auto-generated if None)
            metadata: Optional metadata (citations, etc.)
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "role": self.role,
            "content": self.content
        }
    
    def to_dict_with_metadata(self) -> Dict[str, Any]:
        """Convert to dictionary with full metadata"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    def __repr__(self):
        return f"Message(role={self.role}, content={self.content[:50]}...)"


class ConversationMemory:
    """
    Manages conversation history with context window management
    """
    
    def __init__(self, max_messages: int = MAX_MESSAGE_HISTORY):
        """
        Initialize conversation memory
        
        Args:
            max_messages: Maximum number of messages to keep in memory
        """
        self.max_messages = max_messages
        self.messages: deque[Message] = deque(maxlen=max_messages)
        self.conversation_id = self._generate_conversation_id()
        self.created_at = datetime.now()
        
        logger.info(
            f"ConversationMemory initialized "
            f"(max_messages={max_messages}, id={self.conversation_id})"
        )
    
    # ========================================================================
    # Public API - Message Management
    # ========================================================================
    
    def add_user_message(self, content: str) -> Message:
        """
        Add user message to conversation
        
        Args:
            content: Message content
        
        Returns:
            Created Message object
        """
        message = Message(role="user", content=content)
        self.messages.append(message)
        
        logger.debug(f"Added user message: {content[:100]}...")
        return message
    
    def add_assistant_message(
        self,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        """
        Add assistant message to conversation
        
        Args:
            content: Message content
            citations: Optional list of citations
        
        Returns:
            Created Message object
        """
        metadata = {}
        if citations:
            metadata['citations'] = citations
        
        message = Message(role="assistant", content=content, metadata=metadata)
        self.messages.append(message)
        
        logger.debug(f"Added assistant message: {content[:100]}...")
        return message
    
    def get_messages(
        self,
        limit: Optional[int] = None,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get conversation messages
        
        Args:
            limit: Maximum number of recent messages (None = all)
            include_metadata: If True, include timestamps and metadata
        
        Returns:
            List of message dictionaries
        """
        messages = list(self.messages)
        
        # Limit to recent messages
        if limit is not None and limit > 0:
            messages = messages[-limit:]
        
        # Convert to dict
        if include_metadata:
            return [msg.to_dict_with_metadata() for msg in messages]
        else:
            return [msg.to_dict() for msg in messages]
    
    def get_messages_for_api(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get messages formatted for Claude API
        
        Args:
            limit: Maximum number of recent messages
        
        Returns:
            List of message dicts with role and content only
        """
        return self.get_messages(limit=limit, include_metadata=False)
    
    def clear(self):
        """Clear all messages and start fresh conversation"""
        self.messages.clear()
        self.conversation_id = self._generate_conversation_id()
        self.created_at = datetime.now()
        
        logger.info("Conversation cleared")
    
    # ========================================================================
    # Context Window Management
    # ========================================================================
    
    def get_context_window(
        self,
        max_tokens: int = 4000,
        chars_per_token: int = 4
    ) -> List[Dict[str, str]]:
        """
        Get messages that fit within context window
        
        Args:
            max_tokens: Maximum tokens for context
            chars_per_token: Approximate characters per token
        
        Returns:
            List of messages that fit in context window
        """
        max_chars = max_tokens * chars_per_token
        
        # Start from most recent and work backwards
        messages = []
        current_chars = 0
        
        for message in reversed(self.messages):
            message_chars = len(message.content)
            
            if current_chars + message_chars > max_chars:
                logger.warning(
                    f"Context window limit reached, using {len(messages)} of "
                    f"{len(self.messages)} messages"
                )
                break
            
            messages.insert(0, message.to_dict())  # Insert at beginning to maintain order
            current_chars += message_chars
        
        logger.debug(
            f"Context window: {len(messages)} messages, ~{current_chars} chars"
        )
        
        return messages
    
    def estimate_token_count(self) -> int:
        """
        Estimate total token count of conversation
        
        Returns:
            Estimated token count
        """
        total_chars = sum(len(msg.content) for msg in self.messages)
        estimated_tokens = total_chars // 4  # Rough estimate: 4 chars per token
        
        return estimated_tokens
    
    # ========================================================================
    # Conversation Info
    # ========================================================================
    
    def get_message_count(self) -> int:
        """Get total number of messages"""
        return len(self.messages)
    
    def is_empty(self) -> bool:
        """Check if conversation is empty"""
        return len(self.messages) == 0
    
    def get_last_message(self) -> Optional[Message]:
        """Get most recent message"""
        if self.messages:
            return self.messages[-1]
        return None
    
    def get_conversation_info(self) -> Dict[str, Any]:
        """
        Get conversation metadata
        
        Returns:
            Dictionary with conversation info
        """
        return {
            'conversation_id': self.conversation_id,
            'created_at': self.created_at.isoformat(),
            'message_count': len(self.messages),
            'estimated_tokens': self.estimate_token_count(),
            'is_empty': self.is_empty()
        }
    
    # ========================================================================
    # Search & Filter
    # ========================================================================
    
    def search_messages(self, keyword: str) -> List[Message]:
        """
        Search messages by keyword
        
        Args:
            keyword: Keyword to search for
        
        Returns:
            List of matching messages
        """
        keyword_lower = keyword.lower()
        matches = [
            msg for msg in self.messages
            if keyword_lower in msg.content.lower()
        ]
        
        logger.debug(f"Found {len(matches)} messages matching '{keyword}'")
        return matches
    
    def get_messages_by_role(self, role: str) -> List[Message]:
        """
        Get messages by role
        
        Args:
            role: "user" or "assistant"
        
        Returns:
            List of messages with specified role
        """
        return [msg for msg in self.messages if msg.role == role]
    
    # ========================================================================
    # Export & Import
    # ========================================================================
    
    def export_conversation(self) -> Dict[str, Any]:
        """
        Export entire conversation
        
        Returns:
            Dictionary with full conversation data
        """
        return {
            'conversation_id': self.conversation_id,
            'created_at': self.created_at.isoformat(),
            'message_count': len(self.messages),
            'messages': [msg.to_dict_with_metadata() for msg in self.messages]
        }
    
    def import_conversation(self, data: Dict[str, Any]):
        """
        Import conversation from exported data
        
        Args:
            data: Exported conversation data
        """
        try:
            self.messages.clear()
            self.conversation_id = data.get('conversation_id', self._generate_conversation_id())
            
            created_at_str = data.get('created_at')
            if created_at_str:
                self.created_at = datetime.fromisoformat(created_at_str)
            
            for msg_data in data.get('messages', []):
                message = Message(
                    role=msg_data['role'],
                    content=msg_data['content'],
                    timestamp=datetime.fromisoformat(msg_data.get('timestamp', datetime.now().isoformat())),
                    metadata=msg_data.get('metadata', {})
                )
                self.messages.append(message)
            
            logger.info(f"Imported conversation with {len(self.messages)} messages")
        
        except Exception as e:
            logger.error(f"Failed to import conversation: {e}")
            raise
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID"""
        import uuid
        return f"conv_{uuid.uuid4().hex[:12]}"
    
    # ========================================================================
    # String Representation
    # ========================================================================
    
    def __repr__(self):
        return (
            f"ConversationMemory(id={self.conversation_id}, "
            f"messages={len(self.messages)}, "
            f"tokens≈{self.estimate_token_count()})"
        )
    
    def __len__(self):
        return len(self.messages)


# ============================================================================
# Testing/Debug
# ============================================================================

def test_conversation_memory():
    """Test conversation memory"""
    logger.info("Testing ConversationMemory...")
    
    # Create memory
    memory = ConversationMemory(max_messages=10)
    
    # Add messages
    memory.add_user_message("Hello, how are you?")
    memory.add_assistant_message("I'm doing well, thank you!")
    memory.add_user_message("What is machine learning?")
    memory.add_assistant_message(
        "Machine learning is a subset of AI...",
        citations=[{'filename': 'ml_intro.pdf', 'excerpt': 'ML is...'}]
    )
    
    # Get messages
    messages = memory.get_messages()
    logger.info(f"Messages: {len(messages)}")
    
    # Get info
    info = memory.get_conversation_info()
    logger.info(f"Conversation info: {info}")
    
    # Test context window
    context = memory.get_context_window(max_tokens=1000)
    logger.info(f"Context window: {len(context)} messages")
    
    # Test export
    exported = memory.export_conversation()
    logger.info(f"Exported conversation: {exported['conversation_id']}")
    
    # Test clear
    memory.clear()
    logger.info(f"After clear: {len(memory)} messages")


if __name__ == "__main__":
    test_conversation_memory()