"""Unified document parser interface.

This module provides a unified interface for parsing various document formats
including DOCX, PDF, CSV, and PPTX files. It automatically detects the format
from the file extension and routes to the appropriate parser.
"""

import logging
from pathlib import Path
from typing import Optional

from .docx_parser import parse_docx
from .pdf_parser import parse_pdf
from .csv_parser import parse_csv
from .pptx_parser import parse_pptx


logger = logging.getLogger(__name__)


class DocumentParser:
    """Unified document parser with automatic format detection.

    This class provides a single interface for parsing multiple document formats.
    It automatically detects the file format from the extension and routes to
    the appropriate parser.

    Supported formats:
        - .docx - Microsoft Word documents
        - .pdf - PDF documents
        - .csv - CSV (Comma-Separated Values) files
        - .pptx - Microsoft PowerPoint presentations

    Example:
        >>> parser = DocumentParser()
        >>> text = parser.parse('documents/report.docx')
        >>> print(f"Extracted {len(text)} characters")
    """

    # Mapping of file extensions to parser functions
    PARSERS = {
        '.docx': parse_docx,
        '.pdf': parse_pdf,
        '.csv': parse_csv,
        '.pptx': parse_pptx,
    }

    def parse(self, file_path: str) -> str:
        """Parse a document and extract its text content.

        Automatically detects the document format from the file extension
        and uses the appropriate parser to extract text content.

        Args:
            file_path: Path to the document file to parse (absolute or relative).

        Returns:
            Extracted text content as a string. The format depends on the
            document type but always preserves structure (e.g., page/slide numbers).

        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the file format is unsupported or file is corrupted.
            PermissionError: If the file cannot be read due to permissions.

        Example:
            >>> parser = DocumentParser()
            >>> text = parser.parse('data/customers.csv')
        """
        # Convert to Path for better path handling
        path = Path(file_path)

        # Get file extension (normalized to lowercase)
        extension = path.suffix.lower()

        logger.info(f"Parsing document: {file_path} (format: {extension})")

        # Check if format is supported
        if extension not in self.PARSERS:
            supported = ', '.join(sorted(self.PARSERS.keys()))
            logger.error(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {supported}"
            )
            raise ValueError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {supported}"
            )

        # Get the appropriate parser function
        parser_func = self.PARSERS[extension]
        parser_name = parser_func.__name__

        logger.debug(f"Using parser: {parser_name}")

        # Parse the document
        try:
            text = parser_func(str(path))
            logger.info(
                f"Successfully parsed {file_path} using {parser_name}, "
                f"extracted {len(text)} characters"
            )
            return text
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            raise


def parse_document(file_path: str) -> str:
    """Parse a document and extract its text content.

    Convenience function that creates a DocumentParser instance and parses
    the specified file. This is the recommended way to parse documents.

    Supported formats:
        - .docx - Microsoft Word documents
        - .pdf - PDF documents
        - .csv - CSV (Comma-Separated Values) files
        - .pptx - Microsoft PowerPoint presentations

    Args:
        file_path: Path to the document file to parse (absolute or relative).

    Returns:
        Extracted text content as a string.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file format is unsupported or file is corrupted.
        PermissionError: If the file cannot be read due to permissions.

    Example:
        >>> text = parse_document('documents/report.pdf')
        >>> print(f"Extracted {len(text)} characters")
    """
    parser = DocumentParser()
    return parser.parse(file_path)
