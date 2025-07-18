"""
Symposia Logging - Central logging configuration for the Symposia framework.

This module provides a unified logging configuration for use across the application.
"""

import logging
import sys

# Default formatter
DEFAULT_FORMAT = '%(message)s'
DEBUG_FORMAT = '%(levelname)s - %(name)s - %(message)s'

def setup_logging(verbose=False, name=None):
    """
    Setup logging configuration for the application.
    
    Args:
        verbose (bool): If True, use DEBUG level and more detailed format
        name (str): Optional logger name to return. If None, returns root logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to prevent duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(DEBUG_FORMAT if verbose else DEFAULT_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Return specific logger if name provided
    if name:
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        return logger
    
    return root_logger
