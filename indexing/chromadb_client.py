"""
indexing/chromadb_client.py
ChromaDB wrapper for vector storage and semantic search
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings

from utils.logger import get_logger
from config.settings import CHROMA_DIR, CHROMA_COLLECTION_NAME

logger = get_logger(__name__)


class ChromaDBClient:
    """
    Wrapper around ChromaDB for vector storage and retrieval
    """
    
    def __init__(self, persist_directory: Optional[Path] = None, collection_name: Optional[str] = None):
        """
        Initialize ChromaDB client
        
        Args:
            persist_directory: Directory to persist ChromaDB data (default: ~/.insightos/chroma)
            collection_name: Name of collection to use (default: insightos_documents)
        """
        self.persist_directory = persist_directory or CHROMA_DIR
        self.collection_name = collection_name or CHROMA_COLLECTION_NAME
        
        # Ensure directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,  # Disable telemetry
                    allow_reset=True
                )
            )
            logger.info(f"ChromaDB client initialized at: {self.persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        logger.info(f"Using collection: {self.collection_name}")
    
    def _get_or_create_collection(self):
        """
        Get existing collection or create new one
        
        Returns:
            ChromaDB collection
        """
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
            return collection
        except Exception:
            # Create new collection if it doesn't exist
            logger.info(f"Creating new collection: {self.collection_name}")
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "InsightOS document embeddings"}
            )
            return collection
    
    # ========================================================================
    # Document Operations
    # ========================================================================
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> bool:
        """
        Add documents to collection
        
        Args:
            documents: List of document texts (chunks)
            metadatas: List of metadata dicts (one per document)
            ids: List of unique IDs (one per document)
        
        Returns:
            True if successful, False otherwise
        
        Note:
            ChromaDB automatically generates embeddings for documents
        """
        try:
            # Validate inputs
            if not documents or not metadatas or not ids:
                logger.error("Empty documents, metadatas, or ids provided")
                return False
            
            if not (len(documents) == len(metadatas) == len(ids)):
                logger.error("Length mismatch between documents, metadatas, and ids")
                return False
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to collection")
            return True
        
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def add_single_document(
        self,
        document: str,
        metadata: Dict[str, Any],
        doc_id: str
    ) -> bool:
        """
        Add single document to collection
        
        Args:
            document: Document text
            metadata: Metadata dict
            doc_id: Unique ID
        
        Returns:
            True if successful, False otherwise
        """
        return self.add_documents(
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )
    
    def delete_by_id(self, doc_ids: List[str]) -> bool:
        """
        Delete documents by IDs
        
        Args:
            doc_ids: List of document IDs to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not doc_ids:
                logger.warning("No document IDs provided for deletion")
                return True
            
            self.collection.delete(ids=doc_ids)
            logger.info(f"Deleted {len(doc_ids)} documents")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False
    
    def delete_by_filepath(self, filepath: str) -> bool:
        """
        Delete all documents from a specific file
        
        Args:
            filepath: Path to file whose documents should be deleted
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Query for all documents with this filepath
            results = self.collection.get(
                where={"filepath": filepath}
            )
            
            if not results or not results['ids']:
                logger.info(f"No documents found for filepath: {filepath}")
                return True
            
            # Delete by IDs
            doc_ids = results['ids']
            return self.delete_by_id(doc_ids)
        
        except Exception as e:
            logger.error(f"Failed to delete documents by filepath: {e}")
            return False
    
    # ========================================================================
    # Query Operations
    # ========================================================================
    
    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query collection with semantic search
        
        Args:
            query_text: Query text to search for
            top_k: Number of results to return
            where: Optional metadata filter (e.g., {"file_type": ".pdf"})
        
        Returns:
            List of result dictionaries with keys: id, document, metadata, distance
        """
        try:
            # Query collection
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where
            )
            
            # Format results
            formatted_results = []
            
            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            logger.debug(f"Query returned {len(formatted_results)} results")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Failed to query collection: {e}")
            return []
    
    def query_with_threshold(
        self,
        query_text: str,
        top_k: int = 5,
        distance_threshold: float = 1.5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query with distance threshold filtering
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            distance_threshold: Maximum distance (lower = more similar)
            where: Optional metadata filter
        
        Returns:
            Filtered list of results
        """
        results = self.query(query_text, top_k, where)
        
        # Filter by distance threshold
        filtered_results = [
            r for r in results
            if r['distance'] is not None and r['distance'] <= distance_threshold
        ]
        
        logger.debug(f"Filtered {len(results)} results to {len(filtered_results)} within threshold")
        return filtered_results
    
    # ========================================================================
    # Collection Management
    # ========================================================================
    
    def get_document_count(self) -> int:
        """
        Get total number of documents in collection
        
        Returns:
            Document count
        """
        try:
            count = self.collection.count()
            return count
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            return 0
    
    def get_all_documents(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get all documents from collection
        
        Args:
            limit: Maximum number of documents to return (None = all)
        
        Returns:
            Dictionary with ids, documents, metadatas
        """
        try:
            results = self.collection.get(
                limit=limit
            )
            return results
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return {'ids': [], 'documents': [], 'metadatas': []}
    
    def get_documents_by_file(self, filepath: str) -> Dict[str, Any]:
        """
        Get all documents from a specific file
        
        Args:
            filepath: Path to file
        
        Returns:
            Dictionary with ids, documents, metadatas
        """
        try:
            results = self.collection.get(
                where={"filepath": filepath}
            )
            return results
        except Exception as e:
            logger.error(f"Failed to get documents by file: {e}")
            return {'ids': [], 'documents': [], 'metadatas': []}
    
    def clear_collection(self) -> bool:
        """
        Clear all documents from collection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all document IDs
            results = self.collection.get()
            
            if results and results['ids']:
                doc_ids = results['ids']
                self.collection.delete(ids=doc_ids)
                logger.info(f"Cleared {len(doc_ids)} documents from collection")
            else:
                logger.info("Collection already empty")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
    
    def delete_collection(self) -> bool:
        """
        Delete entire collection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
            
            # Recreate collection
            self.collection = self._get_or_create_collection()
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
    
    # ========================================================================
    # Statistics & Info
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics
        
        Returns:
            Dictionary with statistics
        """
        try:
            count = self.get_document_count()
            
            # Get sample of documents to analyze
            sample = self.collection.get(limit=100)
            
            # Count unique files
            unique_files = set()
            file_types = {}
            
            if sample and sample['metadatas']:
                for metadata in sample['metadatas']:
                    if 'filepath' in metadata:
                        unique_files.add(metadata['filepath'])
                    
                    if 'file_type' in metadata:
                        file_type = metadata['file_type']
                        file_types[file_type] = file_types.get(file_type, 0) + 1
            
            return {
                'total_documents': count,
                'unique_files_sampled': len(unique_files),
                'file_types': file_types,
                'collection_name': self.collection_name,
                'persist_directory': str(self.persist_directory)
            }
        
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                'total_documents': 0,
                'unique_files_sampled': 0,
                'file_types': {},
                'collection_name': self.collection_name,
                'persist_directory': str(self.persist_directory)
            }
    
    def get_indexed_files(self) -> List[str]:
        """
        Get list of all indexed file paths
        
        Returns:
            List of unique file paths
        """
        try:
            # Get all documents
            results = self.collection.get()
            
            if not results or not results['metadatas']:
                return []
            
            # Extract unique file paths
            filepaths = set()
            for metadata in results['metadatas']:
                if 'filepath' in metadata:
                    filepaths.add(metadata['filepath'])
            
            return sorted(list(filepaths))
        
        except Exception as e:
            logger.error(f"Failed to get indexed files: {e}")
            return []
    
    def file_is_indexed(self, filepath: str) -> bool:
        """
        Check if file is indexed
        
        Args:
            filepath: Path to file
        
        Returns:
            True if file has documents in collection, False otherwise
        """
        try:
            results = self.collection.get(
                where={"filepath": filepath},
                limit=1
            )
            
            return bool(results and results['ids'])
        
        except Exception as e:
            logger.error(f"Failed to check if file is indexed: {e}")
            return False
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def generate_document_id(self, filepath: str, chunk_index: int) -> str:
        """
        Generate unique document ID
        
        Args:
            filepath: Path to file
            chunk_index: Index of chunk
        
        Returns:
            Unique ID string
        """
        # Use filepath + chunk_index for deterministic IDs
        # This allows us to update/replace documents
        import hashlib
        
        # Create unique ID from filepath and chunk index
        unique_string = f"{filepath}::{chunk_index}"
        doc_id = hashlib.md5(unique_string.encode()).hexdigest()
        
        return doc_id
    
    def prepare_metadata(
        self,
        filepath: str,
        filename: str,
        chunk_index: int,
        file_type: str,
        file_size: int
    ) -> Dict[str, Any]:
        """
        Prepare metadata dictionary for a document
        
        Args:
            filepath: Full path to file
            filename: Filename only
            chunk_index: Chunk index
            file_type: File extension (e.g., '.pdf')
            file_size: File size in bytes
        
        Returns:
            Metadata dictionary
        """
        return {
            'filepath': filepath,
            'filename': filename,
            'chunk_index': chunk_index,
            'file_type': file_type,
            'file_size': file_size,
            'timestamp': datetime.now().isoformat()
        }
    
    def health_check(self) -> bool:
        """
        Check if ChromaDB is working properly
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get collection count
            count = self.get_document_count()
            logger.info(f"Health check passed: {count} documents in collection")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# ============================================================================
# Testing/Debug
# ============================================================================

def test_chromadb():
    """Test ChromaDB client"""
    logger.info("Testing ChromaDB client...")
    
    # Create client
    client = ChromaDBClient()
    
    # Test health check
    logger.info(f"Health check: {client.health_check()}")
    
    # Test stats
    stats = client.get_stats()
    logger.info(f"Stats: {stats}")
    
    # Test adding documents
    test_docs = [
        "This is the first test document about Python programming.",
        "This is the second test document about machine learning.",
        "This is the third test document about web development."
    ]
    
    test_metadatas = [
        client.prepare_metadata("/test/file1.txt", "file1.txt", 0, ".txt", 100),
        client.prepare_metadata("/test/file2.txt", "file2.txt", 0, ".txt", 150),
        client.prepare_metadata("/test/file3.txt", "file3.txt", 0, ".txt", 200),
    ]
    
    test_ids = [
        client.generate_document_id("/test/file1.txt", 0),
        client.generate_document_id("/test/file2.txt", 0),
        client.generate_document_id("/test/file3.txt", 0),
    ]
    
    success = client.add_documents(test_docs, test_metadatas, test_ids)
    logger.info(f"Added test documents: {success}")
    
    # Test query
    results = client.query("Python programming", top_k=2)
    logger.info(f"Query results: {len(results)}")
    for i, result in enumerate(results):
        logger.info(f"  Result {i+1}: {result['document'][:50]}... (distance: {result['distance']:.3f})")
    
    # Test stats after adding
    stats = client.get_stats()
    logger.info(f"Stats after adding: {stats}")
    
    # Clean up
    client.clear_collection()
    logger.info("Cleared test documents")


if __name__ == "__main__":
    test_chromadb()