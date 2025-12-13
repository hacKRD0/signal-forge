"""CSV document parser.

This module provides functionality to extract text content from CSV files
using pandas for robust handling of various CSV formats and encodings.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd


logger = logging.getLogger(__name__)


def parse_csv(file_path: str) -> str:
    """Extract text content from a CSV file.

    Reads a CSV file and converts it to a readable string format with
    column headers preserved. Handles various encodings by attempting
    UTF-8 first, then falling back to Latin-1 if needed.

    Args:
        file_path: Path to the CSV file to parse (absolute or relative).

    Returns:
        Extracted content as a formatted string with column headers.
        Returns empty string if the CSV has no data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is corrupted or not a valid CSV file.
        PermissionError: If the file cannot be read due to permissions.

    Example:
        >>> text = parse_csv('data/customers.csv')
        >>> print(f"Extracted {len(text)} characters")

    Note:
        This parser attempts multiple encodings (UTF-8, Latin-1) to handle
        files with different character encodings gracefully.
    """
    # Convert to Path for better path handling
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Parsing CSV file: {file_path}")

    # Try different encodings
    encodings = ['utf-8', 'latin-1']
    df = None
    last_error = None

    for encoding in encodings:
        try:
            logger.debug(f"Attempting to read CSV with {encoding} encoding")
            df = pd.read_csv(str(path), encoding=encoding)
            logger.info(f"Successfully read CSV with {encoding} encoding")
            break
        except UnicodeDecodeError as e:
            logger.debug(f"Failed to read with {encoding} encoding: {e}")
            last_error = e
            continue
        except pd.errors.EmptyDataError:
            logger.warning(f"CSV file is empty: {file_path}")
            return ""
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error: {e}")
            raise ValueError(
                f"Malformed CSV file: {file_path}. {str(e)}"
            ) from e
        except PermissionError as e:
            logger.error(f"Permission denied reading file: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading CSV file {file_path}: {e}")
            last_error = e
            continue

    # If all encodings failed
    if df is None:
        logger.error(
            f"Failed to read CSV with any encoding: {file_path}"
        )
        raise ValueError(
            f"Could not read CSV file with supported encodings: {file_path}"
        ) from last_error

    # Check if DataFrame is empty
    if df.empty:
        logger.warning(f"CSV file has no data rows: {file_path}")
        return ""

    logger.debug(f"CSV has {len(df)} rows and {len(df.columns)} columns")

    try:
        # Convert DataFrame to string format with column structure preserved
        # Using to_string() maintains column alignment
        extracted_text = df.to_string(index=False)

        logger.info(
            f"Successfully extracted {len(extracted_text)} characters "
            f"from {len(df)} rows in {file_path}"
        )

        return extracted_text

    except Exception as e:
        logger.error(f"Error converting DataFrame to string: {e}")
        raise ValueError(
            f"Error formatting CSV data from {file_path}: {str(e)}"
        ) from e
