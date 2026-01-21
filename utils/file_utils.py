"""
utils/file_utils.py
File system utilities for InsightOS
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# File/Directory Existence & Permissions
# ============================================================================

def ensure_directory_exists(directory: Path) -> bool:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        directory: Path to directory
    
    Returns:
        True if directory exists or was created successfully
    """
    try:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        return False


def is_readable(path: Path) -> bool:
    """
    Check if path is readable
    
    Args:
        path: Path to check
    
    Returns:
        True if readable, False otherwise
    """
    try:
        path = Path(path)
        return os.access(path, os.R_OK)
    except Exception:
        return False


def is_writable(path: Path) -> bool:
    """
    Check if path is writable
    
    Args:
        path: Path to check
    
    Returns:
        True if writable, False otherwise
    """
    try:
        path = Path(path)
        return os.access(path, os.W_OK)
    except Exception:
        return False


def get_file_permissions(filepath: Path) -> str:
    """
    Get file permissions in octal format (e.g., '0644')
    
    Args:
        filepath: Path to file
    
    Returns:
        Permissions string in octal format
    """
    try:
        filepath = Path(filepath)
        stat_info = filepath.stat()
        return oct(stat_info.st_mode)[-3:]
    except Exception as e:
        logger.error(f"Failed to get permissions for {filepath}: {e}")
        return "unknown"


def set_file_permissions(filepath: Path, mode: int) -> bool:
    """
    Set file permissions
    
    Args:
        filepath: Path to file
        mode: Permission mode (e.g., 0o600 for rw-------)
    
    Returns:
        True if successful, False otherwise
    
    Example:
        set_file_permissions("config.json", 0o600)  # Read/write for owner only
    """
    try:
        filepath = Path(filepath)
        os.chmod(filepath, mode)
        logger.debug(f"Set permissions {oct(mode)} on {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to set permissions on {filepath}: {e}")
        return False


# ============================================================================
# File Information
# ============================================================================

def get_file_size(filepath: Path, human_readable: bool = False) -> str:
    """
    Get file size
    
    Args:
        filepath: Path to file
        human_readable: If True, return human-readable format (e.g., "1.5 MB")
    
    Returns:
        File size as string
    """
    try:
        filepath = Path(filepath)
        size_bytes = filepath.stat().st_size
        
        if not human_readable:
            return str(size_bytes)
        
        # Convert to human-readable format
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} PB"
    
    except Exception as e:
        logger.error(f"Failed to get size of {filepath}: {e}")
        return "unknown"


def get_file_modified_time(filepath: Path) -> Optional[datetime]:
    """
    Get file modification time
    
    Args:
        filepath: Path to file
    
    Returns:
        datetime object or None if error
    """
    try:
        filepath = Path(filepath)
        timestamp = filepath.stat().st_mtime
        return datetime.fromtimestamp(timestamp)
    except Exception as e:
        logger.error(f"Failed to get modification time for {filepath}: {e}")
        return None


def get_file_created_time(filepath: Path) -> Optional[datetime]:
    """
    Get file creation time (or metadata change time on Unix)
    
    Args:
        filepath: Path to file
    
    Returns:
        datetime object or None if error
    """
    try:
        filepath = Path(filepath)
        timestamp = filepath.stat().st_ctime
        return datetime.fromtimestamp(timestamp)
    except Exception as e:
        logger.error(f"Failed to get creation time for {filepath}: {e}")
        return None


def get_file_extension(filepath: Path) -> str:
    """
    Get file extension (lowercase, with dot)
    
    Args:
        filepath: Path to file
    
    Returns:
        File extension (e.g., ".txt", ".pdf")
    """
    filepath = Path(filepath)
    return filepath.suffix.lower()


def get_filename_without_extension(filepath: Path) -> str:
    """
    Get filename without extension
    
    Args:
        filepath: Path to file
    
    Returns:
        Filename without extension
    """
    filepath = Path(filepath)
    return filepath.stem


# ============================================================================
# File Operations
# ============================================================================

def copy_file(src: Path, dst: Path, overwrite: bool = False) -> bool:
    """
    Copy file from source to destination
    
    Args:
        src: Source file path
        dst: Destination file path
        overwrite: If True, overwrite existing file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        src = Path(src)
        dst = Path(dst)
        
        if not src.exists():
            logger.error(f"Source file does not exist: {src}")
            return False
        
        if dst.exists() and not overwrite:
            logger.warning(f"Destination file already exists: {dst}")
            return False
        
        # Ensure destination directory exists
        ensure_directory_exists(dst.parent)
        
        shutil.copy2(src, dst)
        logger.info(f"Copied file: {src} -> {dst}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to copy file {src} to {dst}: {e}")
        return False


def move_file(src: Path, dst: Path, overwrite: bool = False) -> bool:
    """
    Move file from source to destination
    
    Args:
        src: Source file path
        dst: Destination file path
        overwrite: If True, overwrite existing file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        src = Path(src)
        dst = Path(dst)
        
        if not src.exists():
            logger.error(f"Source file does not exist: {src}")
            return False
        
        if dst.exists() and not overwrite:
            logger.warning(f"Destination file already exists: {dst}")
            return False
        
        # Ensure destination directory exists
        ensure_directory_exists(dst.parent)
        
        shutil.move(str(src), str(dst))
        logger.info(f"Moved file: {src} -> {dst}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to move file {src} to {dst}: {e}")
        return False


def delete_file(filepath: Path, confirm: bool = True) -> bool:
    """
    Delete file
    
    Args:
        filepath: Path to file
        confirm: If True, only delete if file exists (safer)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        filepath = Path(filepath)
        
        if confirm and not filepath.exists():
            logger.warning(f"File does not exist, cannot delete: {filepath}")
            return False
        
        filepath.unlink()
        logger.info(f"Deleted file: {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to delete file {filepath}: {e}")
        return False


def delete_directory(dirpath: Path, recursive: bool = False) -> bool:
    """
    Delete directory
    
    Args:
        dirpath: Path to directory
        recursive: If True, delete directory and all contents
    
    Returns:
        True if successful, False otherwise
    """
    try:
        dirpath = Path(dirpath)
        
        if not dirpath.exists():
            logger.warning(f"Directory does not exist, cannot delete: {dirpath}")
            return False
        
        if recursive:
            shutil.rmtree(dirpath)
            logger.info(f"Deleted directory recursively: {dirpath}")
        else:
            dirpath.rmdir()  # Only works if empty
            logger.info(f"Deleted empty directory: {dirpath}")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to delete directory {dirpath}: {e}")
        return False


# ============================================================================
# File Discovery & Listing
# ============================================================================

def list_files_in_directory(
    directory: Path,
    extensions: Optional[List[str]] = None,
    recursive: bool = False,
    include_hidden: bool = False
) -> List[Path]:
    """
    List files in directory with optional filtering
    
    Args:
        directory: Directory to search
        extensions: List of extensions to filter (e.g., ['.txt', '.pdf'])
        recursive: If True, search subdirectories
        include_hidden: If True, include hidden files (starting with '.')
    
    Returns:
        List of file paths
    """
    try:
        directory = Path(directory)
        
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            return []
        
        if not directory.is_dir():
            logger.error(f"Path is not a directory: {directory}")
            return []
        
        files = []
        
        # Determine search pattern
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        # Iterate through files
        for path in directory.glob(pattern):
            # Skip directories
            if not path.is_file():
                continue
            
            # Skip hidden files if requested
            if not include_hidden and path.name.startswith('.'):
                continue
            
            # Filter by extension if specified
            if extensions:
                normalized_extensions = [
                    ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                    for ext in extensions
                ]
                if path.suffix.lower() not in normalized_extensions:
                    continue
            
            files.append(path)
        
        logger.debug(f"Found {len(files)} files in {directory}")
        return files
    
    except Exception as e:
        logger.error(f"Failed to list files in {directory}: {e}")
        return []


def count_files_in_directory(
    directory: Path,
    extensions: Optional[List[str]] = None,
    recursive: bool = False
) -> int:
    """
    Count files in directory
    
    Args:
        directory: Directory to count files in
        extensions: List of extensions to filter
        recursive: If True, count in subdirectories
    
    Returns:
        Number of files
    """
    files = list_files_in_directory(directory, extensions, recursive)
    return len(files)


def get_directory_size(directory: Path) -> Tuple[int, str]:
    """
    Get total size of directory (recursive)
    
    Args:
        directory: Directory to measure
    
    Returns:
        Tuple of (size_in_bytes, human_readable_size)
    """
    try:
        directory = Path(directory)
        total_size = 0
        
        for path in directory.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        
        # Convert to human-readable
        size_bytes = total_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                human_readable = f"{size_bytes:.1f} {unit}"
                break
            size_bytes /= 1024.0
        else:
            human_readable = f"{size_bytes:.1f} PB"
        
        return total_size, human_readable
    
    except Exception as e:
        logger.error(f"Failed to get size of directory {directory}: {e}")
        return 0, "0 B"


# ============================================================================
# Path Utilities
# ============================================================================

def make_relative_path(path: Path, base_path: Path) -> Path:
    """
    Make path relative to base path
    
    Args:
        path: Absolute path to make relative
        base_path: Base path
    
    Returns:
        Relative path
    """
    try:
        path = Path(path).resolve()
        base_path = Path(base_path).resolve()
        return path.relative_to(base_path)
    except ValueError:
        # Paths don't share a common base
        return path


def expand_user_path(path: str) -> Path:
    """
    Expand ~ and environment variables in path
    
    Args:
        path: Path string potentially containing ~ or env vars
    
    Returns:
        Expanded Path object
    """
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return Path(path)


def get_safe_filename(filename: str, replacement: str = "_") -> str:
    """
    Get safe filename by replacing invalid characters
    
    Args:
        filename: Original filename
        replacement: Character to replace invalid chars with
    
    Returns:
        Safe filename
    """
    import re
    
    # Remove invalid characters for most filesystems
    invalid_chars = r'[<>:"|?*\\/\0]'
    safe_name = re.sub(invalid_chars, replacement, filename)
    
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    
    # Ensure not empty
    if not safe_name:
        safe_name = "unnamed"
    
    return safe_name


def is_descendant_path(path: Path, parent: Path) -> bool:
    """
    Check if path is a descendant of parent directory
    
    Args:
        path: Path to check
        parent: Parent directory
    
    Returns:
        True if path is under parent, False otherwise
    """
    try:
        path = Path(path).resolve()
        parent = Path(parent).resolve()
        
        # Check if path starts with parent
        return path.is_relative_to(parent)
    except Exception:
        return False


# ============================================================================
# Temporary Files
# ============================================================================

def create_temp_file(suffix: str = "", prefix: str = "insightos_", directory: Optional[Path] = None) -> Path:
    """
    Create temporary file
    
    Args:
        suffix: File suffix (e.g., ".txt")
        prefix: File prefix
        directory: Directory to create temp file in (default: system temp)
    
    Returns:
        Path to temporary file
    """
    import tempfile
    
    try:
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=directory)
        os.close(fd)  # Close file descriptor
        logger.debug(f"Created temporary file: {path}")
        return Path(path)
    except Exception as e:
        logger.error(f"Failed to create temporary file: {e}")
        raise


def create_temp_directory(prefix: str = "insightos_", directory: Optional[Path] = None) -> Path:
    """
    Create temporary directory
    
    Args:
        prefix: Directory prefix
        directory: Parent directory (default: system temp)
    
    Returns:
        Path to temporary directory
    """
    import tempfile
    
    try:
        path = tempfile.mkdtemp(prefix=prefix, dir=directory)
        logger.debug(f"Created temporary directory: {path}")
        return Path(path)
    except Exception as e:
        logger.error(f"Failed to create temporary directory: {e}")
        raise


# ============================================================================
# File Content Operations
# ============================================================================

def read_text_file(filepath: Path, encoding: str = 'utf-8', errors: str = 'replace') -> Optional[str]:
    """
    Read text file with error handling
    
    Args:
        filepath: Path to file
        encoding: Text encoding
        errors: How to handle encoding errors ('strict', 'ignore', 'replace')
    
    Returns:
        File contents as string, or None if error
    """
    try:
        filepath = Path(filepath)
        return filepath.read_text(encoding=encoding, errors=errors)
    except Exception as e:
        logger.error(f"Failed to read file {filepath}: {e}")
        return None


def write_text_file(filepath: Path, content: str, encoding: str = 'utf-8') -> bool:
    """
    Write text file with error handling
    
    Args:
        filepath: Path to file
        content: Content to write
        encoding: Text encoding
    
    Returns:
        True if successful, False otherwise
    """
    try:
        filepath = Path(filepath)
        ensure_directory_exists(filepath.parent)
        filepath.write_text(content, encoding=encoding)
        logger.debug(f"Wrote text file: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to write file {filepath}: {e}")
        return False


def read_binary_file(filepath: Path) -> Optional[bytes]:
    """
    Read binary file
    
    Args:
        filepath: Path to file
    
    Returns:
        File contents as bytes, or None if error
    """
    try:
        filepath = Path(filepath)
        return filepath.read_bytes()
    except Exception as e:
        logger.error(f"Failed to read binary file {filepath}: {e}")
        return None


def write_binary_file(filepath: Path, content: bytes) -> bool:
    """
    Write binary file
    
    Args:
        filepath: Path to file
        content: Content to write (bytes)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        filepath = Path(filepath)
        ensure_directory_exists(filepath.parent)
        filepath.write_bytes(content)
        logger.debug(f"Wrote binary file: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to write binary file {filepath}: {e}")
        return False


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'ensure_directory_exists',
    'is_readable',
    'is_writable',
    'get_file_permissions',
    'set_file_permissions',
    'get_file_size',
    'get_file_modified_time',
    'get_file_created_time',
    'get_file_extension',
    'get_filename_without_extension',
    'copy_file',
    'move_file',
    'delete_file',
    'delete_directory',
    'list_files_in_directory',
    'count_files_in_directory',
    'get_directory_size',
    'make_relative_path',
    'expand_user_path',
    'get_safe_filename',
    'is_descendant_path',
    'create_temp_file',
    'create_temp_directory',
    'read_text_file',
    'write_text_file',
    'read_binary_file',
    'write_binary_file',
]