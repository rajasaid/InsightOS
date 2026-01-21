"""
utils/logger.py
Logging configuration for InsightOS
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


# Log directory
LOG_DIR = Path.home() / ".insightos" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file path
LOG_FILE = LOG_DIR / "insightos.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log level
DEFAULT_LEVEL = logging.INFO


def setup_logger(name: str = "insightos", level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Setup and configure application logger
    
    Args:
        name: Logger name (default: "insightos")
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler (rotating, max 10MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Log startup message
    logger.info("=" * 80)
    logger.info(f"InsightOS Logger initialized - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Log level: {logging.getLevelName(level)}")
    logger.info("=" * 80)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Module initialized")
    """
    if name:
        # Create child logger with module name
        return logging.getLogger(f"insightos.{name}")
    else:
        # Return root logger
        return logging.getLogger("insightos")


def set_log_level(level: int):
    """
    Change log level for all handlers
    
    Args:
        level: New logging level (e.g., logging.DEBUG, logging.INFO)
    
    Example:
        set_log_level(logging.DEBUG)
    """
    logger = logging.getLogger("insightos")
    logger.setLevel(level)
    
    for handler in logger.handlers:
        handler.setLevel(level)
    
    logger.info(f"Log level changed to: {logging.getLevelName(level)}")


def log_exception(logger: logging.Logger, message: str = "An exception occurred"):
    """
    Log exception with full traceback
    
    Args:
        logger: Logger instance
        message: Custom message to log with exception
    
    Example:
        try:
            risky_operation()
        except Exception:
            log_exception(logger, "Failed to perform risky operation")
    """
    logger.exception(message)


def clear_old_logs(days: int = 30):
    """
    Clear log files older than specified days
    
    Args:
        days: Number of days to keep logs (default: 30)
    """
    logger = logging.getLogger("insightos")
    
    try:
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        deleted_count = 0
        for log_file in LOG_DIR.glob("insightos.log.*"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleared {deleted_count} old log files (older than {days} days)")
    
    except Exception as e:
        logger.error(f"Error clearing old logs: {e}")


def log_system_info():
    """
    Log system information for debugging
    """
    import platform
    import sys
    
    logger = logging.getLogger("insightos")
    
    logger.info("System Information:")
    logger.info(f"  Platform: {platform.platform()}")
    logger.info(f"  Python: {sys.version}")
    logger.info(f"  Architecture: {platform.machine()}")
    logger.info(f"  Processor: {platform.processor()}")


def sanitize_log_message(message: str, sensitive_patterns: list = None) -> str:
    """
    Sanitize log message to remove sensitive information
    
    Args:
        message: Original log message
        sensitive_patterns: List of patterns to redact (default: API keys, tokens)
    
    Returns:
        Sanitized message
    
    Example:
        msg = sanitize_log_message("API key: sk-ant-12345")
        # Returns: "API key: sk-***REDACTED***"
    """
    import re
    
    if sensitive_patterns is None:
        sensitive_patterns = [
            r'sk-ant-[a-zA-Z0-9]+',  # Claude API keys
            r'api[_-]?key["\s:=]+[a-zA-Z0-9]+',  # Generic API keys
            r'token["\s:=]+[a-zA-Z0-9]+',  # Tokens
            r'password["\s:=]+[^\s]+',  # Passwords
        ]
    
    sanitized = message
    for pattern in sensitive_patterns:
        sanitized = re.sub(pattern, '***REDACTED***', sanitized, flags=re.IGNORECASE)
    
    return sanitized


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter to automatically sanitize sensitive data
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to sanitize sensitive data
        
        Args:
            record: Log record to filter
        
        Returns:
            True (always allow record through, just sanitize it)
        """
        # Sanitize the message
        record.msg = sanitize_log_message(str(record.msg))
        
        # Sanitize args if present
        if record.args:
            sanitized_args = tuple(
                sanitize_log_message(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
            record.args = sanitized_args
        
        return True


def add_sensitive_data_filter():
    """
    Add sensitive data filter to all handlers
    
    Example:
        add_sensitive_data_filter()
        logger.info("API key: sk-ant-12345")  # Will be redacted automatically
    """
    logger = logging.getLogger("insightos")
    sensitive_filter = SensitiveDataFilter()
    
    for handler in logger.handlers:
        handler.addFilter(sensitive_filter)
    
    logger.info("Sensitive data filter enabled")


# Performance logging helpers

class LogExecutionTime:
    """
    Context manager to log execution time of code blocks
    
    Example:
        with LogExecutionTime(logger, "indexing operation"):
            index_documents()
    """
    
    def __init__(self, logger: logging.Logger, operation_name: str):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation_name} (took {elapsed:.2f}s)")
        else:
            self.logger.error(f"Failed: {self.operation_name} (after {elapsed:.2f}s)")
        
        return False  # Don't suppress exceptions


def log_function_call(logger: logging.Logger = None):
    """
    Decorator to log function calls with arguments and return values
    
    Args:
        logger: Logger instance (optional, will use function's module logger)
    
    Example:
        @log_function_call()
        def my_function(arg1, arg2):
            return arg1 + arg2
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get logger
            func_logger = logger or get_logger(func.__module__)
            
            # Log function call
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            
            func_logger.debug(f"Calling {func.__name__}({signature})")
            
            try:
                result = func(*args, **kwargs)
                func_logger.debug(f"{func.__name__} returned: {result!r}")
                return result
            except Exception as e:
                func_logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        
        return wrapper
    return decorator


# Export commonly used items
__all__ = [
    'setup_logger',
    'get_logger',
    'set_log_level',
    'log_exception',
    'clear_old_logs',
    'log_system_info',
    'sanitize_log_message',
    'add_sensitive_data_filter',
    'SensitiveDataFilter',
    'LogExecutionTime',
    'log_function_call',
]