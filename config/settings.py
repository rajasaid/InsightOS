"""
config/settings.py
Application-wide settings and constants
"""

from pathlib import Path

# ============================================================================
# Application Information
# ============================================================================

APP_NAME = "InsightOS"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Raja"
APP_DESCRIPTION = "AI-powered desktop knowledge assistant"

# ============================================================================
# Directories
# ============================================================================

# User data directory
USER_DATA_DIR = Path.home() / ".insightos"

# Config file
CONFIG_FILE = USER_DATA_DIR / "config.json"

# Encrypted API key file
API_KEY_FILE = USER_DATA_DIR / ".api_key.enc"

# Logs directory
LOGS_DIR = USER_DATA_DIR / "logs"

# ChromaDB directory
CHROMA_DIR = USER_DATA_DIR / "chroma"

# Ensure directories exist
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# API Configuration
# ============================================================================

# Claude API settings
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 4096
CLAUDE_TEMPERATURE = 1.0

# Agentic mode settings
MAX_TOOL_CALLS_PER_QUERY = 5

# API rate limits (for user reference)
API_RATE_LIMIT_INFO = {
    "requests_per_minute": 50,
    "tokens_per_minute": 40000,
    "requests_per_day": 1000,
}

# ============================================================================
# RAG Configuration
# ============================================================================

# Retrieval settings
DEFAULT_TOP_K = 5
MIN_TOP_K = 1
MAX_TOP_K = 20

# Embedding settings
EMBEDDING_MODEL = "text-embedding-3-small"  # If using OpenAI embeddings
# For Claude/Anthropic, embeddings would be through another service

# Similarity threshold (0.0 - 1.0)
MIN_SIMILARITY_THRESHOLD = 0.0
DEFAULT_SIMILARITY_THRESHOLD = 0.3

# ============================================================================
# Text Processing Configuration
# ============================================================================

# Chunking settings
DEFAULT_CHUNK_SIZE = 300  # characters
MIN_CHUNK_SIZE = 50
MAX_CHUNK_SIZE = 4000

DEFAULT_CHUNK_OVERLAP = 70  # characters
MIN_CHUNK_OVERLAP = 0
MAX_CHUNK_OVERLAP = 700

# ============================================================================
# Supported File Types
# ============================================================================

# Document types
DOCUMENT_EXTENSIONS = [
    '.pdf',   # PDF documents
    '.doc',   # Word 97-2003
    '.docx',  # Word 2007+
    '.odt',   # OpenDocument Text
    '.pages', # Apple Pages
    '.rtf',   # Rich Text Format
]

# Text types
TEXT_EXTENSIONS = [
    '.txt',   # Plain text
    '.md',    # Markdown
    '.asc',   # ASCII text
]

# Code types
CODE_EXTENSIONS = [
    '.py',    # Python
    '.java',  # Java
    '.js',    # JavaScript
    '.jsx',   # React
    '.ts',    # TypeScript
    '.tsx',   # TypeScript React
    '.cpp',   # C++
    '.c',     # C
    '.h',     # C/C++ header
    '.hpp',   # C++ header
    '.cs',    # C#
    '.rb',    # Ruby
    '.go',    # Go
    '.rs',    # Rust
    '.php',   # PHP
    '.swift', # Swift
    '.kt',    # Kotlin
]

# Web types
WEB_EXTENSIONS = [
    '.html',  # HTML
    '.htm',   # HTML (alternate)
    '.css',   # CSS
    '.xml',   # XML
    '.json',  # JSON
    '.yaml',  # YAML
    '.yml',   # YAML (alternate)
]

# Data types
DATA_EXTENSIONS = [
    '.csv',   # Comma-separated values
    '.tsv',   # Tab-separated values
    '.log',   # Log files
]

# Config types
CONFIG_EXTENSIONS = [
    '.ini',   # INI configuration
    '.cfg',   # Configuration
    '.conf',  # Configuration (alternate)
    '.toml',  # TOML
]

# All supported extensions
SUPPORTED_EXTENSIONS = (
    DOCUMENT_EXTENSIONS +
    TEXT_EXTENSIONS +
    CODE_EXTENSIONS +
    WEB_EXTENSIONS +
    DATA_EXTENSIONS +
    CONFIG_EXTENSIONS
)

# ============================================================================
# UI Configuration
# ============================================================================

# Window settings
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# Sidebar settings
SIDEBAR_WIDTH = 300
MIN_SIDEBAR_WIDTH = 250
MAX_SIDEBAR_WIDTH = 400

# Message settings
MAX_MESSAGE_HISTORY = 100  # Maximum messages to keep in memory
MESSAGE_FADE_DURATION = 200  # milliseconds
CITATION_ANIMATION_DURATION = 150  # milliseconds

# Input settings
MAX_INPUT_LENGTH = 10000  # characters
INPUT_PLACEHOLDER = "Ask about your documents..."

# Progress update frequency
PROGRESS_UPDATE_INTERVAL = 100  # milliseconds

# ============================================================================
# Indexing Configuration
# ============================================================================

# Indexing settings
INDEXING_BATCH_SIZE = 50  # Files to process in one batch
INDEXING_PROGRESS_UPDATE_FREQUENCY = 5  # Update progress every N files

# File size limits
MAX_FILE_SIZE_MB = 50  # Maximum file size to process
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Hidden file handling
SKIP_HIDDEN_FILES = True  # Skip files starting with '.'
SKIP_HIDDEN_DIRECTORIES = True  # Skip directories starting with '.'

# Special directories to skip
SKIP_DIRECTORIES = [
    '__pycache__',
    'node_modules',
    '.git',
    '.svn',
    '.hg',
    '.venv',
    'venv',
    'env',
    '.tox',
    'build',
    'dist',
    '.egg-info',
    '.pytest_cache',
    '.mypy_cache',
    '.DS_Store',
]

# ============================================================================
# Logging Configuration
# ============================================================================

# Log settings
LOG_FILE = LOGS_DIR / "insightos.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log rotation
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Log retention
LOG_RETENTION_DAYS = 30

# ============================================================================
# Security Configuration
# ============================================================================

# Encryption settings
ENCRYPTION_ALGORITHM = "Fernet"  # AES-128 CBC + HMAC
KDF_ITERATIONS = 100000  # PBKDF2 iterations
KDF_SALT = b'insightos_salt_v1'  # Static salt (OK for machine-specific encryption)

# File permissions (Unix/macOS)
CONFIG_FILE_PERMISSIONS = 0o600  # rw-------
API_KEY_FILE_PERMISSIONS = 0o600  # rw-------

# Memory safety
CLEAR_SENSITIVE_DATA_FROM_MEMORY = True  # Clear API keys after use

# ============================================================================
# Performance Configuration
# ============================================================================

# Threading settings
MAX_WORKER_THREADS = 4  # For parallel file processing

# Cache settings
ENABLE_EMBEDDING_CACHE = True
EMBEDDING_CACHE_SIZE = 1000  # Number of cached embeddings

# Database settings
CHROMA_PERSIST_DIRECTORY = CHROMA_DIR
CHROMA_COLLECTION_NAME = "insightos_documents"

# ============================================================================
# Feature Flags
# ============================================================================

# Features that can be toggled
ENABLE_FILE_WATCHING = False  # Auto-reindex on file changes (future feature)
ENABLE_CONVERSATION_MEMORY = True  # Remember conversation history
ENABLE_CITATIONS = True  # Show citations in responses
ENABLE_SYSTEM_MONITORING = False  # System monitoring removed from scope
ENABLE_AGENTIC_MODE = False  # (default OFF)

# Experimental features
ENABLE_STREAMING_RESPONSES = False  # Stream LLM responses (future feature)
ENABLE_MULTI_LANGUAGE_SUPPORT = False  # i18n support (future feature)

# ============================================================================
# Validation Limits
# ============================================================================

# API key validation
API_KEY_MIN_LENGTH = 20
API_KEY_MAX_LENGTH = 200
API_KEY_PREFIX = "sk-ant-"

# Directory validation
MAX_MONITORED_DIRECTORIES = 50  # Maximum directories to monitor

# Query validation
MIN_QUERY_LENGTH = 1
MAX_QUERY_LENGTH = 10000

# ============================================================================
# Error Messages
# ============================================================================

ERROR_MESSAGES = {
    'no_api_key': "No API key configured. Please add your Claude API key in Settings.",
    'invalid_api_key': "Invalid API key. Please check your API key in Settings.",
    'no_directories': "No directories monitored. Please add directories to search.",
    'no_files_indexed': "No files have been indexed yet. Please add directories and index them.",
    'indexing_failed': "Indexing failed. Please check the logs for details.",
    'query_failed': "Failed to process query. Please try again.",
    'file_read_error': "Failed to read file. The file may be corrupted or inaccessible.",
    'network_error': "Network error. Please check your internet connection.",
    'rate_limit_error': "API rate limit exceeded. Please wait and try again.",
}

# ============================================================================
# Success Messages
# ============================================================================

SUCCESS_MESSAGES = {
    'api_key_saved': "API key saved successfully.",
    'api_key_validated': "API key validated successfully.",
    'directory_added': "Directory added successfully.",
    'indexing_complete': "Indexing completed successfully.",
    'settings_saved': "Settings saved successfully.",
}

# ============================================================================
# Default Configuration
# ============================================================================

DEFAULT_CONFIG = {
    'top_k': DEFAULT_TOP_K,
    'chunk_size': DEFAULT_CHUNK_SIZE,
    'chunk_overlap': DEFAULT_CHUNK_OVERLAP,
    'monitored_directories': [],
    'file_types_enabled': SUPPORTED_EXTENSIONS,
    'similarity_threshold': DEFAULT_SIMILARITY_THRESHOLD,
    'agentic_mode_enabled': False,  
    'agentic_mode_consent_given': False  
}

# ============================================================================
# Development/Debug Settings
# ============================================================================

DEBUG_MODE = False  # Set to True for development
VERBOSE_LOGGING = False  # Extra detailed logs
SKIP_API_VALIDATION = False  # Skip API key validation (for testing)

# ============================================================================
# Timeouts
# ============================================================================

API_TIMEOUT_SECONDS = 60  # Timeout for API calls
FILE_READ_TIMEOUT_SECONDS = 10  # Timeout for reading large files
INDEXING_TIMEOUT_SECONDS = 300  # Timeout for indexing operation

# ============================================================================
# Helper Functions
# ============================================================================

def is_supported_file(filepath: str) -> bool:
    """
    Check if file extension is supported
    
    Args:
        filepath: Path to file
    
    Returns:
        True if supported, False otherwise
    """
    from pathlib import Path
    return Path(filepath).suffix.lower() in SUPPORTED_EXTENSIONS


def should_skip_directory(dirname: str) -> bool:
    """
    Check if directory should be skipped during indexing
    
    Args:
        dirname: Directory name
    
    Returns:
        True if should skip, False otherwise
    """
    if SKIP_HIDDEN_DIRECTORIES and dirname.startswith('.'):
        return True
    
    return dirname in SKIP_DIRECTORIES


def get_file_category(extension: str) -> str:
    """
    Get category of file based on extension
    
    Args:
        extension: File extension (e.g., '.pdf')
    
    Returns:
        Category name ('document', 'text', 'code', 'web', 'data', 'config', 'unknown')
    """
    extension = extension.lower()
    
    if extension in DOCUMENT_EXTENSIONS:
        return 'document'
    elif extension in TEXT_EXTENSIONS:
        return 'text'
    elif extension in CODE_EXTENSIONS:
        return 'code'
    elif extension in WEB_EXTENSIONS:
        return 'web'
    elif extension in DATA_EXTENSIONS:
        return 'data'
    elif extension in CONFIG_EXTENSIONS:
        return 'config'
    else:
        return 'unknown'


def get_settings_dict() -> dict:
    """
    Get all settings as a dictionary (useful for debugging/export)
    
    Returns:
        Dictionary of all settings
    """
    return {
        'app_name': APP_NAME,
        'app_version': APP_VERSION,
        'directories': {
            'user_data_dir': str(USER_DATA_DIR),
            'config_file': str(CONFIG_FILE),
            'logs_dir': str(LOGS_DIR),
            'chroma_dir': str(CHROMA_DIR),
        },
        'api': {
            'model': CLAUDE_MODEL,
            'max_tokens': CLAUDE_MAX_TOKENS,
            'temperature': CLAUDE_TEMPERATURE,
        },
        'rag': {
            'default_top_k': DEFAULT_TOP_K,
            'chunk_size': DEFAULT_CHUNK_SIZE,
            'chunk_overlap': DEFAULT_CHUNK_OVERLAP,
        },
        'supported_extensions': SUPPORTED_EXTENSIONS,
        'feature_flags': {
            'file_watching': ENABLE_FILE_WATCHING,
            'conversation_memory': ENABLE_CONVERSATION_MEMORY,
            'citations': ENABLE_CITATIONS,
        },
    }