"""
core/rag_retriever.py
RAG retrieval logic - queries ChromaDB and formats context for Claude
Updated to integrate with agent layer and MCP system
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from indexing.chromadb_client import ChromaDBClient
from utils.logger import get_logger
from config.settings import DEFAULT_TOP_K, DEFAULT_SIMILARITY_THRESHOLD

logger = get_logger(__name__)


class RetrievalResult:
    """Represents a single retrieved chunk with metadata"""
    
    def __init__(
        self,
        text: str,
        metadata: Dict[str, Any],
        distance: float,
        relevance_score: float
    ):
        """
        Initialize retrieval result
        
        Args:
            text: Chunk text content
            metadata: Chunk metadata (filepath, filename, etc.)
            distance: Distance from query (lower = more similar)
            relevance_score: Normalized relevance score (0-1, higher = more relevant)
        """
        self.text = text
        self.metadata = metadata
        self.distance = distance
        self.relevance_score = relevance_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'text': self.text,
            'metadata': self.metadata,
            'distance': self.distance,
            'relevance_score': self.relevance_score
        }
    
    def __repr__(self):
        return f"RetrievalResult(file={self.metadata.get('filename')}, score={self.relevance_score:.3f})"


class RAGRetriever:
    """
    RAG retrieval component - queries vector store and formats context
    Integrates with agent layer for Claude API calls
    """
    
    def __init__(
        self,
        chromadb_client: Optional[ChromaDBClient] = None,
        top_k: int = DEFAULT_TOP_K,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    ):
        """
        Initialize RAG retriever
        
        Args:
            chromadb_client: ChromaDB client instance
            top_k: Number of chunks to retrieve
            similarity_threshold: Minimum similarity threshold (0.0-1.0)
        """
        self.chromadb_client = chromadb_client or ChromaDBClient()
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        
        logger.info(
            f"RAGRetriever initialized (top_k={top_k}, "
            f"threshold={similarity_threshold})"
        )
    
    # ========================================================================
    # Public API - Retrieval
    # ========================================================================
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: User query text
            top_k: Number of results (overrides default)
            filter_metadata: Optional metadata filter (e.g., {"file_type": ".pdf"})
        
        Returns:
            List of RetrievalResult objects, sorted by relevance
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to retrieve()")
            return []
        
        k = top_k if top_k is not None else self.top_k
        
        logger.debug(f"Retrieving {k} chunks for query: {query[:100]}...")
        
        try:
            # Query ChromaDB
            raw_results = self.chromadb_client.query(
                query_text=query,
                top_k=k,
                where=filter_metadata
            )
            
            if not raw_results:
                logger.info("No results found for query")
                return []
            
            # Convert to RetrievalResult objects
            results = []
            for result in raw_results:
                # Calculate relevance score (inverse of distance, normalized)
                # ChromaDB distance is typically 0-2, where 0 is identical
                distance = result.get('distance', 1.0)
                relevance_score = max(0.0, 1.0 - (distance / 2.0))
                
                # Apply threshold filter
                if relevance_score >= self.similarity_threshold:
                    results.append(RetrievalResult(
                        text=result['document'],
                        metadata=result['metadata'],
                        distance=distance,
                        relevance_score=relevance_score
                    ))
            
            # Filter by threshold
            if not results:
                logger.info(
                    f"No results above threshold ({self.similarity_threshold})"
                )
                return []
            
            logger.info(
                f"Retrieved {len(results)} chunks "
                f"(filtered from {len(raw_results)} by threshold)"
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    def format_context_for_agent(
        self,
        results: List[RetrievalResult],
        max_context_length: int = 8000,
        include_metadata: bool = True
    ) -> str:
        """
        Format retrieved chunks as context for the agent layer
        Optimized for Claude API consumption
        
        Args:
            results: List of retrieval results
            max_context_length: Maximum context length in characters
            include_metadata: Whether to include detailed metadata
        
        Returns:
            Formatted context string optimized for Claude
        """
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        # Header
        header = f"Retrieved {len(results)} relevant document(s) from your knowledge base:\n"
        context_parts.append(header)
        current_length += len(header)
        
        for i, result in enumerate(results):
            # Format single chunk for agent
            if include_metadata:
                chunk_context = self._format_chunk_with_metadata(result, i + 1)
            else:
                chunk_context = self._format_chunk_simple(result, i + 1)
            
            chunk_length = len(chunk_context)
            
            # Check if adding this chunk would exceed limit
            if current_length + chunk_length > max_context_length:
                logger.warning(
                    f"Context length limit reached, using {i} of {len(results)} chunks"
                )
                break
            
            context_parts.append(chunk_context)
            current_length += chunk_length
        
        context = "\n\n".join(context_parts)
        
        logger.debug(
            f"Formatted context for agent: {len(context_parts)-1} chunks, "
            f"{current_length} characters"
        )
        
        return context
    
    def format_context(
        self,
        results: List[RetrievalResult],
        max_context_length: int = 8000
    ) -> str:
        """
        Format retrieved chunks into context for Claude
        (Legacy method - now calls format_context_for_agent)
        
        Args:
            results: List of retrieval results
            max_context_length: Maximum context length in characters
        
        Returns:
            Formatted context string
        """
        return self.format_context_for_agent(
            results, 
            max_context_length=max_context_length,
            include_metadata=True
        )
    
    def retrieve_and_format(
        self,
        query: str,
        top_k: Optional[int] = None,
        max_context_length: int = 8000
    ) -> tuple[str, List[RetrievalResult]]:
        """
        Retrieve and format in one call (convenience method)
        
        Args:
            query: User query
            top_k: Number of results
            max_context_length: Max context length
        
        Returns:
            Tuple of (formatted_context, results)
        """
        results = self.retrieve(query, top_k)
        context = self.format_context_for_agent(results, max_context_length)
        
        return context, results
    
    def get_context_for_query(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> str:
        """
        Get formatted context for a query (agent-optimized)
        Simple method for agent integration
        
        Args:
            query: User query
            top_k: Number of results to retrieve
            
        Returns:
            Formatted context string ready for agent
        """
        context, _ = self.retrieve_and_format(query, top_k)
        return context
    
    # ========================================================================
    # Citation Formatting
    # ========================================================================
    
    def format_citations(
        self,
        results: List[RetrievalResult]
    ) -> List[Dict[str, Any]]:
        """
        Format results as citations for UI
        
        Args:
            results: List of retrieval results
        
        Returns:
            List of citation dictionaries for UI
        """
        citations = []
        
        for result in results:
            citation = {
                'filename': result.metadata.get('filename', 'Unknown'),
                'filepath': result.metadata.get('filepath', ''),
                'excerpt': self._truncate_text(result.text, max_length=200),
                'chunk_index': result.metadata.get('chunk_index', 0),
                'relevance_score': result.relevance_score,
                'file_type': result.metadata.get('file_type', ''),
            }
            
            citations.append(citation)
        
        return citations
    
    def get_source_documents(
        self,
        results: List[RetrievalResult]
    ) -> List[str]:
        """
        Extract unique source document filenames from results
        Useful for agent to know which documents were used
        
        Args:
            results: List of retrieval results
            
        Returns:
            List of unique source filenames
        """
        sources = set()
        for result in results:
            filename = result.metadata.get('filename', 'Unknown')
            sources.add(filename)
        
        return sorted(list(sources))
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _format_chunk_with_metadata(
        self,
        result: RetrievalResult,
        index: int
    ) -> str:
        """
        Format a single chunk with full metadata for context
        
        Args:
            result: Retrieval result
            index: Chunk number (1-indexed)
        
        Returns:
            Formatted chunk string
        """
        filename = result.metadata.get('filename', 'Unknown')
        filepath = result.metadata.get('filepath', '')
        chunk_index = result.metadata.get('chunk_index', 0)
        
        # Format with metadata
        formatted = f"""[Document {index}]
Source: {filename}
Path: {filepath}
Chunk: {chunk_index}
Relevance: {result.relevance_score:.2f}

Content:
{result.text}
"""
        
        return formatted
    
    def _format_chunk_simple(
        self,
        result: RetrievalResult,
        index: int
    ) -> str:
        """
        Format a single chunk with minimal metadata (more concise)
        
        Args:
            result: Retrieval result
            index: Chunk number (1-indexed)
        
        Returns:
            Formatted chunk string
        """
        filename = result.metadata.get('filename', 'Unknown')
        
        formatted = f"""[Document {index}: {filename}]
{result.text}
"""
        
        return formatted
    
    def _format_single_chunk(
        self,
        result: RetrievalResult,
        index: int
    ) -> str:
        """
        Format a single chunk for context (legacy method)
        
        Args:
            result: Retrieval result
            index: Chunk number (1-indexed)
        
        Returns:
            Formatted chunk string
        """
        return self._format_chunk_with_metadata(result, index)
    
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
        
        return text[:max_length] + "..."
    
    # ========================================================================
    # Statistics & Info
    # ========================================================================
    
    def get_retrieval_stats(
        self,
        results: List[RetrievalResult]
    ) -> Dict[str, Any]:
        """
        Get statistics about retrieval results
        
        Args:
            results: List of results
        
        Returns:
            Statistics dictionary
        """
        if not results:
            return {
                'total_chunks': 0,
                'avg_relevance': 0.0,
                'min_relevance': 0.0,
                'max_relevance': 0.0,
                'unique_files': 0
            }
        
        relevance_scores = [r.relevance_score for r in results]
        unique_files = set(r.metadata.get('filepath') for r in results)
        
        return {
            'total_chunks': len(results),
            'avg_relevance': sum(relevance_scores) / len(relevance_scores),
            'min_relevance': min(relevance_scores),
            'max_relevance': max(relevance_scores),
            'unique_files': len(unique_files),
            'file_types': self._get_file_type_distribution(results),
            'source_documents': self.get_source_documents(results)
        }
    
    def _get_file_type_distribution(
        self,
        results: List[RetrievalResult]
    ) -> Dict[str, int]:
        """Get distribution of file types in results"""
        distribution = {}
        
        for result in results:
            file_type = result.metadata.get('file_type', 'unknown')
            distribution[file_type] = distribution.get(file_type, 0) + 1
        
        return distribution
    
    # ========================================================================
    # Configuration
    # ========================================================================
    
    def set_top_k(self, top_k: int):
        """Update top_k setting"""
        self.top_k = top_k
        logger.info(f"Updated top_k to: {top_k}")
    
    def set_similarity_threshold(self, threshold: float):
        """Update similarity threshold"""
        if not 0.0 <= threshold <= 1.0:
            logger.error(f"Invalid threshold: {threshold}, must be 0.0-1.0")
            return
        
        self.similarity_threshold = threshold
        logger.info(f"Updated similarity threshold to: {threshold}")
    
    # ========================================================================
    # Agent Integration Helper
    # ========================================================================
    
    def prepare_context_for_agent(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Prepare complete context package for agent layer
        
        Args:
            query: User's current query
            conversation_history: Previous conversation messages
            top_k: Number of chunks to retrieve
            
        Returns:
            Dictionary with formatted context and metadata for agent
        """
        # Retrieve relevant chunks
        results = self.retrieve(query, top_k)
        
        # Format context for Claude
        context = self.format_context_for_agent(results)
        
        # Get source documents
        sources = self.get_source_documents(results)
        
        # Get statistics
        stats = self.get_retrieval_stats(results)
        
        return {
            'rag_context': context,
            'source_documents': sources,
            'retrieval_stats': stats,
            'query': query,
            'has_context': len(results) > 0,
            'num_chunks': len(results)
        }


# ============================================================================
# Testing/Debug
# ============================================================================

def test_retriever():
    """Test retriever with sample data"""
    logger.info("Testing RAG Retriever with agent integration...")
    
    # Create retriever
    retriever = RAGRetriever(top_k=5, similarity_threshold=0.3)
    
    # Test query
    query = "What is machine learning?"
    
    logger.info(f"Testing query: {query}")
    results = retriever.retrieve(query)
    
    logger.info(f"Retrieved {len(results)} results")
    
    for i, result in enumerate(results):
        logger.info(f"  {i+1}. {result}")
    
    # Test agent-optimized formatting
    if results:
        context = retriever.format_context_for_agent(results)
        logger.info(f"Formatted context for agent ({len(context)} chars)")
        
        # Test context preparation
        context_package = retriever.prepare_context_for_agent(query)
        logger.info(f"Context package prepared:")
        logger.info(f"  - Has context: {context_package['has_context']}")
        logger.info(f"  - Num chunks: {context_package['num_chunks']}")
        logger.info(f"  - Sources: {context_package['source_documents']}")
        
        citations = retriever.format_citations(results)
        logger.info(f"Generated {len(citations)} citations")
        
        stats = retriever.get_retrieval_stats(results)
        logger.info(f"Stats: {stats}")


if __name__ == "__main__":
    test_retriever()