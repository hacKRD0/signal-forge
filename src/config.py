"""Configuration module for Customer & Partner Discovery Prototype.

This module handles loading environment variables and providing
centralized configuration for the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Application configuration class.

    Loads configuration from environment variables and provides
    validation for required settings.
    """

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load environment variables from .env file if it exists
        load_dotenv()

        # API Configuration
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        if not self.google_api_key or self.google_api_key == 'your_api_key_here':
            raise ValueError(
                "GOOGLE_API_KEY must be set in .env file. "
                "Copy .env.example to .env and add your API key."
            )

        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # Directory Paths
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / os.getenv('DATA_DIR', 'data')
        self.logs_dir = self.project_root / 'logs'

        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def __repr__(self):
        """String representation of configuration (without exposing API key)."""
        return (
            f"Config(log_level='{self.log_level}', "
            f"data_dir='{self.data_dir}', "
            f"logs_dir='{self.logs_dir}')"
        )


# Singleton instance
_config = None


def get_config() -> Config:
    """Get or create the configuration singleton instance.

    Returns:
        Config: The application configuration instance.

    Raises:
        ValueError: If required environment variables are not set.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


# Example usage:
# from src.config import get_config
# config = get_config()
# print(config.google_api_key)
