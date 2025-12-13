"""Discovery agent wrapper for customer and partner discovery operations.

This module provides a high-level interface for discovery operations using
Google ADK agents with specialized prompts.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .agent_setup import create_discovery_agent, get_generation_config
from .prompts import (
    CONTEXT_EXTRACTION_PROMPT,
    CUSTOMER_DISCOVERY_PROMPT,
    PARTNER_DISCOVERY_PROMPT,
)
from .query_builder import QueryBuilder
from ..models.business_context import BusinessContext


logger = logging.getLogger(__name__)


class DiscoveryAgent:
    """High-level wrapper for discovery operations using Google ADK.

    This class provides methods for:
    - Extracting business context from documents
    - Finding potential customers
    - Finding potential partners

    Each operation uses specialized prompts and handles responses appropriately.

    Attributes:
        client: Google ADK client instance
        model: Model name being used
        temperature: Temperature setting for generation
        interaction_log: List of all agent interactions for tracing
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        enable_web_search: bool = True,
    ):
        """Initialize the discovery agent.

        Args:
            model: The Gemini model to use. Defaults to "gemini-2.0-flash-exp".
            temperature: Controls randomness (0.0-1.0). Defaults to 0.7.
            enable_web_search: Whether to enable web search tool. Defaults to True.

        Raises:
            ValueError: If configuration is invalid.
            RuntimeError: If agent initialization fails.
        """
        try:
            self.client = create_discovery_agent(
                model=model,
                temperature=temperature,
                enable_web_search=enable_web_search,
            )
            self.model = model
            self.temperature = temperature
            self.enable_web_search = enable_web_search
            self.interaction_log: List[Dict[str, Any]] = []
            self.query_builder = QueryBuilder()

            logger.info(
                f"DiscoveryAgent initialized with model={model}, "
                f"temperature={temperature}, web_search={enable_web_search}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize DiscoveryAgent: {e}")
            raise

    def _log_interaction(
        self,
        operation: str,
        prompt: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an agent interaction for tracing.

        Args:
            operation: Name of the operation (e.g., "extract_context")
            prompt: The full prompt sent to the agent
            response: The agent's response
            metadata: Additional metadata about the interaction
        """
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "model": self.model,
            "temperature": self.temperature,
            "prompt": prompt,
            "response": response,
            "metadata": metadata or {},
        }
        self.interaction_log.append(interaction)
        logger.debug(f"Logged interaction for {operation}")

    def _generate_content(
        self, system_prompt: str, user_input: str, operation: str
    ) -> str:
        """Generate content using the agent with error handling.

        Args:
            system_prompt: The system prompt to use
            user_input: The user's input/query
            operation: Name of the operation for logging

        Returns:
            str: The agent's response text

        Raises:
            RuntimeError: If content generation fails after retries
        """
        try:
            # Combine system prompt and user input
            full_prompt = f"{system_prompt}\n\n---\n\nUser Input:\n{user_input}"

            # Generate content
            config = get_generation_config(temperature=self.temperature)

            # Use the models API for content generation
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=config,
            )

            # Extract response text
            response_text = response.text

            # Log the interaction
            self._log_interaction(
                operation=operation,
                prompt=full_prompt,
                response=response_text,
                metadata={"model": self.model},
            )

            return response_text

        except Exception as e:
            error_msg = f"Content generation failed for {operation}: {e}"
            logger.error(error_msg)
            self._log_interaction(
                operation=operation,
                prompt=f"{system_prompt}\n\n---\n\n{user_input}",
                response="",
                metadata={"error": str(e)},
            )
            raise RuntimeError(error_msg) from e

    def _format_discovery_prompt(
        self, prompt_template: str, context: Dict[str, Any], queries: List[str]
    ) -> str:
        """Format discovery prompt with context and queries.

        Combines the system prompt template with business context and suggested
        search queries into a complete prompt for the agent.

        Args:
            prompt_template: The base system prompt (customer or partner discovery)
            context: Business context dictionary
            queries: List of search query strings to include

        Returns:
            str: Formatted prompt string ready for agent consumption

        Example:
            >>> prompt = agent._format_discovery_prompt(
            ...     CUSTOMER_DISCOVERY_PROMPT,
            ...     context_dict,
            ...     ["marketing agencies in US", "SMB marketing firms"]
            ... )
        """
        # Format context as string
        context_str = json.dumps(context, indent=2)

        # Format queries as numbered list
        queries_str = "\n".join(f"{i+1}. {q}" for i, q in enumerate(queries))

        # Combine into full prompt
        formatted_prompt = f"""{prompt_template}

---

**Business Context:**
{context_str}

---

**Suggested Search Queries:**

Use these targeted search queries to find the best matches:

{queries_str}

For each query, use the web search tool to find relevant companies. Analyze the results and return the top prospects in the specified JSON format."""

        return formatted_prompt

    def extract_context(self, document_text: str) -> Dict[str, Any]:
        """Extract business context from a document.

        Args:
            document_text: The text content of the business document

        Returns:
            dict: Structured business context with keys like industry,
                products_services, target_market, geography, etc.

        Raises:
            RuntimeError: If context extraction fails
            ValueError: If document_text is empty

        Example:
            >>> agent = DiscoveryAgent()
            >>> context = agent.extract_context(doc_text)
            >>> print(context['industry'])
            'SaaS - Marketing Automation'
        """
        if not document_text or not document_text.strip():
            raise ValueError("document_text cannot be empty")

        logger.info("Extracting context from document")

        try:
            response_text = self._generate_content(
                system_prompt=CONTEXT_EXTRACTION_PROMPT,
                user_input=f"Document content:\n\n{document_text}",
                operation="extract_context",
            )

            # Try to parse as JSON if it's in JSON format
            try:
                # Look for JSON in the response
                if "{" in response_text and "}" in response_text:
                    json_start = response_text.index("{")
                    json_end = response_text.rindex("}") + 1
                    json_str = response_text[json_start:json_end]
                    context = json.loads(json_str)
                else:
                    # If no JSON, return the text wrapped in a dict
                    context = {"raw_response": response_text}
            except (json.JSONDecodeError, ValueError):
                # If parsing fails, return raw response
                context = {"raw_response": response_text}

            logger.info(f"Context extraction completed: {len(context)} fields extracted")
            return context

        except Exception as e:
            logger.error(f"Context extraction failed: {e}")
            raise RuntimeError(f"Failed to extract context: {e}") from e

    def find_customers(
        self, business_context: Dict[str, Any], filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Find potential customers based on business context.

        Args:
            business_context: Business context dict from extract_context()
            filters: Optional filters to narrow search:
                - geography: List of geographic regions
                - industry: List of industries to focus on
                - size: Company size range (e.g., "50-200 employees")

        Returns:
            list: List of potential customer dicts, each with:
                - company_name: str
                - website: str
                - locations: list
                - size_estimate: str
                - brief_rationale: str

        Raises:
            RuntimeError: If customer discovery fails
            ValueError: If business_context is empty

        Example:
            >>> agent = DiscoveryAgent()
            >>> customers = agent.find_customers(
            ...     context,
            ...     filters={"geography": ["North America"]}
            ... )
            >>> print(len(customers))
            8
        """
        if not business_context:
            raise ValueError("business_context cannot be empty")

        logger.info("Finding potential customers")

        try:
            # Convert dict to BusinessContext for query generation
            context = BusinessContext.from_dict(business_context)

            # Generate targeted search queries
            queries = self.query_builder.build_customer_queries(context, filters)
            logger.info(f"Generated {len(queries)} customer search queries: {queries}")

            # Format the complete discovery prompt with context and queries
            formatted_prompt = self._format_discovery_prompt(
                CUSTOMER_DISCOVERY_PROMPT,
                business_context,
                queries
            )

            # Execute discovery with formatted prompt
            response_text = self._generate_content(
                system_prompt=formatted_prompt,
                user_input="Please search for and identify potential customers.",
                operation="find_customers",
            )

            # Try to parse response - could be JSON array or text with embedded JSON
            customers = self._parse_discovery_response(response_text)

            logger.info(f"Found {len(customers)} potential customers")
            return customers

        except Exception as e:
            logger.error(f"Customer discovery failed: {e}")
            raise RuntimeError(f"Failed to find customers: {e}") from e

    def find_partners(
        self, business_context: Dict[str, Any], filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Find potential partners based on business context.

        Args:
            business_context: Business context dict from extract_context()
            filters: Optional filters to narrow search:
                - geography: List of geographic regions
                - industry: List of industries to focus on
                - partnership_type: Type of partnership (e.g., "technology", "distribution")

        Returns:
            list: List of potential partner dicts, each with:
                - company_name: str
                - website: str
                - locations: list
                - size_estimate: str
                - brief_rationale: str

        Raises:
            RuntimeError: If partner discovery fails
            ValueError: If business_context is empty

        Example:
            >>> agent = DiscoveryAgent()
            >>> partners = agent.find_partners(
            ...     context,
            ...     filters={"partnership_type": "technology"}
            ... )
            >>> print(len(partners))
            6
        """
        if not business_context:
            raise ValueError("business_context cannot be empty")

        logger.info("Finding potential partners")

        try:
            # Convert dict to BusinessContext for query generation
            context = BusinessContext.from_dict(business_context)

            # Generate targeted search queries
            queries = self.query_builder.build_partner_queries(context, filters)
            logger.info(f"Generated {len(queries)} partner search queries: {queries}")

            # Format the complete discovery prompt with context and queries
            formatted_prompt = self._format_discovery_prompt(
                PARTNER_DISCOVERY_PROMPT,
                business_context,
                queries
            )

            # Execute discovery with formatted prompt
            response_text = self._generate_content(
                system_prompt=formatted_prompt,
                user_input="Please search for and identify potential partners.",
                operation="find_partners",
            )

            # Try to parse response - could be JSON array or text with embedded JSON
            partners = self._parse_discovery_response(response_text)

            logger.info(f"Found {len(partners)} potential partners")
            return partners

        except Exception as e:
            logger.error(f"Partner discovery failed: {e}")
            raise RuntimeError(f"Failed to find partners: {e}") from e

    def _parse_discovery_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse discovery response into list of company dicts.

        Handles various response formats including JSON arrays, multiple JSON
        objects, or structured text.

        Args:
            response_text: The raw response from the agent

        Returns:
            list: List of company dictionaries
        """
        try:
            # Try parsing as JSON array first
            if response_text.strip().startswith("["):
                return json.loads(response_text)

            # Look for JSON objects in the text
            results = []
            lines = response_text.split("\n")
            current_json = ""
            brace_count = 0

            for line in lines:
                for char in line:
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1

                    if brace_count > 0 or char in "{":
                        current_json += char

                    if brace_count == 0 and current_json:
                        try:
                            obj = json.loads(current_json)
                            results.append(obj)
                            current_json = ""
                        except json.JSONDecodeError:
                            current_json = ""

            if results:
                return results

            # If no JSON found, return raw response in a structured format
            return [{"raw_response": response_text}]

        except Exception as e:
            logger.warning(f"Failed to parse discovery response: {e}")
            return [{"raw_response": response_text}]

    def get_interaction_log(self) -> List[Dict[str, Any]]:
        """Get the log of all agent interactions.

        Returns:
            list: List of interaction dictionaries with timestamps,
                prompts, responses, and metadata.
        """
        return self.interaction_log.copy()

    def clear_interaction_log(self) -> None:
        """Clear the interaction log."""
        self.interaction_log.clear()
        logger.info("Interaction log cleared")
