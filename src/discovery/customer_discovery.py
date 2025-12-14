"""Customer discovery orchestrator that coordinates search, filtering, and enrichment.

This module provides the CustomerDiscovery class that orchestrates the complete
customer discovery pipeline: query generation -> web search -> relevance filtering
-> enrichment -> ranked results.
"""

import logging
from typing import Optional, Dict, Any, List

from ..agent.discovery_agent import DiscoveryAgent
from ..agent.query_builder import QueryBuilder
from .web_search import WebSearchEngine
from .relevance_scorer import RelevanceScorer
from ..models.business_context import BusinessContext
from ..models.discovery_results import DiscoveryResult, CompanyInfo


logger = logging.getLogger(__name__)


class CustomerDiscovery:
    """Orchestrates customer discovery workflow.

    This class coordinates the complete customer discovery pipeline:
    1. Generate targeted search queries using QueryBuilder
    2. Execute web searches using WebSearchEngine
    3. Filter candidates by relevance to business context
    4. Enrich top candidates with additional details
    5. Return top N qualified candidates as DiscoveryResult

    Example:
        >>> from src.agent.discovery_agent import DiscoveryAgent
        >>> from src.agent.query_builder import QueryBuilder
        >>> from src.discovery.web_search import WebSearchEngine
        >>> from src.models.business_context import BusinessContext
        >>>
        >>> agent = DiscoveryAgent()
        >>> query_builder = QueryBuilder()
        >>> search_engine = WebSearchEngine(agent)
        >>> discovery = CustomerDiscovery(agent, search_engine, query_builder)
        >>>
        >>> context = BusinessContext(
        ...     industry="SaaS - Marketing Automation",
        ...     target_market="B2B - SMB marketing agencies"
        ... )
        >>> result = discovery.discover(context, target_count=10)
        >>> print(len(result.companies))
        10
    """

    def __init__(
        self,
        agent: DiscoveryAgent,
        search_engine: WebSearchEngine,
        query_builder: QueryBuilder,
    ):
        """Initialize the customer discovery orchestrator.

        Args:
            agent: DiscoveryAgent instance for AI operations
            search_engine: WebSearchEngine instance for searching
            query_builder: QueryBuilder instance for query generation

        Raises:
            ValueError: If any required dependency is None
        """
        if agent is None:
            raise ValueError("agent cannot be None")
        if search_engine is None:
            raise ValueError("search_engine cannot be None")
        if query_builder is None:
            raise ValueError("query_builder cannot be None")

        self.agent = agent
        self.search_engine = search_engine
        self.query_builder = query_builder
        self.relevance_scorer = RelevanceScorer(agent)

        logger.info("CustomerDiscovery initialized")

    def discover(
        self,
        context: BusinessContext,
        filters: Optional[Dict[str, Any]] = None,
        target_count: int = 10,
    ) -> DiscoveryResult:
        """Execute the complete customer discovery pipeline.

        This method orchestrates the full workflow:
        1. Generate customer-focused search queries
        2. Search the web for potential customers
        3. Filter by relevance (keep top 15-20)
        4. Enrich top candidates with additional details
        5. Return top N (target_count) as DiscoveryResult

        Args:
            context: BusinessContext with company information
            filters: Optional filters to narrow search:
                - geography: str or list of geographic regions
                - industry: str or list of industries to target
                - size: Company size range
            target_count: Number of final results to return (default: 10)

        Returns:
            DiscoveryResult: Discovery result with top qualified customer candidates

        Raises:
            RuntimeError: If discovery pipeline fails
            ValueError: If context is None

        Example:
            >>> discovery = CustomerDiscovery(agent, search_engine, query_builder)
            >>> context = BusinessContext(industry="SaaS")
            >>> result = discovery.discover(context, target_count=10)
            >>> print(f"Found {len(result.companies)} customers")
            Found 10 customers
        """
        if context is None:
            raise ValueError("context cannot be None")

        if filters is None:
            filters = {}

        logger.info(f"Starting customer discovery (target: {target_count} results)")

        try:
            # Step 1: Generate customer queries
            logger.info("Step 1: Generating customer search queries")
            queries = self.query_builder.build_customer_queries(context, filters)
            logger.info(f"Generated {len(queries)} search queries: {queries}")

            # Step 2: Execute web search
            logger.info("Step 2: Executing web searches")
            candidates = self.search_engine.search_and_parse(queries)
            logger.info(f"Found {len(candidates)} initial candidates from web search")

            if not candidates:
                logger.warning("No candidates found from web search")
                return DiscoveryResult(
                    entity_type="customer",
                    companies=[],
                    query_used=", ".join(queries),
                )

            # Step 3: Filter by relevance (keep 15-20 candidates)
            logger.info("Step 3: Filtering candidates by relevance")
            relevant_candidates = self._filter_by_relevance(candidates, context)
            logger.info(
                f"Filtered to {len(relevant_candidates)} relevant candidates "
                f"(from {len(candidates)})"
            )

            if not relevant_candidates:
                logger.warning("No relevant candidates after filtering")
                return DiscoveryResult(
                    entity_type="customer",
                    companies=[],
                    query_used=", ".join(queries),
                )

            # Step 4: Enrich top candidates
            logger.info(f"Step 4: Enriching top {target_count} candidates")
            top_candidates = relevant_candidates[:target_count]
            enriched_candidates = []

            for i, candidate in enumerate(top_candidates, 1):
                logger.info(f"Enriching candidate {i}/{len(top_candidates)}: {candidate.name}")
                enriched = self._enrich_company_info(candidate)
                enriched_candidates.append(enriched)

            logger.info(f"Enriched {len(enriched_candidates)} candidates")

            # Step 5: Create and return DiscoveryResult
            result = DiscoveryResult(
                entity_type="customer",
                companies=enriched_candidates,
                query_used=", ".join(queries),
            )

            logger.info(
                f"Customer discovery completed: {len(result.companies)} qualified candidates"
            )
            return result

        except Exception as e:
            error_msg = f"Customer discovery failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _filter_by_relevance(
        self, candidates: List[CompanyInfo], context: BusinessContext
    ) -> List[CompanyInfo]:
        """Filter candidates by relevance to business context.

        Uses RelevanceScorer to score each candidate and filter out low-relevance
        matches. Keeps candidates with score >= 0.6 (RELEVANCE_THRESHOLD).
        Returns top 15-20 candidates for efficiency.

        Args:
            candidates: List of CompanyInfo candidates
            context: BusinessContext for relevance scoring

        Returns:
            list: Filtered list of relevant CompanyInfo instances (top 15-20)

        Example:
            >>> candidates = [company1, company2, company3]
            >>> context = BusinessContext(industry="SaaS")
            >>> relevant = discovery._filter_by_relevance(candidates, context)
            >>> print(len(relevant))
            15
        """
        logger.info(f"Filtering {len(candidates)} candidates by relevance")

        # Use RelevanceScorer to score all candidates
        scored_candidates = self.relevance_scorer.batch_score(
            candidates, context, entity_type="customer"
        )

        # Filter by relevance threshold (>= 0.6)
        relevant_candidates = self.relevance_scorer.filter_by_threshold(
            scored_candidates,
            threshold=RelevanceScorer.RELEVANCE_THRESHOLD,
        )

        # Limit to 15-20 candidates for enrichment efficiency
        # (We'll enrich only top 10, but keeping 15-20 gives us buffer)
        max_candidates = 20
        filtered = relevant_candidates[:max_candidates]

        logger.info(
            f"Filtered to {len(filtered)} relevant candidates "
            f"(threshold >= {RelevanceScorer.RELEVANCE_THRESHOLD})"
        )
        return filtered

    def _enrich_company_info(self, company: CompanyInfo) -> CompanyInfo:
        """Enrich company information with additional details.

        Uses the agent with web search to find more complete information about
        the company, including fuller description and precise location data.

        Args:
            company: CompanyInfo to enrich

        Returns:
            CompanyInfo: Enriched company information

        Example:
            >>> company = CompanyInfo(name="Acme Corp", website="acme.com")
            >>> enriched = discovery._enrich_company_info(company)
            >>> print(enriched.description)
            'Acme Corp is a leading provider of...'
        """
        logger.info(f"Enriching company info for: {company.name}")

        try:
            # Create enrichment prompt
            enrichment_prompt = f"""Find additional information about this company:

Company Name: {company.name}
Website: {company.website}
Current Description: {company.description}
Current Locations: {', '.join(company.locations) if company.locations else 'Unknown'}

Please search for and provide:
1. A fuller, more detailed description of what the company does
2. Precise location information (headquarters, major offices)
3. Company size estimate (if available)

Return the information in JSON format:
{{
  "description": "detailed description...",
  "locations": ["location1", "location2"],
  "size_estimate": "Small/Medium/Large or number of employees"
}}
"""

            # Use agent to enrich
            response = self.agent._generate_content(
                system_prompt=enrichment_prompt,
                user_input=f"Search for information about {company.name}",
                operation="enrich_company",
            )

            # Try to parse enrichment response
            import json

            enriched_data = {}
            if "{" in response and "}" in response:
                try:
                    json_start = response.index("{")
                    json_end = response.rindex("}") + 1
                    json_str = response[json_start:json_end]
                    enriched_data = json.loads(json_str)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse enrichment JSON: {e}")

            # Update company info with enriched data
            if enriched_data:
                if "description" in enriched_data and enriched_data["description"]:
                    company.description = enriched_data["description"]

                if "locations" in enriched_data and enriched_data["locations"]:
                    company.locations = enriched_data["locations"]

                if "size_estimate" in enriched_data and enriched_data["size_estimate"]:
                    company.size_estimate = enriched_data["size_estimate"]

                logger.info(f"Successfully enriched {company.name}")
            else:
                logger.warning(f"No enrichment data found for {company.name}")

            return company

        except Exception as e:
            logger.warning(f"Enrichment failed for {company.name}: {e}")
            # Return original company info if enrichment fails
            return company
