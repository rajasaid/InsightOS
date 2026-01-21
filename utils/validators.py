"""
utils/validators.py
Input validation helpers for InsightOS
"""

import re
from pathlib import Path
from typing import Optional, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


# ============================================================================
# API Key Validation
# ============================================================================

def validate_api_key_format(api_key: str) -> Tuple[bool, Optional[str]]:
    """
    Validate API key format (structure only, not actual validity)
    
    Args:
        api_key: API key string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, "error message") if invalid
    
    Example:
        is_valid, error = validate_api_key_format("sk-ant-...")
        if not is_valid:
            print(error)
    """
    if not api_key:
        return False, "API key cannot be empty"
    
    api_key = api_key.strip()
    
    # Check minimum length
    if len(api_key) < 20:
        return False, "API key is too short (minimum 20 characters)"
    
    # Check maximum length (reasonable limit)
    if len(api_key) > 200:
        return False, "API key is too long (maximum 200 characters)"
    
    # Check for Claude API key pattern (sk-ant-...)
    if not api_key.startswith("sk-ant-"):
        return False, "API key must start with 'sk-ant-' (Claude API key format)"
    
    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^sk-ant-[a-zA-Z0-9_-]+$', api_key):
        return False, "API key contains invalid characters"
    
    # Check for whitespace
    if ' ' in api_key or '\t' in api_key or '\n' in api_key:
        return False, "API key cannot contain whitespace"
    
    return True, None


def is_valid_api_key_format(api_key: str) -> bool:
    """
    Check if API key format is valid (convenience wrapper)
    
    Args:
        api_key: API key string to validate
    
    Returns:
        True if valid format, False otherwise
    """
    is_valid, _ = validate_api_key_format(api_key)
    return is_valid


# ============================================================================
# File Path Validation
# ============================================================================

def validate_file_path(filepath: str, must_exist: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate file path
    
    Args:
        filepath: File path to validate
        must_exist: If True, file must exist on disk
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filepath:
        return False, "File path cannot be empty"
    
    filepath = filepath.strip()
    
    try:
        path = Path(filepath)
        
        # Check for invalid characters (OS-specific)
        # These are generally invalid on most systems
        invalid_chars = ['<', '>', '|', '\0']
        if any(char in str(path) for char in invalid_chars):
            return False, "File path contains invalid characters"
        
        # Check if path is absolute (recommended)
        if not path.is_absolute():
            logger.warning(f"File path is not absolute: {filepath}")
        
        # Check if file exists (if required)
        if must_exist:
            if not path.exists():
                return False, f"File does not exist: {filepath}"
            
            if not path.is_file():
                return False, f"Path is not a file: {filepath}"
        
        return True, None
    
    except Exception as e:
        return False, f"Invalid file path: {str(e)}"


def validate_directory_path(dirpath: str, must_exist: bool = False, must_be_readable: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate directory path
    
    Args:
        dirpath: Directory path to validate
        must_exist: If True, directory must exist
        must_be_readable: If True, directory must be readable
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not dirpath:
        return False, "Directory path cannot be empty"
    
    dirpath = dirpath.strip()
    
    try:
        path = Path(dirpath)
        
        # Check for invalid characters
        invalid_chars = ['<', '>', '|', '\0']
        if any(char in str(path) for char in invalid_chars):
            return False, "Directory path contains invalid characters"
        
        # Check if path is absolute
        if not path.is_absolute():
            logger.warning(f"Directory path is not absolute: {dirpath}")
        
        # Check if directory exists (if required)
        if must_exist:
            if not path.exists():
                return False, f"Directory does not exist: {dirpath}"
            
            if not path.is_dir():
                return False, f"Path is not a directory: {dirpath}"
            
            # Check if readable
            if must_be_readable:
                try:
                    list(path.iterdir())
                except PermissionError:
                    return False, f"Directory is not readable: {dirpath}"
        
        return True, None
    
    except Exception as e:
        return False, f"Invalid directory path: {str(e)}"


def is_supported_file_type(filepath: str, supported_extensions: list) -> bool:
    """
    Check if file has a supported extension
    
    Args:
        filepath: File path to check
        supported_extensions: List of supported extensions (e.g., ['.txt', '.pdf'])
    
    Returns:
        True if supported, False otherwise
    """
    path = Path(filepath)
    extension = path.suffix.lower()
    
    # Normalize supported extensions (ensure lowercase and leading dot)
    normalized_extensions = [
        ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
        for ext in supported_extensions
    ]
    
    return extension in normalized_extensions


# ============================================================================
# Configuration Validation
# ============================================================================

def validate_top_k(top_k: int) -> Tuple[bool, Optional[str]]:
    """
    Validate top_k parameter for RAG retrieval
    
    Args:
        top_k: Number of results to retrieve
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(top_k, int):
        return False, "top_k must be an integer"
    
    if top_k < 1:
        return False, "top_k must be at least 1"
    
    if top_k > 20:
        return False, "top_k cannot exceed 20 (too many results may reduce quality)"
    
    return True, None


def validate_chunk_size(chunk_size: int) -> Tuple[bool, Optional[str]]:
    """
    Validate chunk size for text chunking
    
    Args:
        chunk_size: Chunk size in characters
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(chunk_size, int):
        return False, "Chunk size must be an integer"
    
    if chunk_size < 100:
        return False, "Chunk size must be at least 100 characters"
    
    if chunk_size > 5000:
        return False, "Chunk size cannot exceed 5000 characters"
    
    return True, None


def validate_chunk_overlap(chunk_overlap: int, chunk_size: int = None) -> Tuple[bool, Optional[str]]:
    """
    Validate chunk overlap for text chunking
    
    Args:
        chunk_overlap: Chunk overlap in characters
        chunk_size: Chunk size (optional, for additional validation)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(chunk_overlap, int):
        return False, "Chunk overlap must be an integer"
    
    if chunk_overlap < 0:
        return False, "Chunk overlap cannot be negative"
    
    if chunk_overlap > 1000:
        return False, "Chunk overlap cannot exceed 1000 characters"
    
    # If chunk_size provided, ensure overlap is smaller
    if chunk_size is not None:
        if chunk_overlap >= chunk_size:
            return False, "Chunk overlap must be smaller than chunk size"
    
    return True, None


def validate_config(config: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate configuration dictionary
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(config, dict):
        return False, "Configuration must be a dictionary"
    
    # Validate top_k if present
    if 'top_k' in config:
        is_valid, error = validate_top_k(config['top_k'])
        if not is_valid:
            return False, f"Invalid top_k: {error}"
    
    # Validate chunk_size if present
    if 'chunk_size' in config:
        is_valid, error = validate_chunk_size(config['chunk_size'])
        if not is_valid:
            return False, f"Invalid chunk_size: {error}"
    
    # Validate chunk_overlap if present
    if 'chunk_overlap' in config:
        chunk_size = config.get('chunk_size')
        is_valid, error = validate_chunk_overlap(config['chunk_overlap'], chunk_size)
        if not is_valid:
            return False, f"Invalid chunk_overlap: {error}"
    
    # Validate monitored_directories if present
    if 'monitored_directories' in config:
        if not isinstance(config['monitored_directories'], list):
            return False, "monitored_directories must be a list"
        
        for directory in config['monitored_directories']:
            is_valid, error = validate_directory_path(directory, must_exist=False)
            if not is_valid:
                return False, f"Invalid directory: {error}"
    
    # Validate file_types_enabled if present
    if 'file_types_enabled' in config:
        if not isinstance(config['file_types_enabled'], list):
            return False, "file_types_enabled must be a list"
        
        for ext in config['file_types_enabled']:
            if not isinstance(ext, str):
                return False, f"File extension must be string: {ext}"
            if not ext.startswith('.'):
                return False, f"File extension must start with '.': {ext}"
    
    return True, None


# ============================================================================
# Text/String Validation
# ============================================================================

def validate_query(query: str, min_length: int = 1, max_length: int = 10000) -> Tuple[bool, Optional[str]]:
    """
    Validate user query
    
    Args:
        query: User query string
        min_length: Minimum query length
        max_length: Maximum query length
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query:
        return False, "Query cannot be empty"
    
    query = query.strip()
    
    if len(query) < min_length:
        return False, f"Query must be at least {min_length} characters"
    
    if len(query) > max_length:
        return False, f"Query cannot exceed {max_length} characters"
    
    # Check for suspicious patterns (basic injection prevention)
    suspicious_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers (onclick, onload, etc.)
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Query contains potentially unsafe content"
    
    return True, None


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
    
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = r'[<>:"|?*\\/\0]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Truncate to max length
    if len(sanitized) > max_length:
        # Preserve extension if present
        path = Path(sanitized)
        if path.suffix:
            stem = path.stem[:max_length - len(path.suffix) - 1]
            sanitized = f"{stem}{path.suffix}"
        else:
            sanitized = sanitized[:max_length]
    
    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized


# ============================================================================
# Numeric Validation
# ============================================================================

def validate_range(value: float, min_val: float, max_val: float, name: str = "Value") -> Tuple[bool, Optional[str]]:
    """
    Validate that a numeric value is within a range
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the value (for error messages)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, (int, float)):
        return False, f"{name} must be a number"
    
    if value < min_val:
        return False, f"{name} must be at least {min_val}"
    
    if value > max_val:
        return False, f"{name} cannot exceed {max_val}"
    
    return True, None


# ============================================================================
# Batch Validation
# ============================================================================

def validate_all(validators: list) -> Tuple[bool, list]:
    """
    Run multiple validators and collect all errors
    
    Args:
        validators: List of (validator_func, *args) tuples
    
    Returns:
        Tuple of (all_valid, error_messages_list)
    
    Example:
        validators = [
            (validate_api_key_format, api_key),
            (validate_top_k, top_k),
            (validate_chunk_size, chunk_size),
        ]
        is_valid, errors = validate_all(validators)
    """
    errors = []
    
    for validator_func, *args in validators:
        is_valid, error = validator_func(*args)
        if not is_valid:
            errors.append(error)
    
    return len(errors) == 0, errors


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'ValidationError',
    'validate_api_key_format',
    'is_valid_api_key_format',
    'validate_file_path',
    'validate_directory_path',
    'is_supported_file_type',
    'validate_top_k',
    'validate_chunk_size',
    'validate_chunk_overlap',
    'validate_config',
    'validate_query',
    'sanitize_filename',
    'validate_range',
    'validate_all',
]