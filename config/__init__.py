"""
config/__init__.py
Configuration package initialization
"""

from config.settings import (
    # Application info
    APP_NAME,
    APP_VERSION,
    APP_AUTHOR,
    APP_DESCRIPTION,
    
    # Directories
    USER_DATA_DIR,
    CONFIG_FILE,
    API_KEY_FILE,
    LOGS_DIR,
    CHROMA_DIR,
    
    # API Configuration
    CLAUDE_MODEL,
    CLAUDE_MAX_TOKENS,
    CLAUDE_TEMPERATURE,
    MAX_TOOL_CALLS_PER_QUERY,
    
    # RAG Configuration
    DEFAULT_TOP_K,
    MIN_TOP_K,
    MAX_TOP_K,
    DEFAULT_SIMILARITY_THRESHOLD,
    
    # Text Processing
    DEFAULT_CHUNK_SIZE,
    MIN_CHUNK_SIZE,
    MAX_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    MIN_CHUNK_OVERLAP,
    MAX_CHUNK_OVERLAP,
    
    # Supported File Types
    SUPPORTED_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    TEXT_EXTENSIONS,
    CODE_EXTENSIONS,
    WEB_EXTENSIONS,
    DATA_EXTENSIONS,
    CONFIG_EXTENSIONS,
    
    # UI Configuration
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    SIDEBAR_WIDTH,
    
    # Indexing Configuration
    INDEXING_BATCH_SIZE,
    MAX_FILE_SIZE_MB,
    MAX_FILE_SIZE_BYTES,
    SKIP_DIRECTORIES,
    
    # Messages
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    
    # Default Configuration
    DEFAULT_CONFIG,
    
    # Helper Functions
    is_supported_file,
    should_skip_directory,
    get_file_category,
    get_settings_dict,
)

__all__ = [
    # Application info
    'APP_NAME',
    'APP_VERSION',
    'APP_AUTHOR',
    'APP_DESCRIPTION',
    
    # Directories
    'USER_DATA_DIR',
    'CONFIG_FILE',
    'API_KEY_FILE',
    'LOGS_DIR',
    'CHROMA_DIR',
    
    # API Configuration
    'CLAUDE_MODEL',
    'CLAUDE_MAX_TOKENS',
    'CLAUDE_TEMPERATURE',
    'MAX_TOOL_CALLS_PER_QUERY',
    
    # RAG Configuration
    'DEFAULT_TOP_K',
    'MIN_TOP_K',
    'MAX_TOP_K',
    'DEFAULT_SIMILARITY_THRESHOLD',
    
    # Text Processing
    'DEFAULT_CHUNK_SIZE',
    'MIN_CHUNK_SIZE',
    'MAX_CHUNK_SIZE',
    'DEFAULT_CHUNK_OVERLAP',
    'MIN_CHUNK_OVERLAP',
    'MAX_CHUNK_OVERLAP',
    
    # Supported File Types
    'SUPPORTED_EXTENSIONS',
    'DOCUMENT_EXTENSIONS',
    'TEXT_EXTENSIONS',
    'CODE_EXTENSIONS',
    'WEB_EXTENSIONS',
    'DATA_EXTENSIONS',
    'CONFIG_EXTENSIONS',
    
    # UI Configuration
    'DEFAULT_WINDOW_WIDTH',
    'DEFAULT_WINDOW_HEIGHT',
    'MIN_WINDOW_WIDTH',
    'MIN_WINDOW_HEIGHT',
    'SIDEBAR_WIDTH',
    
    # Indexing Configuration
    'INDEXING_BATCH_SIZE',
    'MAX_FILE_SIZE_MB',
    'MAX_FILE_SIZE_BYTES',
    'SKIP_DIRECTORIES',
    
    # Messages
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    
    # Default Configuration
    'DEFAULT_CONFIG',
    
    # Helper Functions
    'is_supported_file',
    'should_skip_directory',
    'get_file_category',
    'get_settings_dict',
]