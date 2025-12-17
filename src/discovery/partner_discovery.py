"""Partner discovery orchestrator that coordinates search, filtering, and enrichment.

This module provides the PartnerDiscovery class that orchestrates the complete
partner discovery pipeline: query generation -> web search -> relevance filtering
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
from ..scoring.match_scorer import MatchScorer
from ..scoring.rationale_generator import RationaleGenerator


logger = logging.getLogger(__name__)


class PartnerDiscovery:
    """Orchestrates partner discovery workflow.

    This class coordinates the complete partner discovery pipeline:
    1. Generate targeted search queries using QueryBuilder (partner-focused)
    2. Execute web searches using WebSearchEngine
    3. Filter candidates by partnership potential to business context
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
        >>> discovery = PartnerDiscovery(agent, search_engine, query_builder)
        >>>
        >>> context = BusinessContext(
        ...     industry="SaaS - Marketing Automation",
        ...     products_services=["Email platform", "Analytics"]
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
        scorer: MatchScorer,
        rationale_gen: RationaleGenerator,
    ):
        """Initialize the partner discovery orchestrator.

        Args:
            agent: DiscoveryAgent instance for AI operations
            search_engine: WebSearchEngine instance for searching
            query_builder: QueryBuilder instance for query generation
            scorer: MatchScorer instance for scoring matches
            rationale_gen: RationaleGenerator instance for generating explanations

        Raises:
            ValueError: If any required dependency is None
        """
        if agent is None:
            raise ValueError("agent cannot be None")
        if search_engine is None:
            raise ValueError("search_engine cannot be None")
        if query_builder is None:
            raise ValueError("query_builder cannot be None")
        if scorer is None:
            raise ValueError("scorer cannot be None")
        if rationale_gen is None:
            raise ValueError("rationale_gen cannot be None")

        self.agent = agent
        self.search_engine = search_engine
        self.query_builder = query_builder
        self.relevance_scorer = RelevanceScorer(agent)
        self.scorer = scorer
        self.rationale_gen = rationale_gen

        logger.info("PartnerDiscovery initialized")

    def discover(
        self,
        context: BusinessContext,
        filters: Optional[Dict[str, Any]] = None,
        target_count: int = 10,
    ) -> DiscoveryResult:
        """Execute the complete partner discovery pipeline.

        This method orchestrates the full workflow:
        1. Generate partner-focused search queries (complementary businesses)
        2. Search the web for potential partners
        3. Filter by partnership potential (keep top 15-20)
        4. Enrich top candidates with additional details
        5. Return top N (target_count) as DiscoveryResult

        Args:
            context: BusinessContext with company information
            filters: Optional filters to narrow search:
                - geography: str or list of geographic regions
                - industry: str or list of industries to target
                - partnership_type: Type of partnership (e.g., "technology", "distribution")
            target_count: Number of final results to return (default: 10)

        Returns:
            DiscoveryResult: Discovery result with top qualified partner candidates

        Raises:
            RuntimeError: If discovery pipeline fails
            ValueError: If context is None

        Example:
            >>> discovery = PartnerDiscovery(agent, search_engine, query_builder)
            >>> context = BusinessContext(industry="SaaS")
            >>> result = discovery.discover(context, target_count=10)
            >>> print(f"Found {len(result.companies)} partners")
            Found 10 partners
        """
        if context is None:
            raise ValueError("context cannot be None")

        if filters is None:
            filters = {}

        logger.info(f"Starting partner discovery (target: {target_count} results)")

        try:
            # Step 1: Generate partner queries (different from customer queries)
            logger.info("Step 1: Generating partner search queries")
            queries = self.query_builder.build_partner_queries(context, filters)
            logger.info(f"Generated {len(queries)} search queries: {queries}")

            # Step 2: Execute web search
            logger.info("Step 2: Executing web searches")
            candidates = self.search_engine.search_and_parse(queries)
            logger.info(f"Found {len(candidates)} initial candidates from web search")

            if not candidates:
                logger.warning("No candidates found from web search")
                return DiscoveryResult(
                    entity_type="partner",
                    companies=[],
                    query_used=", ".join(queries),
                )

            # Step 3: Filter by partnership potential (keep 15-20 candidates)
            logger.info("Step 3: Filtering candidates by partnership potential")
            relevant_candidates = self._filter_by_partnership_potential(candidates, context)
            logger.info(
                f"Filtered to {len(relevant_candidates)} relevant candidates "
                f"(from {len(candidates)})"
            )

            if not relevant_candidates:
                logger.warning("No relevant candidates after filtering")
                return DiscoveryResult(
                    entity_type="partner",
                    companies=[],
                    query_used=", ".join(queries),
                )

            # Step 4: Score top candidates
            logger.info(f"Step 4: Scoring top {target_count} candidates")
            top_candidates = relevant_candidates[:target_count]
            scored_candidates = []

            for i, candidate in enumerate(top_candidates, 1):
                logger.info(f"Scoring candidate {i}/{len(top_candidates)}: {candidate.name}")
                # Score the match (using entity_type="partner")
                match_score = self.scorer.score_match(candidate, context, "partner")
                candidate.match_score = match_score
                scored_candidates.append(candidate)

            logger.info(f"Scored {len(scored_candidates)} candidates")

            # Step 5: Enrich candidates
            logger.info(f"Step 5: Enriching {len(scored_candidates)} candidates")
            enriched_candidates = []

            for i, candidate in enumerate(scored_candidates, 1):
                logger.info(f"Enriching candidate {i}/{len(scored_candidates)}: {candidate.name}")
                enriched = self._enrich_partner_info(candidate)
                enriched_candidates.append(enriched)

            logger.info(f"Enriched {len(enriched_candidates)} candidates")

            # Step 6: Generate rationales
            logger.info(f"Step 6: Generating rationales for {len(enriched_candidates)} candidates")
            for i, candidate in enumerate(enriched_candidates, 1):
                logger.info(f"Generating rationale {i}/{len(enriched_candidates)}: {candidate.name}")
                rationale = self.rationale_gen.generate_rationale(
                    candidate, context, candidate.match_score, "partner"
                )
                candidate.rationale = rationale

            logger.info(f"Generated {len(enriched_candidates)} rationales")

            # Step 7: Sort by overall score (descending - best matches first)
            logger.info("Step 7: Sorting results by match score")
            enriched_candidates.sort(
                key=lambda c: c.match_score.overall_score if c.match_score else 0.0,
                reverse=True
            )

            # Calculate average score
            total_score = sum(
                c.match_score.overall_score for c in enriched_candidates if c.match_score
            )
            avg_score = total_score / len(enriched_candidates) if enriched_candidates else 0.0

            # Step 8: Create and return DiscoveryResult
            result = DiscoveryResult(
                entity_type="partner",
                companies=enriched_candidates,
                query_used=", ".join(queries),
                scored=True,
                avg_score=avg_score,
            )

            logger.info(
                f"Partner discovery completed: {len(result.companies)} qualified candidates, "
                f"avg score: {avg_score:.1f}"
            )
            return result

        except Exception as e:
            error_msg = f"Partner discovery failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _filter_by_partnership_potential(
        self, candidates: List[CompanyInfo], context: BusinessContext
    ) -> List[CompanyInfo]:
        """Filter candidates by partnership potential to business context.

        Uses RelevanceScorer to score each candidate based on partnership fit
        (complementary services, integration opportunities, shared target market).
        Keeps candidates with score >= 0.3 (RELEVANCE_THRESHOLD).
        Returns top 15-20 candidates for efficiency.

        Args:
            candidates: List of CompanyInfo candidates
            context: BusinessContext for partnership scoring

        Returns:
            list: Filtered list of relevant CompanyInfo instances (top 15-20)

        Example:
            >>> candidates = [company1, company2, company3]
            >>> context = BusinessContext(industry="SaaS")
            >>> relevant = discovery._filter_by_partnership_potential(candidates, context)
            >>> print(len(relevant))
            15
        """
        logger.info(f"Filtering {len(candidates)} candidates by partnership potential")

        # Use RelevanceScorer to score all candidates as partners
        scored_candidates = self.relevance_scorer.batch_score(
            candidates, context, entity_type="partner"
        )

        # Filter by relevance threshold (>= 0.3)
        relevant_candidates = self.relevance_scorer.filter_by_threshold(
            scored_candidates,
            threshold=RelevanceScorer.RELEVANCE_THRESHOLD,
        )

        # Limit to top 10 candidates
        max_candidates = 10
        filtered = relevant_candidates[:max_candidates]

        logger.info(
            f"Filtered to {len(filtered)} relevant candidates "
            f"(threshold >= {RelevanceScorer.RELEVANCE_THRESHOLD})"
        )
        return filtered

    def _enrich_partner_info(self, company: CompanyInfo) -> CompanyInfo:
        """Enrich partner information with additional details.

        Uses the agent with web search to find more complete information about
        the potential partner, focusing on partnership aspects like integration
        capabilities and complementary offerings.

        Args:
            company: CompanyInfo to enrich

        Returns:
            CompanyInfo: Enriched company information

        Example:
            >>> company = CompanyInfo(name="Acme Corp", website="acme.com")
            >>> enriched = discovery._enrich_partner_info(company)
            >>> print(enriched.description)
            'Acme Corp is a leading provider of...'
        """
        logger.info(f"Enriching partner info for: {company.name}")

        try:
            # Create enrichment prompt focused on partnership aspects
            enrichment_prompt = f"""Find additional information about this potential partner company:

Company Name: {company.name}
Website: {company.website}
Current Description: {company.description}
Current Locations: {', '.join(company.locations) if company.locations else 'Unknown'}

Please search for and provide:
1. A fuller, more detailed description of what the company does
2. Precise location information (headquarters, major offices)
3. Company size estimate (if available)
4. Any information about partnerships, integrations, or partner programs

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
                operation="enrich_partner",
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
