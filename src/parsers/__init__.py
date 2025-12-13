"""Document parsers package.

This package contains parsers for various document formats including
DOCX, PDF, CSV, and PPTX files.
"""

from .document_parser import DocumentParser, parse_document

__all__ = ['DocumentParser', 'parse_document']
