"""Document processing integration for Streamlit UI.

This module handles the processing of uploaded files, including saving to temporary
storage, parsing, and extracting business context using the ContextExtractor.
"""

import logging
import tempfile
import os
from pathlib import Path
from typing import List

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.parsers.document_parser import parse_document
from src.agent.context_extractor import ContextExtractor
from src.models.business_context import BusinessContext


logger = logging.getLogger(__name__)


def process_uploaded_files(
    uploaded_files: List[UploadedFile],
    context_extractor: ContextExtractor
) -> BusinessContext:
    """Process uploaded files and extract business context.

    This function:
    1. Saves uploaded files to a temporary directory
    2. Parses each file to extract text
    3. Uses ContextExtractor to extract structured business context
    4. Cleans up temporary files
    5. Shows progress indicators during processing

    Args:
        uploaded_files: List of UploadedFile objects from Streamlit file uploader.
        context_extractor: ContextExtractor instance for extracting context.

    Returns:
        BusinessContext object containing extracted information.

    Raises:
        ValueError: If uploaded_files is empty or context_extractor is None.
        RuntimeError: If processing fails.

    Example:
        >>> from src.agent.discovery_agent import DiscoveryAgent
        >>> agent = DiscoveryAgent()
        >>> extractor = ContextExtractor(agent)
        >>> context = process_uploaded_files(uploaded_files, extractor)
    """
    if not uploaded_files:
        raise ValueError("No files to process")

    if context_extractor is None:
        raise ValueError("context_extractor cannot be None")

    # Create temporary directory for uploaded files
    temp_dir = tempfile.mkdtemp()
    file_paths = []

    try:
        # Progress bar for overall processing
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Step 1: Save uploaded files to temporary directory
        status_text.text("Saving uploaded files...")
        for i, uploaded_file in enumerate(uploaded_files):
            # Save file to temp directory
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_paths.append(file_path)

            # Update progress
            progress = (i + 1) / (len(uploaded_files) * 3)
            progress_bar.progress(progress)

        logger.info(f"Saved {len(file_paths)} files to {temp_dir}")

        # Step 2: Parse documents
        status_text.text("Parsing documents...")
        parsed_count = 0
        for i, file_path in enumerate(file_paths):
            try:
                parse_document(file_path)
                parsed_count += 1
                logger.debug(f"Parsed {file_path}")
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
                st.warning(f"Could not parse {os.path.basename(file_path)}: {e}")

            # Update progress
            progress = (len(uploaded_files) + i + 1) / (len(uploaded_files) * 3)
            progress_bar.progress(progress)

        if parsed_count == 0:
            raise ValueError("No files could be parsed successfully")

        # Step 3: Extract business context
        status_text.text("Extracting business context with AI...")
        context = context_extractor.extract_from_files(file_paths)

        # Complete progress
        progress_bar.progress(1.0)
        status_text.text("Processing complete!")

        logger.info(
            f"Successfully processed {parsed_count}/{len(file_paths)} files, "
            f"extracted context for {context.company_name or 'Unknown'}"
        )

        return context

    except ValueError:
        # Re-raise ValueError as-is
        raise
    except Exception as e:
        error_msg = f"Failed to process uploaded files: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    finally:
        # Clean up temporary files
        try:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            logger.debug(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {e}")
