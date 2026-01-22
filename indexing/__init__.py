"""
indexing/__init__.py
Indexing package initialization
"""

from indexing.indexer import Indexer, IndexingResult
from indexing.chromadb_client import ChromaDBClient
from indexing.file_readers import (
    get_reader_for_file,
    read_file,
    get_supported_extensions,
    FileReadError
)
from indexing.chunker import chunk_text, TextChunk, get_chunk_statistics
from indexing.normalizer import get_default_normalizer, get_aggressive_normalizer, Normalizer

__all__ = [
    # Main classes
    'Indexer',
    'IndexingResult',
    'ChromaDBClient',
    
    # File readers
    'get_reader_for_file',
    'read_file',
    'get_supported_extensions',
    'FileReadError',
    
    # Chunker
    'chunk_text',
    'TextChunk',
    'get_chunk_statistics',
    # Normalizer
    'get_default_normalizer',
    'get_aggressive_normalizer',
    'Normalizer',
]