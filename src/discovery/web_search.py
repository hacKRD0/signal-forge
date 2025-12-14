"""Web search integration using Google ADK built-in search tool.

This module provides the WebSearchEngine class that uses Google ADK's built-in
web search capability to find and parse company information.
"""

import logging
from typing import List, Dict, Any, Optional

from .search_parser import SearchResultParser
from ..models.discovery_results import CompanyInfo


logger = logging.getLogger(__name__)


class WebSearchEngine:
    """Web search engine using Google ADK's built-in search tool.

    This class integrates with the Google ADK agent's built-in web search
    capability to perform searches and parse results into structured company
    information.

    Example:
        >>> from src.agent.discovery_agent import DiscoveryAgent
        >>> agent = DiscoveryAgent(enable_web_search=True)
        >>> engine = WebSearchEngine(agent)
        >>> queries = ["SaaS companies in North America"]
        >>> companies = engine.search_and_parse(queries)
        >>> print(len(companies))
        5
    """

    def __init__(self, agent):
        """Initialize the web search engine.

        Args:
            agent: DiscoveryAgent instance with web search enabled

        Raises:
            ValueError: If agent is None or web search is not enabled
        """
        if agent is None:
            raise ValueError("Agent cannot be None")

        if not agent.enable_web_search:
            logger.warning("Agent web search is not enabled - searches may fail")

        self.agent = agent
        self.parser = SearchResultParser(agent)
        self.max_results_per_query = 5  # Balances coverage and quality
        logger.info(
            f"WebSearchEngine initialized with max_results={self.max_results_per_query}"
        )

    def search(
        self,
        queries: List[str],
        max_results_per_query: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Perform web searches for multiple queries using Google ADK.

        Args:
            queries: List of search query strings
            max_results_per_query: Optional override for max results per query.
                                  Defaults to self.max_results_per_query (5)

        Returns:
            list: List of search result dictionaries with keys:
                - query: The search query used
                - result_text: The text content of the result
                - url: The source URL
                - snippet: Brief snippet/summary

        Raises:
            RuntimeError: If search fails

        Example:
            >>> engine = WebSearchEngine(agent)
            >>> results = engine.search(["marketing agencies"])
            >>> print(len(results))
            5
            >>> print(results[0]['query'])
            'marketing agencies'
        """
        if not queries:
            logger.warning("No queries provided to search()")
            return []

        max_results = max_results_per_query or self.max_results_per_query

        # Log rate limiting warning if many queries
        if len(queries) > 10:
            logger.warning(
                f"Searching {len(queries)} queries may hit rate limits. "
                f"Consider reducing query count."
            )

        all_results = []

        for query in queries:
            try:
                logger.info(f"Searching for: {query}")

                # Use agent to perform web search
                results = self._search_with_agent(query, max_results)

                # Add query context to each result
                for result in results:
                    result["query"] = query

                all_results.extend(results)
                logger.info(f"Found {len(results)} results for query: {query}")

            except Exception as e:
                logger.error(f"Search failed for query '{query}': {e}")
                # Continue with other queries even if one fails
                continue

        logger.info(f"Total search results collected: {len(all_results)}")
        return all_results

    def _search_with_agent(
        self, query: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Perform a single search using the Google ADK agent.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            list: List of search result dictionaries

        Raises:
            RuntimeError: If search fails
        """
        search_prompt = f"""Perform a web search for the following query and return the top {max_results} results.

Query: {query}

For each result, provide:
1. The URL
2. The title
3. A snippet/description

Use your web search tool to find the most relevant results. Return the results in JSON format as an array of objects with fields: "url", "title", "snippet".

Example format:
[
  {{"url": "https://example.com", "title": "Example Title", "snippet": "Example description..."}},
  ...
]
"""

        try:
            # Use agent's generate_content method to perform search
            response = self.agent._generate_content(
                system_prompt=search_prompt,
                user_input=f"Search for: {query}",
                operation="web_search"
            )

            # Parse the search results from agent response
            results = self._parse_search_results(response)

            # Limit to max_results
            return results[:max_results]

        except Exception as e:
            error_msg = f"Web search failed for query '{query}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _parse_search_results(self, response: str) -> List[Dict[str, Any]]:
        """Parse search results from agent response.

        Args:
            response: Agent response containing search results

        Returns:
            list: List of parsed search result dictionaries
        """
        import json

        results = []

        try:
            # Try to extract JSON array from response
            if "[" in response and "]" in response:
                json_start = response.index("[")
                json_end = response.rindex("]") + 1
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)

                # Convert to standard format
                for item in parsed:
                    result = {
                        "url": item.get("url", ""),
                        "result_text": item.get("title", "") + "\n" + item.get("snippet", ""),
                        "snippet": item.get("snippet", ""),
                    }
                    if result["url"]:  # Only add if we have a URL
                        results.append(result)

            else:
                # Try to parse as simple text format
                lines = response.split("\n")
                current_result = {}

                for line in lines:
                    line = line.strip()
                    if line.startswith("http"):
                        # New URL found
                        if current_result.get("url"):
                            results.append(current_result)
                        current_result = {
                            "url": line,
                            "result_text": "",
                            "snippet": ""
                        }
                    elif current_result.get("url") and line:
                        # Add to result text
                        current_result["result_text"] += line + "\n"
                        if not current_result["snippet"]:
                            current_result["snippet"] = line

                # Add last result
                if current_result.get("url"):
                    results.append(current_result)

        except Exception as e:
            logger.warning(f"Failed to parse search results: {e}")
            # Return empty list if parsing fails
            return []

        logger.debug(f"Parsed {len(results)} search results from agent response")
        return results

    def search_and_parse(
        self,
        queries: List[str],
        max_results_per_query: Optional[int] = None,
    ) -> List[CompanyInfo]:
        """Search for queries and parse results into CompanyInfo.

        This is the primary method that combines search and parsing into a
        single operation.

        Args:
            queries: List of search query strings
            max_results_per_query: Optional override for max results per query

        Returns:
            list: Deduplicated list of CompanyInfo instances

        Raises:
            RuntimeError: If search or parsing fails

        Example:
            >>> engine = WebSearchEngine(agent)
            >>> queries = ["SaaS marketing companies", "email automation providers"]
            >>> companies = engine.search_and_parse(queries)
            >>> print(len(companies))
            8
            >>> print(companies[0].name)
            'Acme Marketing Automation'
        """
        try:
            # Perform searches
            logger.info(f"Searching and parsing {len(queries)} queries")
            search_results = self.search(queries, max_results_per_query)

            if not search_results:
                logger.warning("No search results found")
                return []

            # Parse search results into CompanyInfo
            companies = self.parser.parse_multiple_results(search_results)

            # Deduplicate companies
            unique_companies = self.parser.deduplicate_companies(companies)

            logger.info(
                f"Search and parse complete: {len(unique_companies)} unique companies "
                f"from {len(search_results)} results"
            )

            return unique_companies

        except Exception as e:
            error_msg = f"Search and parse operation failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def set_max_results(self, max_results: int) -> None:
        """Set the maximum number of results per query.

        Args:
            max_results: Maximum results per query (recommended: 3-10)

        Raises:
            ValueError: If max_results is less than 1
        """
        if max_results < 1:
            raise ValueError("max_results must be at least 1")

        self.max_results_per_query = max_results
        logger.info(f"Max results per query set to {max_results}")
