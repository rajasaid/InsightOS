"""
indexing/chunker.py
Text chunking with overlap for RAG indexing
"""

from typing import List, Dict, Any
import re

from utils.logger import get_logger
from config.settings import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP

logger = get_logger(__name__)


class TextChunk:
    """Represents a chunk of text with metadata"""
    
    def __init__(
        self,
        text: str,
        chunk_index: int,
        start_pos: int,
        end_pos: int,
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize text chunk
        
        Args:
            text: Chunk text content
            chunk_index: Index of this chunk in the document
            start_pos: Start position in original text
            end_pos: End position in original text
            metadata: Additional metadata
        """
        self.text = text
        self.chunk_index = chunk_index
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"TextChunk(index={self.chunk_index}, len={len(self.text)}, start={self.start_pos})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'chunk_index': self.chunk_index,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'metadata': self.metadata
        }


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    preserve_sentences: bool = True
) -> List[TextChunk]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        preserve_sentences: If True, try to break at sentence boundaries
    
    Returns:
        List of TextChunk objects
    
    Example:
        chunks = chunk_text("Long text...", chunk_size=1000, chunk_overlap=200)
    """
    if not text or not text.strip():
        logger.warning("Empty text provided to chunk_text")
        return []
    
    # Validate parameters
    if chunk_size <= 0:
        logger.error(f"Invalid chunk_size: {chunk_size}")
        chunk_size = DEFAULT_CHUNK_SIZE
    
    if chunk_overlap < 0:
        logger.error(f"Invalid chunk_overlap: {chunk_overlap}")
        chunk_overlap = 0
    
    if chunk_overlap >= chunk_size:
        logger.warning(f"chunk_overlap ({chunk_overlap}) >= chunk_size ({chunk_size}), reducing overlap")
        chunk_overlap = chunk_size // 2
    
    # If text is shorter than chunk size, return as single chunk
    if len(text) <= chunk_size:
        logger.debug(f"Text shorter than chunk_size, returning single chunk")
        return [TextChunk(
            text=text,
            chunk_index=0,
            start_pos=0,
            end_pos=len(text)
        )]
    
    # Choose chunking strategy
    if preserve_sentences:
        return _chunk_by_sentences(text, chunk_size, chunk_overlap)
    else:
        return _chunk_by_characters(text, chunk_size, chunk_overlap)


def _chunk_by_characters(
    text: str,
    chunk_size: int,
    chunk_overlap: int
) -> List[TextChunk]:
    """
    Simple character-based chunking with overlap
    
    Args:
        text: Text to chunk
        chunk_size: Chunk size in characters
        chunk_overlap: Overlap size in characters
    
    Returns:
        List of TextChunk objects
    """
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        # Calculate end position
        end = start + chunk_size
        
        # Get chunk text
        chunk_text = text[start:end]
        
        # Create chunk
        chunks.append(TextChunk(
            text=chunk_text,
            chunk_index=chunk_index,
            start_pos=start,
            end_pos=end
        ))
        
        # Move to next chunk (with overlap)
        start = end - chunk_overlap
        chunk_index += 1
        
        # Prevent infinite loop
        if start >= len(text):
            break
    
    logger.debug(f"Created {len(chunks)} chunks (character-based)")
    return chunks


def _chunk_by_sentences(
    text: str,
    chunk_size: int,
    chunk_overlap: int
) -> List[TextChunk]:
    """
    Sentence-aware chunking - tries to break at sentence boundaries
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap size in characters
    
    Returns:
        List of TextChunk objects
    """
    # Split text into sentences
    sentences = _split_into_sentences(text)
    
    if not sentences:
        logger.warning("No sentences found, falling back to character chunking")
        return _chunk_by_characters(text, chunk_size, chunk_overlap)
    
    chunks = []
    current_chunk = []
    current_length = 0
    chunk_index = 0
    start_pos = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        # If single sentence is longer than chunk_size, split it
        if sentence_length > chunk_size:
            # Save current chunk if it has content
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(TextChunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    start_pos=start_pos,
                    end_pos=start_pos + len(chunk_text)
                ))
                chunk_index += 1
                start_pos += len(chunk_text) - chunk_overlap
                current_chunk = []
                current_length = 0
            
            # Split long sentence by characters
            long_chunks = _chunk_by_characters(sentence, chunk_size, chunk_overlap)
            for long_chunk in long_chunks:
                # Adjust indices
                long_chunk.chunk_index = chunk_index
                long_chunk.start_pos = start_pos + long_chunk.start_pos
                long_chunk.end_pos = start_pos + long_chunk.end_pos
                chunks.append(long_chunk)
                chunk_index += 1
            
            start_pos = chunks[-1].end_pos - chunk_overlap
            continue
        
        # Check if adding this sentence would exceed chunk_size
        if current_length + sentence_length > chunk_size and current_chunk:
            # Save current chunk
            chunk_text = " ".join(current_chunk)
            chunks.append(TextChunk(
                text=chunk_text,
                chunk_index=chunk_index,
                start_pos=start_pos,
                end_pos=start_pos + len(chunk_text)
            ))
            
            # Start new chunk with overlap
            # Include last few sentences for overlap
            overlap_sentences = []
            overlap_length = 0
            
            for sent in reversed(current_chunk):
                if overlap_length + len(sent) <= chunk_overlap:
                    overlap_sentences.insert(0, sent)
                    overlap_length += len(sent) + 1  # +1 for space
                else:
                    break
            
            current_chunk = overlap_sentences
            current_length = sum(len(s) for s in current_chunk) + len(current_chunk) - 1
            chunk_index += 1
            start_pos = chunks[-1].end_pos - overlap_length
        
        # Add sentence to current chunk
        current_chunk.append(sentence)
        current_length += sentence_length + (1 if current_chunk else 0)  # +1 for space
    
    # Don't forget the last chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append(TextChunk(
            text=chunk_text,
            chunk_index=chunk_index,
            start_pos=start_pos,
            end_pos=start_pos + len(chunk_text)
        ))
    
    logger.debug(f"Created {len(chunks)} chunks (sentence-based)")
    return chunks


def _split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences
    
    Args:
        text: Text to split
    
    Returns:
        List of sentences
    """
    # Simple sentence splitting using regex
    # Matches periods, question marks, exclamation points followed by space and capital letter
    # Also handles common abbreviations
    
    # Replace common abbreviations to avoid false splits
    text = text.replace("Dr.", "Dr")
    text = text.replace("Mr.", "Mr")
    text = text.replace("Mrs.", "Mrs")
    text = text.replace("Ms.", "Ms")
    text = text.replace("Prof.", "Prof")
    text = text.replace("Sr.", "Sr")
    text = text.replace("Jr.", "Jr")
    text = text.replace("etc.", "etc")
    text = text.replace("e.g.", "eg")
    text = text.replace("i.e.", "ie")
    text = text.replace("vs.", "vs")
    
    # Split on sentence boundaries
    # Pattern: period/question/exclamation followed by whitespace and capital letter or end of string
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$'
    sentences = re.split(sentence_pattern, text)
    
    # Clean up sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def chunk_text_by_tokens(
    text: str,
    max_tokens: int = 512,
    overlap_tokens: int = 50,
    encoding_name: str = "cl100k_base"
) -> List[TextChunk]:
    """
    Split text into chunks by token count (requires tiktoken)
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Overlap in tokens
        encoding_name: Tokenizer encoding to use
    
    Returns:
        List of TextChunk objects
    
    Note:
        This is more accurate for LLM context windows but requires tiktoken library
    """
    try:
        import tiktoken
        
        # Get encoding
        encoding = tiktoken.get_encoding(encoding_name)
        
        # Tokenize entire text
        tokens = encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            logger.debug("Text fits in single chunk (token-based)")
            return [TextChunk(
                text=text,
                chunk_index=0,
                start_pos=0,
                end_pos=len(text)
            )]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(tokens):
            # Get chunk tokens
            end = start + max_tokens
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = encoding.decode(chunk_tokens)
            
            # Create chunk
            chunks.append(TextChunk(
                text=chunk_text,
                chunk_index=chunk_index,
                start_pos=start,
                end_pos=end
            ))
            
            # Move to next chunk with overlap
            start = end - overlap_tokens
            chunk_index += 1
        
        logger.debug(f"Created {len(chunks)} chunks (token-based)")
        return chunks
    
    except ImportError:
        logger.warning("tiktoken not installed, falling back to character-based chunking")
        # Convert token counts to approximate character counts
        # Rough estimate: 1 token ≈ 4 characters
        char_chunk_size = max_tokens * 4
        char_overlap = overlap_tokens * 4
        return chunk_text(text, char_chunk_size, char_overlap)
    
    except Exception as e:
        logger.error(f"Error in token-based chunking: {e}")
        # Fallback
        char_chunk_size = max_tokens * 4
        char_overlap = overlap_tokens * 4
        return chunk_text(text, char_chunk_size, char_overlap)


def get_chunk_statistics(chunks: List[TextChunk]) -> Dict[str, Any]:
    """
    Get statistics about chunks
    
    Args:
        chunks: List of chunks
    
    Returns:
        Dictionary with statistics
    """
    if not chunks:
        return {
            'num_chunks': 0,
            'total_chars': 0,
            'avg_chunk_size': 0,
            'min_chunk_size': 0,
            'max_chunk_size': 0
        }
    
    chunk_sizes = [len(chunk.text) for chunk in chunks]
    
    return {
        'num_chunks': len(chunks),
        'total_chars': sum(chunk_sizes),
        'avg_chunk_size': sum(chunk_sizes) / len(chunks),
        'min_chunk_size': min(chunk_sizes),
        'max_chunk_size': max(chunk_sizes)
    }


# ============================================================================
# Testing/Debug
# ============================================================================

def test_chunking():
    """Test chunking with sample text"""
    logger.info("Testing text chunking...")
    
    # Sample text
    sample_text = """
    This is the first sentence. This is the second sentence. This is the third sentence.
    This is the fourth sentence with more text to make it longer. This is the fifth sentence.
    This is the sixth sentence. This is the seventh sentence that is also quite long for testing.
    This is the eighth sentence. This is the ninth sentence. This is the tenth sentence.
    """ * 10  # Repeat to make it longer
    
    # Test character-based chunking
    logger.info("\n=== Character-based chunking ===")
    chunks = chunk_text(sample_text, chunk_size=500, chunk_overlap=100, preserve_sentences=False)
    stats = get_chunk_statistics(chunks)
    logger.info(f"Statistics: {stats}")
    
    # Test sentence-based chunking
    logger.info("\n=== Sentence-based chunking ===")
    chunks = chunk_text(sample_text, chunk_size=500, chunk_overlap=100, preserve_sentences=True)
    stats = get_chunk_statistics(chunks)
    logger.info(f"Statistics: {stats}")
    
    # Show first 3 chunks
    for i, chunk in enumerate(chunks[:3]):
        logger.info(f"\nChunk {i}:")
        logger.info(f"  Text: {chunk.text[:100]}...")
        logger.info(f"  Length: {len(chunk.text)}")
        logger.info(f"  Position: {chunk.start_pos}-{chunk.end_pos}")


if __name__ == "__main__":
    test_chunking()