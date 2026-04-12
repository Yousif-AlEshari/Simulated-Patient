"""src.utils.logger

Production-grade logging system for Python/FastAPI/Streamlit application.

Supports two modes (development/production) with rotating file handlers, colored console output,
structured logging, and automatic decorator support.
"""

from __future__ import annotations

import atexit
import functools
import logging
import logging.handlers
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

# ============================================================================
# ANSI Color Codes for Console Output
# ============================================================================

class _ColorCodes:
    """ANSI color codes for log level names."""
    RESET = "\033[0m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    GRAY = "\033[90m"


def _colorize_level(levelname: str) -> str:
    """Return colorized level name with ANSI escape codes."""
    colors = {
        "DEBUG": _ColorCodes.CYAN,
        "INFO": _ColorCodes.GREEN,
        "WARNING": _ColorCodes.YELLOW,
        "ERROR": _ColorCodes.RED,
    }
    color = colors.get(levelname, _ColorCodes.RESET)
    return f"{color}{levelname}{_ColorCodes.RESET}"


# ============================================================================
# Custom Formatters
# ============================================================================

class _ColoredFormatter(logging.Formatter):
    """Formatter that applies ANSI color codes to log levels (development)."""
    def format(self, record: logging.LogRecord) -> str:
        record.levelname = _colorize_level(record.levelname)
        return super().format(record)


class _StructuredFormatter(logging.Formatter):
    """Formatter for structured logging (production, no colors)."""
    def format(self, record: logging.LogRecord) -> str:
        return super().format(record)


# ============================================================================
# Log File Management
# ============================================================================

_log_counter_lock = threading.Lock()


def _get_logs_dir() -> Path:
    """Get or create the logs directory under src/utils/logs/."""
    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def _next_log_file_number() -> int:
    """Scan existing log files and return the next zero-padded number."""
    logs_dir = _get_logs_dir()
    if not logs_dir.exists():
        return 1
    
    # Pattern: app_YYYYMMDD_HHMMSS_NNN.log
    pattern = re.compile(r'app_\d{8}_\d{6}_(\d{3})\.log')
    numbers = []
    
    for file in logs_dir.glob("app_*.log"):
        match = pattern.match(file.name)
        if match:
            try:
                num = int(match.group(1))
                numbers.append(num)
            except (ValueError, IndexError):
                pass
    
    if not numbers:
        return 1
    return max(numbers) + 1


def _get_current_log_file() -> Path:
    """Get the current log file path with timestamp and auto-incrementing counter."""
    with _log_counter_lock:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        counter = _next_log_file_number()
        filename = f"app_{timestamp}_{counter:03d}.log"
        return _get_logs_dir() / filename


# ============================================================================
# Logger Setup (Module-Level Initialization)
# ============================================================================

_setup_complete = False
_setup_lock = threading.Lock()


def _setup_logging() -> None:
    """Configure the root logger with appropriate handlers based on APP_ENV."""
    global _setup_complete
    
    with _setup_lock:
        if _setup_complete:
            return
        
        # Determine environment and log level
        app_env = os.environ.get("APP_ENV", "development").lower()
        is_production = app_env == "production"
        log_level = logging.WARNING if is_production else logging.DEBUG
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove any existing handlers to prevent duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Always add rotating file handler
        log_file = _get_current_log_file()
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)  # File captures all levels
        file_formatter = _StructuredFormatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # In development mode, also add console handler with colors
        if not is_production:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_formatter = _ColoredFormatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Suppress verbose third-party library DEBUG logs to reduce noise
        # These libraries log at DEBUG level for internal operations we don't need to see
        logging.getLogger("pymongo").setLevel(logging.WARNING)
        logging.getLogger("pymongo.topology").setLevel(logging.WARNING)
        logging.getLogger("pymongo.serverSelection").setLevel(logging.WARNING)
        logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
        logging.getLogger("pymongo.command").setLevel(logging.WARNING)
        logging.getLogger("passlib").setLevel(logging.WARNING)
        logging.getLogger("passlib.handlers").setLevel(logging.WARNING)
        logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.WARNING)
        
        _setup_complete = True


# Call setup at module load time (guarded by flag to avoid Streamlit/FastAPI re-imports)
_setup_logging()


# ============================================================================
# Public Logger Factory
# ============================================================================

def get_logger(name: str = "app") -> logging.Logger:
    """Get a logger instance for the given module name.
    
    Args:
        name: Module name (typically __name__). Defaults to "app".
    
    Returns:
        A logging.Logger instance configured for the app.
    """
    return logging.getLogger(name)


# ============================================================================
# Decorator Factory for Automatic Function Logging
# ============================================================================

F = TypeVar("F", bound=Callable[..., Any])


def log_call(func: F) -> F:
    """Decorator that logs function entry, exit, elapsed time, and exceptions.
    
    Logs at DEBUG level for entry/exit, INFO for elapsed time > 1 second,
    and ERROR for any exceptions.
    
    Usage:
        @log_call
        def my_function(x, y):
            return x + y
    """
    logger = get_logger(func.__module__)
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = f"{func.__module__}.{func.__name__}"
        logger.debug(f"→ {func_name} START")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            # Log result summary (truncate long results)
            result_str = repr(result)
            if len(result_str) > 100:
                result_str = result_str[:97] + "..."
            logger.debug(f"← {func_name} END: {result_str}")
            
            # Log elapsed time if over 1 second
            if elapsed > 1:
                logger.info(f"{func_name} completed in {elapsed:.2f}s")
            
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"✗ {func_name} FAILED after {elapsed:.2f}s: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise
    
    return wrapper  # type: ignore


# ============================================================================
# Graceful Shutdown
# ============================================================================

def _shutdown_logging() -> None:
    """Flush and close all handlers on shutdown."""
    logging.shutdown()


atexit.register(_shutdown_logging)
