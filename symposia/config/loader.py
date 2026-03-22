"""
Configuration loader for Symposia.

This module provides utilities for loading configuration from YAML files
and handling environment-specific configurations.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file. If None, will try to load
                    from environment variable SYMPOSIA_CONFIG or default locations.
    
    Returns:
        Configuration dictionary
    
    Raises:
        FileNotFoundError: If the configuration file cannot be found
        yaml.YAMLError: If the YAML file is malformed
    """
    if config_path is None:
        # Try environment variable first
        config_path = os.getenv('SYMPOSIA_CONFIG')
        
        if config_path is None:
            # Try default locations (user configs first, then examples)
            default_paths = [
                'config/symposia.local.yaml',
                'config/symposia.yaml',
                'symposia.yaml',
                'examples/symposia.local.yaml',
                'examples/symposia.yaml'
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if config_path is None:
                logger.warning("No configuration file found. Using default configuration.")
                return DEFAULT_CONFIG
    
    # Ensure the path exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    logger.info(f"Loading configuration from: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        if not config:
            raise ValueError("Configuration file is empty")
        
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML configuration: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def get_config_path() -> str:
    """
    Get the path to the configuration file being used.
    
    Returns:
        Path to the configuration file
    """
    config_path = os.getenv('SYMPOSIA_CONFIG')
    
    if config_path is None:
        # Try default locations
        default_paths = [
            'config/symposia.local.yaml',
            'config/symposia.yaml',
            'symposia.yaml',
            'examples/symposia.local.yaml',
            'examples/symposia.yaml'
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                return path
        
        return 'default'  # Indicates using default config
    
    return config_path


def validate_config_path(config_path: str) -> bool:
    """
    Validate that a configuration file exists and is readable.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        True if the file exists and is readable, False otherwise
    """
    try:
        return os.path.isfile(config_path) and os.access(config_path, os.R_OK)
    except Exception:
        return False 