"""
indexing/indexer.py
Main indexer orchestrator - coordinates file reading, chunking, and storage
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from indexing.file_readers import get_reader_for_file, FileReadError
from indexing.chunker import chunk_text, TextChunk
from indexing.chromadb_client import ChromaDBClient
from indexing.normalizer import get_default_normalizer, Normalizer
from mcp_servers import config
from security.config_manager import ConfigManager, get_config_manager
from utils.logger import get_logger
from utils.file_utils import list_files_in_directory, get_file_size
from config.settings import (
    SUPPORTED_EXTENSIONS,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    MAX_FILE_SIZE_BYTES,
    INDEXING_BATCH_SIZE,
    SKIP_DIRECTORIES,
    SKIP_HIDDEN_FILES,
    should_skip_directory
)

logger = get_logger(__name__)


class IndexingResult:
    """Result of an indexing operation"""
    
    def __init__(self):
        self.files_processed = 0
        self.files_skipped = 0
        self.files_failed = 0
        self.chunks_created = 0
        self.total_size_bytes = 0
        self.errors = []
        self.start_time = datetime.now()
        self.end_time = None
    
    def mark_complete(self):
        """Mark indexing as complete"""
        self.end_time = datetime.now()
    
    def get_duration(self) -> float:
        """Get duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'files_processed': self.files_processed,
            'files_skipped': self.files_skipped,
            'files_failed': self.files_failed,
            'chunks_created': self.chunks_created,
            'total_size_mb': self.total_size_bytes / (1024 * 1024),
            'duration_seconds': self.get_duration(),
            'errors': self.errors
        }
    
    def __repr__(self):
        return (
            f"IndexingResult(processed={self.files_processed}, "
            f"skipped={self.files_skipped}, failed={self.files_failed}, "
            f"chunks={self.chunks_created})"
        )


class Indexer:
    """
    Main indexer orchestrator for file processing and storage
    """
    
    def __init__(
        self,
        chromadb_client: Optional[ChromaDBClient] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP, 
        use_normalization=True, normalizer=None,
        config_manager: ConfigManager = None
    ):
        """
        Initialize Indexer
        
        Args:
            chromadb_client: ChromaDB client instance (creates new if None)
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chromadb_client = chromadb_client or ChromaDBClient()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.config_manager = config_manager or get_config_manager()
        self.use_normalization = use_normalization
        self.normalizer = normalizer or get_default_normalizer()

        logger.info(
            f"Indexer initialized (chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap})"
        )
    
    # ========================================================================
    # Public API - Directory Indexing
    # ========================================================================
    
    def index_directory(
        self,
        directory_path: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        recursive: bool = True
    ) -> IndexingResult:
        """
        Index all supported files in a directory
        
        Args:
            directory_path: Path to directory
            progress_callback: Optional callback(current, total, message)
            recursive: If True, search subdirectories
        
        Returns:
            IndexingResult with statistics
        """
        logger.info(f"Starting directory indexing: {directory_path}")
        try:
            self.config_manager.reload()
        except Exception as e:
            logger.warning(f"Config reload failed: {e}")

        result = IndexingResult()
        
        try:
            directory = Path(directory_path)
            
            if not directory.exists():
                error_msg = f"Directory does not exist: {directory_path}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                result.mark_complete()
                return result
            
            if not directory.is_dir():
                error_msg = f"Path is not a directory: {directory_path}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                result.mark_complete()
                return result
            
            # Discover files
            files = self._discover_files(directory, recursive)
            total_files = len(files)
            
            if total_files == 0:
                logger.warning(f"No supported files found in: {directory_path}")
                result.mark_complete()
                return result
            
            logger.info(f"Found {total_files} files to index")
            
            # Index files
            for i, filepath in enumerate(files):
                # Update progress
                if progress_callback:
                    progress_callback(i + 1, total_files, f"Indexing: {filepath.name}")
                
                # Index file
                try:
                    file_result = self.index_file(filepath)
                    
                    if file_result['success']:
                        result.files_processed += 1
                        result.chunks_created += file_result['chunks_created']
                        result.total_size_bytes += file_result['file_size']
                    else:
                        result.files_failed += 1
                        if 'error' in file_result:
                            result.errors.append(f"{filepath}: {file_result['error']}")
                
                except Exception as e:
                    logger.error(f"Error indexing file {filepath}: {e}")
                    result.files_failed += 1
                    result.errors.append(f"{filepath}: {str(e)}")
            
            result.mark_complete()
            logger.info(f"Directory indexing complete: {result}")
            
            return result
        
        except Exception as e:
            logger.error(f"Critical error during directory indexing: {e}")
            result.errors.append(f"Critical error: {str(e)}")
            result.mark_complete()
            return result
    
    def index_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Index a single file
        
        Args:
            filepath: Path to file
        
        Returns:
            Dictionary with indexing result
        """
        filepath = Path(filepath)
        
        try:
            # Check if file should be skipped
            skip_reason = self._should_skip_file(filepath)
            if skip_reason:
                logger.debug(f"Skipping file: {filepath} - {skip_reason}")
                return {
                    'success': False,
                    'skipped': True,
                    'reason': skip_reason
                }
            
            # Get file info
            file_size = int(get_file_size(filepath))
            filename = filepath.name
            file_type = filepath.suffix.lower()
            
            logger.debug(f"Indexing file: {filepath} ({file_size} bytes)")
            
            # Read file
            reader = get_reader_for_file(filepath)
            if not reader:
                return {
                    'success': False,
                    'error': f"No reader available for {file_type}"
                }
            
            text = reader.read(filepath)
            
            if not text or not text.strip():
                return {
                    'success': False,
                    'error': "No text extracted from file"
                }
            # Normalize text
            if self.use_normalization:
                text = self.normalizer.normalize(text)

            logger.debug(f"Extracted {len(text)} characters from {filepath}")
            
            # Chunk text
            chunks = chunk_text(
                text=text,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                preserve_sentences=True
            )
            
            if not chunks:
                return {
                    'success': False,
                    'error': "No chunks created from text"
                }
            
            logger.debug(f"Created {len(chunks)} chunks from {filepath}")
            
            # Prepare for storage
            documents = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                # Generate ID
                doc_id = self.chromadb_client.generate_document_id(
                    str(filepath),
                    chunk.chunk_index
                )
                
                # Prepare metadata
                metadata = self.chromadb_client.prepare_metadata(
                    filepath=str(filepath),
                    filename=filename,
                    chunk_index=chunk.chunk_index,
                    file_type=file_type,
                    file_size=file_size
                )
                
                documents.append(chunk.text)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            # Store in ChromaDB
            success = self.chromadb_client.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            if not success:
                return {
                    'success': False,
                    'error': "Failed to store in ChromaDB"
                }
            
            logger.info(f"Successfully indexed: {filepath} ({len(chunks)} chunks)")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'chunks_created': len(chunks),
                'file_size': file_size
            }
        
        except FileReadError as e:
            logger.error(f"Failed to read file {filepath}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        
        except Exception as e:
            logger.error(f"Error indexing file {filepath}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reindex_all(
        self,
        directories: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> IndexingResult:
        """
        Re-index all directories (clears existing index first)
        
        Args:
            directories: List of directory paths
            progress_callback: Optional callback(current, total, message)
        
        Returns:
            IndexingResult with statistics
        """
        logger.info(f"Starting full re-index of {len(directories)} directories")
        
        # Clear existing index
        logger.info("Clearing existing index...")
        self.chromadb_client.clear_collection()
        
        # Index all directories
        combined_result = IndexingResult()
        
        for dir_idx, directory in enumerate(directories):
            logger.info(f"Indexing directory {dir_idx + 1}/{len(directories)}: {directory}")
            
            # Create progress callback that accounts for multiple directories
            if progress_callback:
                def dir_progress(current, total, message):
                    overall_progress = (dir_idx * 100 + (current * 100 // total)) // len(directories)
                    progress_callback(overall_progress, 100, message)
            else:
                dir_progress = None
            
            result = self.index_directory(directory, dir_progress)
            
            # Combine results
            combined_result.files_processed += result.files_processed
            combined_result.files_skipped += result.files_skipped
            combined_result.files_failed += result.files_failed
            combined_result.chunks_created += result.chunks_created
            combined_result.total_size_bytes += result.total_size_bytes
            combined_result.errors.extend(result.errors)
        
        combined_result.mark_complete()
        logger.info(f"Full re-index complete: {combined_result}")
        
        return combined_result
    
    def remove_file(self, filepath: str) -> bool:
        """
        Remove file from index
        
        Args:
            filepath: Path to file
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Removing file from index: {filepath}")
        
        try:
            success = self.chromadb_client.delete_by_filepath(filepath)
            
            if success:
                logger.info(f"Successfully removed file from index: {filepath}")
            else:
                logger.warning(f"Failed to remove file from index: {filepath}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error removing file from index: {e}")
            return False
    
    # ========================================================================
    # Public API - Statistics & Info
    # ========================================================================
    
    def get_indexed_files(self) -> List[str]:
        """
        Get list of all indexed files
        
        Returns:
            List of file paths
        """
        return self.chromadb_client.get_indexed_files()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get indexing statistics
        
        Returns:
            Dictionary with statistics
        """
        chromadb_stats = self.chromadb_client.get_stats()
        
        return {
            'total_chunks': chromadb_stats['total_documents'],
            'indexed_files': len(self.get_indexed_files()),
            'file_types': chromadb_stats['file_types'],
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'collection_name': chromadb_stats['collection_name']
        }
    
    def is_file_indexed(self, filepath: str) -> bool:
        """
        Check if file is indexed
        
        Args:
            filepath: Path to file
        
        Returns:
            True if indexed, False otherwise
        """
        return self.chromadb_client.file_is_indexed(filepath)
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _discover_files(self, directory: Path, recursive: bool) -> List[Path]:
        """
        Discover all supported files in directory
        
        Args:
            directory: Directory to search
            recursive: If True, search subdirectories
        
        Returns:
            List of file paths
        """
        try:
            cfg = self.config_manager.get_config()
            enabled = set(cfg.get('file_types_enabled', []))
            supported = set(SUPPORTED_EXTENSIONS)
            extensions = sorted(enabled & supported)
            files = list_files_in_directory(
                directory=directory,
                extensions=extensions,
                recursive=recursive,
                include_hidden=not SKIP_HIDDEN_FILES
            )
            
            # Filter out files in skip directories
            if recursive:
                filtered_files = []
                for filepath in files:
                    # Check if any parent directory should be skipped
                    should_skip = False
                    for parent in filepath.parents:
                        if should_skip_directory(parent.name):
                            should_skip = True
                            break
                    
                    if not should_skip:
                        filtered_files.append(filepath)
                
                files = filtered_files
            
            logger.debug(f"Discovered {len(files)} files in {directory}")
            return files
        
        except Exception as e:
            logger.error(f"Error discovering files in {directory}: {e}")
            return []
    
    def _should_skip_file(self, filepath: Path) -> Optional[str]:
        """
        Check if file should be skipped
        
        Args:
            filepath: Path to file
        
        Returns:
            Skip reason if should skip, None otherwise
        """
        # Check if file exists
        if not filepath.exists():
            return "File does not exist"
        
        # Check if it's a file
        if not filepath.is_file():
            return "Not a file"
        
        # Check file size
        try:
            file_size = int(get_file_size(filepath))
            if file_size > MAX_FILE_SIZE_BYTES:
                return f"File too large ({file_size / (1024*1024):.1f} MB)"
            
            if file_size == 0:
                return "Empty file"
        
        except Exception as e:
            return f"Cannot get file size: {str(e)}"
        
        # Check if extension is supported
        extension = filepath.suffix.lower()
        try:
            # Get enabled extensions from config
            config = self.config_manager.get_config()
            enabled_extensions = config.get('file_types_enabled', [])
            if extension not in enabled_extensions:
                return f"File type disabled: {extension}"
        except Exception as e:
            return f"Error checking enabled file types: {str(e)}"
        
        # if extension not in SUPPORTED_EXTENSIONS:
        #     return f"Unsupported file type: {extension}"
        
        # Check if file is readable
        from utils.file_utils import is_readable
        if not is_readable(filepath):
            return "File not readable"
        
        return None


# ============================================================================
# Testing/Debug
# ============================================================================

def test_indexer():
    """Test indexer with sample files"""
    logger.info("Testing Indexer...")
    
    # Create indexer
    indexer = Indexer()
    
    # Test stats
    stats = indexer.get_stats()
    logger.info(f"Initial stats: {stats}")
    
    # Test health
    health = indexer.chromadb_client.health_check()
    logger.info(f"Health check: {health}")


if __name__ == "__main__":
    test_indexer()
