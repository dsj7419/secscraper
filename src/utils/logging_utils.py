"""
Logging configuration and utilities for the SEC Earnings Scraper.
"""
import logging
import sys
from functools import wraps
from pathlib import Path
from typing import Any, Callable
from datetime import datetime

from config.settings import get_settings

settings = get_settings()


def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: The name of the logger, typically __name__
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)
    
    if not logger.handlers:
        # Create handlers
        log_file = settings.LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Create formatter
        formatter = logging.Formatter(settings.LOG_FORMAT)
        
        # Set formatter and level
        for handler in (file_handler, console_handler):
            handler.setFormatter(formatter)
            handler.setLevel(settings.LOG_LEVEL)
            logger.addHandler(handler)
    
    return logger


def log_execution_time(logger: logging.Logger) -> Callable:
    """
    Decorator to log function execution time.
    
    Args:
        logger: Logger instance to use for logging
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.debug(
                    f"Function {func.__name__} executed in {duration:.2f} seconds"
                )
                return result
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.error(
                    f"Function {func.__name__} failed after {duration:.2f} seconds: {str(e)}"
                )
                raise
        return wrapper
    return decorator


def log_api_call(logger: logging.Logger) -> Callable:
    """
    Decorator to log API calls with their parameters.
    
    Args:
        logger: Logger instance to use for logging
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info(f"API call to {func.__name__} started")
            logger.debug(f"Parameters: args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"API call to {func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"API call to {func.__name__} failed: {str(e)}")
                raise
        return wrapper
    return decorator