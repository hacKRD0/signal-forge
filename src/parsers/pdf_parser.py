"""PDF document parser.

This module provides functionality to extract text content from PDF files
using PyPDF2.
"""

import logging
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError


logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> str:
    """Extract text content from a PDF file.

    Reads a PDF file and extracts all text content from all pages.
    Pages are separated with page markers to preserve document structure.

    Args:
        file_path: Path to the PDF file to parse (absolute or relative).

    Returns:
        Extracted text as a single string with page separators.
        Returns empty string if the PDF has no extractable text.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is corrupted, encrypted, or not a valid PDF.
        PermissionError: If the file cannot be read due to permissions.

    Example:
        >>> text = parse_pdf('documents/report.pdf')
        >>> print(f"Extracted {len(text)} characters")

    Note:
        This parser extracts only text content. It does not perform OCR
        on scanned PDFs or images embedded in PDFs.
    """
    # Convert to Path for better path handling
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Parsing PDF file: {file_path}")

    try:
        # Open the PDF file
        reader = PdfReader(str(path))

        # Check if PDF is encrypted
        if reader.is_encrypted:
            logger.error(f"PDF file is encrypted: {file_path}")
            raise ValueError(
                f"PDF file is encrypted and cannot be parsed: {file_path}. "
                "Please decrypt the PDF before parsing."
            )

        # Get number of pages
        num_pages = len(reader.pages)
        logger.debug(f"PDF has {num_pages} pages")

        if num_pages == 0:
            logger.warning(f"PDF file has no pages: {file_path}")
            return ""

        # Extract text from all pages
        text_parts = []
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text.strip():  # Only add pages with text
                    # Add page separator for clarity
                    text_parts.append(f"--- Page {page_num} ---")
                    text_parts.append(page_text.strip())
                else:
                    logger.debug(f"Page {page_num} has no extractable text")
            except Exception as e:
                logger.warning(
                    f"Error extracting text from page {page_num}: {e}"
                )
                continue

        # Join all text parts with newlines
        extracted_text = "\n\n".join(text_parts)

        logger.info(
            f"Successfully extracted {len(extracted_text)} characters "
            f"from {num_pages} pages in {file_path}"
        )

        return extracted_text

    except PdfReadError as e:
        logger.error(f"Corrupted or invalid PDF file: {file_path}")
        raise ValueError(
            f"File is corrupted or not a valid PDF file: {file_path}"
        ) from e
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing PDF file {file_path}: {e}")
        raise ValueError(
            f"Error parsing PDF file {file_path}: {str(e)}"
        ) from e
