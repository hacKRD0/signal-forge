"""Error handling and user feedback for discovery operations.

This module provides error handling utilities for displaying user-friendly
error messages and providing actionable guidance when discovery fails.
"""

import logging
import streamlit as st
from typing import Optional

logger = logging.getLogger(__name__)


def handle_discovery_error(error: Exception, entity_type: Optional[str] = None) -> None:
    """Display user-friendly error messages based on error type.

    This function checks the error type and displays an appropriate,
    user-friendly error message with actionable guidance. Full error
    details are logged for debugging.

    Args:
        error: The exception that occurred during discovery
        entity_type: Optional entity type being discovered (Customer/Partner)

    Example:
        >>> try:
        ...     result = run_discovery("Customer", context)
        ... except Exception as e:
        ...     handle_discovery_error(e, "Customer")
    """
    # Log full error details for debugging
    logger.error(f"Discovery error: {error}", exc_info=True)

    # Determine error type and provide appropriate message
    error_message = str(error).lower()

    if "api" in error_message or "401" in error_message or "403" in error_message:
        # API authentication/authorization error
        st.error(
            "API Configuration Error",
            icon="⚠️"
        )
        st.markdown(
            """
            The API key may be missing or invalid.

            **What to do:**
            1. Check that `.env` file has `GOOGLE_API_KEY` set
            2. Verify the API key is valid and hasn't expired
            3. Ensure the key has access to Google Search API
            4. Restart the application after updating `.env`
            """
        )

    elif "network" in error_message or "timeout" in error_message or "connection" in error_message:
        # Network/connection error
        st.error(
            "Connection Error",
            icon="🌐"
        )
        st.markdown(
            """
            Unable to connect to external services.

            **What to do:**
            1. Check your internet connection
            2. Verify network access to external APIs
            3. Try again in a moment (may be temporary)
            4. If problem persists, check firewall/proxy settings
            """
        )

    elif "parsing" in error_message or "json" in error_message:
        # Data parsing error
        st.error(
            "Data Processing Error",
            icon="📄"
        )
        st.markdown(
            """
            Failed to process search results.

            **What to do:**
            1. Try again - this may be a temporary issue
            2. Try with different filters or entity type
            3. Check that your business context is complete
            """
        )

    elif "context" in error_message or "none" in error_message:
        # Missing context error
        st.error(
            "Missing Business Context",
            icon="📋"
        )
        st.markdown(
            """
            Business context is required to run discovery.

            **What to do:**
            1. Upload business documents
            2. Click "Process Documents" to extract context
            3. Verify context appears in the summary
            4. Then try discovery again
            """
        )

    else:
        # Generic error
        st.error(
            f"Discovery Failed",
            icon="❌"
        )
        st.markdown(
            f"""
            An unexpected error occurred during {entity_type or 'entity'} discovery.

            **What to do:**
            1. Check that all required information is provided
            2. Try again with simpler filters (or no filters)
            3. Review the business context for accuracy
            4. Check application logs for more details

            **Error:** {error}
            """
        )


def validate_discovery_preconditions() -> bool:
    """Validate that all preconditions for discovery are met.

    Checks for:
    - Business context is available
    - API key is configured

    Returns:
        bool: True if all preconditions are met, False otherwise
    """
    # Check for API key
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        st.warning(
            "API Key Not Configured",
            icon="🔑"
        )
        st.markdown(
            """
            Please configure your Google API key in `.env`:
            ```
            GOOGLE_API_KEY=your_api_key_here
            ```
            Then restart the application.
            """
        )
        return False

    return True


def show_discovery_info() -> None:
    """Display helpful information about the discovery process.

    Shows user-friendly guidance on what to expect during discovery.
    """
    st.info(
        """
        **Discovery Process**

        Searching for relevant companies may take 30-60 seconds.
        The system will:
        1. Generate targeted search queries
        2. Search the web for matching companies
        3. Filter results by relevance
        4. Score and rank matches
        5. Generate explanations for each match

        You can select filters (geography, industry) to narrow results.
        """,
        icon="ℹ️"
    )
