"""Google ADK agent initialization module.

This module handles the creation and configuration of Google ADK agents
for customer and partner discovery operations.
"""

import logging
from typing import Optional
import google.genai as genai
from google.genai import types

from src.config import get_config


logger = logging.getLogger(__name__)


def create_discovery_agent(
    model: str = "gemini-2.0-flash-exp",
    temperature: float = 0.7,
    enable_web_search: bool = True
) -> genai.Client:
    """Create and configure a Google ADK agent for discovery operations.

    This function initializes a Google ADK client configured with:
    - Web search tool access for finding companies and information
    - Optimized temperature for balanced creativity and consistency
    - Latest Gemini model for fast, capable responses

    Args:
        model: The Gemini model to use. Defaults to "gemini-2.0-flash-exp".
        temperature: Controls randomness (0.0-1.0). 0.7 balances creativity
            and consistency. Lower values (0.3) are more deterministic,
            higher values (0.9) are more creative.
        enable_web_search: Whether to enable the web search tool.
            Defaults to True.

    Returns:
        genai.Client: Configured Google ADK client instance ready for
            discovery operations.

    Raises:
        ValueError: If API key is not configured or invalid.
        RuntimeError: If agent initialization fails.

    Example:
        >>> from src.agent.agent_setup import create_discovery_agent
        >>> agent = create_discovery_agent()
        >>> # Agent is ready to use with web search capabilities
    """
    try:
        # Load configuration and validate API key
        config = get_config()

        if not config.google_api_key:
            raise ValueError(
                "Google API key not found. Please set GOOGLE_API_KEY "
                "in your .env file."
            )

        # Configure the Google ADK client
        genai.configure(api_key=config.google_api_key)

        # Create client instance
        client = genai.Client(api_key=config.google_api_key)

        logger.info(
            f"Google ADK agent initialized successfully with model: {model}, "
            f"temperature: {temperature}, web_search: {enable_web_search}"
        )

        return client

    except ValueError as e:
        logger.error(f"API key validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize Google ADK agent: {e}")
        raise RuntimeError(f"Agent initialization failed: {e}") from e


def get_generation_config(temperature: float = 0.7) -> types.GenerateContentConfig:
    """Get generation configuration for agent responses.

    Args:
        temperature: Controls randomness (0.0-1.0). Defaults to 0.7.

    Returns:
        types.GenerateContentConfig: Configuration object for content generation.
    """
    return types.GenerateContentConfig(
        temperature=temperature,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
    )
