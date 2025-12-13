"""Context extraction from parsed documents using Google ADK agent.

This module provides the ContextExtractor class for extracting structured
business context from single or multiple documents.
"""

import json
import logging
from typing import List, Dict, Any

from src.parsers.document_parser import parse_document
from src.models.business_context import BusinessContext
from .discovery_agent import DiscoveryAgent


logger = logging.getLogger(__name__)


class ContextExtractor:
    """Extract structured business context from documents using AI.

    This class processes one or more documents and extracts structured business
    context information using a Google ADK agent. It handles multi-document
    processing by combining texts intelligently and parsing agent responses
    into BusinessContext objects.

    Attributes:
        agent: DiscoveryAgent instance used for context extraction

    Example:
        >>> agent = DiscoveryAgent()
        >>> extractor = ContextExtractor(agent)
        >>> context = extractor.extract_from_files(['doc1.pdf', 'doc2.docx'])
        >>> print(context.company_name)
    """

    def __init__(self, agent: DiscoveryAgent):
        """Initialize the context extractor.

        Args:
            agent: DiscoveryAgent instance to use for extraction

        Raises:
            ValueError: If agent is None
        """
        if agent is None:
            raise ValueError("agent cannot be None")

        self.agent = agent
        logger.info("ContextExtractor initialized")

    def extract_from_files(self, file_paths: List[str]) -> BusinessContext:
        """Extract business context from multiple document files.

        This method processes multiple documents by:
        1. Parsing each document to extract text
        2. Combining all text with separators
        3. Calling the agent to extract context from the combined text
        4. Parsing the agent response into a BusinessContext object

        Args:
            file_paths: List of file paths to process (supports DOCX, PDF, CSV, PPTX)

        Returns:
            BusinessContext: Structured business context extracted from documents

        Raises:
            ValueError: If file_paths is empty or None
            FileNotFoundError: If any file does not exist
            RuntimeError: If extraction fails

        Example:
            >>> extractor = ContextExtractor(agent)
            >>> context = extractor.extract_from_files([
            ...     'company_overview.pdf',
            ...     'product_catalog.docx'
            ... ])
            >>> print(context.industry)
        """
        if not file_paths:
            raise ValueError("file_paths cannot be empty")

        logger.info(f"Extracting context from {len(file_paths)} files")

        try:
            # Parse all documents and collect their text
            document_texts = []
            for file_path in file_paths:
                logger.debug(f"Parsing document: {file_path}")
                try:
                    text = parse_document(file_path)
                    if text and text.strip():
                        document_texts.append(text)
                        logger.debug(
                            f"Parsed {file_path}: {len(text)} characters"
                        )
                    else:
                        logger.warning(f"Document {file_path} is empty, skipping")
                except Exception as e:
                    logger.error(f"Failed to parse {file_path}: {e}")
                    # Continue with other documents instead of failing completely
                    continue

            if not document_texts:
                logger.error("No valid document text extracted from any file")
                raise ValueError("No valid document text could be extracted")

            # Combine all document texts with separators
            separator = "\n\n" + "=" * 80 + "\n\n"
            combined_text = separator.join(document_texts)

            logger.info(
                f"Combined {len(document_texts)} documents, "
                f"total {len(combined_text)} characters"
            )

            # Extract context from combined text
            return self.extract_from_text(combined_text)

        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            error_msg = f"Failed to extract context from files: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def extract_from_text(self, text: str) -> BusinessContext:
        """Extract business context directly from text.

        This method is useful for testing or when text has already been extracted.
        It calls the agent to extract structured context and parses the response
        into a BusinessContext object.

        Args:
            text: Text content to extract context from

        Returns:
            BusinessContext: Structured business context extracted from text

        Raises:
            ValueError: If text is empty or None
            RuntimeError: If extraction fails

        Example:
            >>> extractor = ContextExtractor(agent)
            >>> text = "Acme Corp is a SaaS company..."
            >>> context = extractor.extract_from_text(text)
            >>> print(context.company_name)
        """
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        logger.info("Extracting context from text")

        try:
            # Call agent to extract context
            agent_response = self.agent.extract_context(text)

            logger.debug(f"Agent response: {agent_response}")

            # Parse agent response into BusinessContext
            context = self._parse_agent_response(agent_response)

            logger.info(
                f"Context extraction completed: "
                f"company={context.company_name or 'Unknown'}, "
                f"industry={context.industry or 'Unknown'}"
            )

            return context

        except Exception as e:
            error_msg = f"Failed to extract context from text: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _parse_agent_response(self, response: Dict[str, Any]) -> BusinessContext:
        """Parse agent response into BusinessContext object.

        This method handles various response formats gracefully:
        - Standard JSON with expected fields
        - JSON with some missing fields (uses defaults)
        - Unexpected formats (extracts what's available)

        Args:
            response: Agent response dictionary

        Returns:
            BusinessContext: Parsed business context with defaults for missing fields

        Example:
            >>> response = {"industry": "SaaS", "company_name": "Acme"}
            >>> context = extractor._parse_agent_response(response)
            >>> print(context.industry)
            'SaaS'
        """
        try:
            # If response has 'raw_response', it means parsing failed in agent
            # Try to extract JSON from raw response
            if "raw_response" in response and len(response) == 1:
                raw_text = response["raw_response"]
                logger.debug("Agent returned raw_response, attempting to parse JSON")

                # Try to find and parse JSON in the raw response
                if "{" in raw_text and "}" in raw_text:
                    json_start = raw_text.index("{")
                    json_end = raw_text.rindex("}") + 1
                    json_str = raw_text[json_start:json_end]
                    try:
                        response = json.loads(json_str)
                    except json.JSONDecodeError:
                        logger.warning("Could not parse JSON from raw_response")
                        # Keep original response with raw_response

            # Extract fields with defaults for missing values
            context_data = {}

            # Map agent response fields to BusinessContext fields
            field_mappings = {
                "company_name": ["company_name", "company", "name"],
                "industry": ["industry", "sector"],
                "products_services": [
                    "products_services",
                    "products",
                    "services",
                    "offerings",
                ],
                "target_market": ["target_market", "market", "customers"],
                "geography": ["geography", "locations", "regions", "markets"],
                "key_strengths": [
                    "key_strengths",
                    "strengths",
                    "value_proposition",
                    "differentiators",
                ],
                "additional_notes": [
                    "additional_notes",
                    "notes",
                    "business_model",
                    "technology_stack",
                ],
            }

            # Extract each field, trying alternative names
            for field_name, possible_keys in field_mappings.items():
                for key in possible_keys:
                    if key in response:
                        value = response[key]

                        # Handle list fields
                        if field_name in [
                            "products_services",
                            "geography",
                            "key_strengths",
                        ]:
                            if isinstance(value, list):
                                context_data[field_name] = value
                            elif isinstance(value, str):
                                # Try to split comma-separated strings
                                if "," in value:
                                    context_data[field_name] = [
                                        item.strip()
                                        for item in value.split(",")
                                        if item.strip()
                                    ]
                                else:
                                    context_data[field_name] = [value]
                            break
                        # Handle string fields
                        else:
                            if isinstance(value, str):
                                context_data[field_name] = value
                            elif isinstance(value, list):
                                # Convert list to comma-separated string
                                context_data[field_name] = ", ".join(
                                    str(v) for v in value
                                )
                            else:
                                context_data[field_name] = str(value)
                            break

            # If we have company_size or business_model in response, add to additional_notes
            additional_info = []
            for key in ["company_size", "business_model", "technology_stack"]:
                if key in response and key not in context_data.get(
                    "additional_notes", ""
                ):
                    value = response[key]
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    additional_info.append(f"{key.replace('_', ' ').title()}: {value}")

            # Append to additional_notes if we found extra info
            if additional_info:
                existing_notes = context_data.get("additional_notes", "")
                if existing_notes:
                    context_data["additional_notes"] = (
                        f"{existing_notes}. {'. '.join(additional_info)}"
                    )
                else:
                    context_data["additional_notes"] = ". ".join(additional_info)

            # Create BusinessContext with extracted data
            context = BusinessContext.from_dict(context_data)

            logger.debug(f"Parsed context: {context.to_dict()}")

            return context

        except Exception as e:
            logger.warning(f"Error parsing agent response, using defaults: {e}")
            # Return empty context with defaults on parsing failure
            return BusinessContext()
