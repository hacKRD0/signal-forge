"""Search result parser for extracting company information.

This module provides the SearchResultParser class that uses the Google ADK agent
to extract structured company information from web search results.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from ..models.discovery_results import CompanyInfo


logger = logging.getLogger(__name__)


class SearchResultParser:
    """Parser for extracting structured company info from search results.

    Uses the Google ADK agent to intelligently parse search result text and
    extract company details like name, website, location, and size.

    Example:
        >>> from src.agent.discovery_agent import DiscoveryAgent
        >>> agent = DiscoveryAgent()
        >>> parser = SearchResultParser(agent)
        >>> result_text = "Acme Corp - Leading SaaS provider in North America..."
        >>> company = parser.parse_company_info(result_text, "https://acme.com")
        >>> print(company.name)
        'Acme Corp'
    """

    def __init__(self, agent=None):
        """Initialize the search result parser.

        Args:
            agent: Optional DiscoveryAgent instance. If not provided,
                   parsing will use simpler heuristic-based extraction.
        """
        self.agent = agent
        logger.info("SearchResultParser initialized")

    def parse_company_info(
        self, search_result_text: str, source_url: str = ""
    ) -> Optional[CompanyInfo]:
        """Extract structured company info from a search result.

        Args:
            search_result_text: The text content of a search result
            source_url: The URL where this result was found

        Returns:
            CompanyInfo: Extracted company information, or None if parsing fails

        Example:
            >>> parser = SearchResultParser()
            >>> result = "Acme Corp - Marketing automation for SMBs in USA"
            >>> company = parser.parse_company_info(result, "https://acme.com")
            >>> print(company.name)
            'Acme Corp'
        """
        if not search_result_text or not search_result_text.strip():
            logger.warning("Empty search result text provided")
            return None

        try:
            if self.agent:
                # Use agent to extract structured data
                company_info = self._parse_with_agent(search_result_text, source_url)
            else:
                # Use heuristic-based parsing
                company_info = self._parse_with_heuristics(search_result_text, source_url)

            if company_info:
                logger.debug(f"Parsed company: {company_info.name}")
                return company_info
            else:
                logger.warning("Failed to parse company info from result")
                return None

        except Exception as e:
            logger.error(f"Error parsing company info: {e}")
            return None

    def _parse_with_agent(
        self, search_result_text: str, source_url: str
    ) -> Optional[CompanyInfo]:
        """Parse company info using the Google ADK agent.

        Args:
            search_result_text: Search result text
            source_url: Source URL

        Returns:
            CompanyInfo or None
        """
        extraction_prompt = """Extract structured company information from this search result.

Return a JSON object with these fields:
- name: Company name (string)
- website: Company website URL (string, extract from text or use the source URL)
- locations: List of locations/regions where company operates (list of strings)
- size_estimate: Company size estimate - one of: "Small", "Medium", "Large", "Unknown" (string)
- description: Brief 1-2 sentence description of what the company does (string)

Search Result:
{result_text}

Source URL: {source_url}

Return ONLY the JSON object, no additional text."""

        try:
            # Format the prompt
            prompt = extraction_prompt.format(
                result_text=search_result_text,
                source_url=source_url or "Not provided"
            )

            # Use agent to generate structured response
            response = self.agent._generate_content(
                system_prompt=prompt,
                user_input="Extract the company information.",
                operation="parse_company_info"
            )

            # Parse JSON response
            company_data = self._extract_json_from_response(response)

            if company_data:
                # Create CompanyInfo with source URL
                return CompanyInfo(
                    name=company_data.get("name", "Unknown"),
                    website=company_data.get("website", source_url or ""),
                    locations=company_data.get("locations", []),
                    size_estimate=company_data.get("size_estimate", "Unknown"),
                    description=company_data.get("description", ""),
                    sources=[source_url] if source_url else []
                )
            else:
                logger.warning("No valid JSON found in agent response")
                return None

        except Exception as e:
            logger.error(f"Agent-based parsing failed: {e}")
            return None

    def _parse_with_heuristics(
        self, search_result_text: str, source_url: str
    ) -> Optional[CompanyInfo]:
        """Parse company info using simple heuristics.

        Args:
            search_result_text: Search result text
            source_url: Source URL

        Returns:
            CompanyInfo or None
        """
        try:
            # Extract company name (usually first line or before " - ")
            lines = search_result_text.strip().split("\n")
            first_line = lines[0] if lines else search_result_text

            # Try to extract name from "Company Name - Description" format
            if " - " in first_line:
                name = first_line.split(" - ")[0].strip()
            else:
                # Use first few words as name
                words = first_line.split()[:3]
                name = " ".join(words)

            # Try to extract website from text
            website = source_url
            if "http" in search_result_text:
                # Simple URL extraction
                for word in search_result_text.split():
                    if word.startswith("http"):
                        website = word.strip(".,;:)")
                        break

            # Extract location hints
            locations = []
            location_keywords = ["USA", "US", "United States", "North America",
                                "Europe", "Asia", "UK", "Canada", "Australia"]
            for keyword in location_keywords:
                if keyword in search_result_text:
                    locations.append(keyword)
                    break  # Just take first match

            # Estimate size based on keywords
            size_estimate = "Unknown"
            if any(word in search_result_text.lower() for word in ["small", "startup", "smb"]):
                size_estimate = "Small"
            elif any(word in search_result_text.lower() for word in ["enterprise", "large", "fortune"]):
                size_estimate = "Large"
            elif any(word in search_result_text.lower() for word in ["medium", "mid-size", "growing"]):
                size_estimate = "Medium"

            # Use result text as description (truncate if too long)
            description = search_result_text[:200] + "..." if len(search_result_text) > 200 else search_result_text

            return CompanyInfo(
                name=name,
                website=website or "",
                locations=locations,
                size_estimate=size_estimate,
                description=description,
                sources=[source_url] if source_url else []
            )

        except Exception as e:
            logger.error(f"Heuristic parsing failed: {e}")
            return None

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from agent response.

        Args:
            response_text: Agent response that may contain JSON

        Returns:
            dict or None: Parsed JSON object
        """
        try:
            # Try direct JSON parse first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Look for JSON object in text
            try:
                if "{" in response_text and "}" in response_text:
                    json_start = response_text.index("{")
                    json_end = response_text.rindex("}") + 1
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
            except (ValueError, json.JSONDecodeError):
                pass

        return None

    def parse_multiple_results(
        self, results: List[Dict[str, str]]
    ) -> List[CompanyInfo]:
        """Process multiple search results and extract companies.

        Args:
            results: List of search result dicts with keys:
                - result_text: The text content
                - url: The source URL
                - snippet: Optional snippet (used if result_text not available)

        Returns:
            list: List of unique CompanyInfo instances (duplicates removed)

        Example:
            >>> parser = SearchResultParser()
            >>> results = [
            ...     {"result_text": "Acme Corp...", "url": "https://acme.com"},
            ...     {"result_text": "Beta Inc...", "url": "https://beta.com"}
            ... ]
            >>> companies = parser.parse_multiple_results(results)
            >>> len(companies)
            2
        """
        companies = []
        seen_keys = set()  # Track (name, website) to prevent duplicates

        for result in results:
            # Get text content
            text = result.get("result_text") or result.get("snippet", "")
            url = result.get("url", "")

            if not text:
                logger.debug(f"Skipping result with no text: {url}")
                continue

            # Parse company info
            company_info = self.parse_company_info(text, url)

            if company_info:
                # Check for duplicates
                key = (company_info.name.lower(), company_info.website.lower())
                if key not in seen_keys:
                    seen_keys.add(key)
                    companies.append(company_info)
                    logger.debug(f"Added company: {company_info.name}")
                else:
                    logger.debug(f"Duplicate company skipped: {company_info.name}")

        logger.info(f"Parsed {len(companies)} unique companies from {len(results)} results")
        return companies

    def deduplicate_companies(self, companies: List[CompanyInfo]) -> List[CompanyInfo]:
        """Remove duplicate companies from a list.

        Deduplication is based on company name and website (case-insensitive).

        Args:
            companies: List of CompanyInfo instances

        Returns:
            list: Deduplicated list of CompanyInfo instances

        Example:
            >>> parser = SearchResultParser()
            >>> companies = [
            ...     CompanyInfo("Acme", "acme.com", [], "Small", "", []),
            ...     CompanyInfo("ACME", "acme.com", [], "Medium", "", []),
            ... ]
            >>> unique = parser.deduplicate_companies(companies)
            >>> len(unique)
            1
        """
        seen_keys = set()
        unique_companies = []

        for company in companies:
            key = (company.name.lower(), company.website.lower())
            if key not in seen_keys:
                seen_keys.add(key)
                unique_companies.append(company)

        removed_count = len(companies) - len(unique_companies)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate companies")

        return unique_companies
