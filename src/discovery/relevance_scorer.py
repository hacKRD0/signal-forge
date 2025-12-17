"""Relevance scoring for customer and partner discovery.

This module provides the RelevanceScorer class that uses AI to score how relevant
a discovered company is as a potential customer or partner based on business context.
"""

import logging
from typing import List, Tuple, Dict, Any

from ..agent.discovery_agent import DiscoveryAgent
from ..models.business_context import BusinessContext
from ..models.discovery_results import CompanyInfo


logger = logging.getLogger(__name__)


class RelevanceScorer:
    """Score company relevance as potential customers or partners.

    This class uses the DiscoveryAgent to score how well a discovered company
    matches the business context as a potential customer or partner. Scores
    range from 0.0 (not relevant) to 1.0 (highly relevant).

    Relevance threshold: >= 0.3 is considered relevant

    Example:
        >>> from src.agent.discovery_agent import DiscoveryAgent
        >>> from src.models.business_context import BusinessContext
        >>> from src.models.discovery_results import CompanyInfo
        >>>
        >>> agent = DiscoveryAgent()
        >>> scorer = RelevanceScorer(agent)
        >>>
        >>> context = BusinessContext(
        ...     industry="SaaS - Marketing Automation",
        ...     target_market="B2B - SMB marketing agencies"
        ... )
        >>> company = CompanyInfo(
        ...     name="ABC Marketing Agency",
        ...     description="Small marketing agency specializing in digital campaigns"
        ... )
        >>> score = scorer.score_customer_relevance(company, context)
        >>> print(f"Relevance score: {score}")
        Relevance score: 0.85
    """

    RELEVANCE_THRESHOLD = 0.3  # Minimum score to be considered relevant

    def __init__(self, agent: DiscoveryAgent):
        """Initialize the relevance scorer.

        Args:
            agent: DiscoveryAgent instance for scoring operations

        Raises:
            ValueError: If agent is None
        """
        if agent is None:
            raise ValueError("agent cannot be None")

        self.agent = agent
        self._score_cache: Dict[str, float] = {}  # Cache to avoid re-scoring

        logger.info("RelevanceScorer initialized with threshold=0.3")

    def score_customer_relevance(
        self, company: CompanyInfo, context: BusinessContext
    ) -> float:
        """Score a company's relevance as a potential customer.

        Uses the agent to analyze the company against the business context and
        return a relevance score from 0.0 to 1.0.

        Args:
            company: CompanyInfo to score
            context: BusinessContext to score against

        Returns:
            float: Relevance score from 0.0 (not relevant) to 1.0 (highly relevant)

        Raises:
            ValueError: If company or context is None
            RuntimeError: If scoring fails

        Example:
            >>> scorer = RelevanceScorer(agent)
            >>> score = scorer.score_customer_relevance(company, context)
            >>> print(score >= RelevanceScorer.RELEVANCE_THRESHOLD)
            True
        """
        if company is None:
            raise ValueError("company cannot be None")
        if context is None:
            raise ValueError("context cannot be None")

        # Check cache first
        cache_key = self._make_cache_key(company, context, "customer")
        if cache_key in self._score_cache:
            logger.debug(f"Using cached score for {company.name}")
            return self._score_cache[cache_key]

        logger.info(f"Scoring customer relevance for: {company.name}")

        try:
            # Create scoring prompt
            scoring_prompt = f"""Score this company as a potential customer on a scale of 0.0 to 1.0.

**Business Context (Our Company):**
- Industry: {context.industry or 'N/A'}
- Products/Services: {', '.join(context.products_services) if context.products_services else 'N/A'}
- Target Market: {context.target_market or 'N/A'}
- Geography: {', '.join(context.geography) if context.geography else 'N/A'}

**Company to Score (Potential Customer):**
- Name: {company.name}
- Website: {company.website}
- Description: {company.description or 'N/A'}
- Locations: {', '.join(company.locations) if company.locations else 'N/A'}
- Size: {company.size_estimate}

**Scoring Guidelines:**
- 0.9-1.0: Perfect match - Company clearly needs our products/services, perfect fit for target market
- 0.7-0.8: Strong match - Company is in target market and would benefit from our offerings
- 0.6: Good match - Company is relevant but not ideal
- 0.4-0.5: Weak match - Some relevance but not in core target market
- 0.0-0.3: Poor match - Not in target market or unlikely to need our products/services

**Threshold: Scores >= 0.6 are considered relevant**

Return ONLY a JSON object with your score and brief reasoning:
{{
  "score": 0.85,
  "reasoning": "Brief explanation of why this score was given"
}}
"""

            # Use agent to score
            response = self.agent._generate_content(
                system_prompt=scoring_prompt,
                user_input=f"Score {company.name} as a potential customer",
                operation="score_customer_relevance",
            )

            # Parse score from response
            score = self._parse_score(response)

            # Cache the score
            self._score_cache[cache_key] = score

            logger.info(f"Scored {company.name}: {score:.2f}")
            return score

        except Exception as e:
            error_msg = f"Failed to score customer relevance for {company.name}: {e}"
            logger.error(error_msg)
            # Return neutral score on error to avoid losing candidates
            return 0.5

    def score_partner_relevance(
        self, company: CompanyInfo, context: BusinessContext
    ) -> float:
        """Score a company's relevance as a potential partner.

        Uses the agent to analyze the company against the business context and
        return a partnership relevance score from 0.0 to 1.0. Partnership scoring
        focuses on complementary fit, not customer need.

        Args:
            company: CompanyInfo to score
            context: BusinessContext to score against

        Returns:
            float: Partnership relevance score from 0.0 (not relevant) to 1.0 (highly relevant)

        Raises:
            ValueError: If company or context is None
            RuntimeError: If scoring fails

        Example:
            >>> scorer = RelevanceScorer(agent)
            >>> score = scorer.score_partner_relevance(company, context)
            >>> print(score >= RelevanceScorer.RELEVANCE_THRESHOLD)
            True
        """
        if company is None:
            raise ValueError("company cannot be None")
        if context is None:
            raise ValueError("context cannot be None")

        # Check cache first
        cache_key = self._make_cache_key(company, context, "partner")
        if cache_key in self._score_cache:
            logger.debug(f"Using cached score for {company.name}")
            return self._score_cache[cache_key]

        logger.info(f"Scoring partner relevance for: {company.name}")

        try:
            # Create partnership scoring prompt
            scoring_prompt = f"""Score this company as a potential partner on a scale of 0.0 to 1.0.

**Business Context (Our Company):**
- Industry: {context.industry or 'N/A'}
- Products/Services: {', '.join(context.products_services) if context.products_services else 'N/A'}
- Target Market: {context.target_market or 'N/A'}
- Geography: {', '.join(context.geography) if context.geography else 'N/A'}
- Key Strengths: {', '.join(context.key_strengths) if context.key_strengths else 'N/A'}

**Company to Score (Potential Partner):**
- Name: {company.name}
- Website: {company.website}
- Description: {company.description or 'N/A'}
- Locations: {', '.join(company.locations) if company.locations else 'N/A'}
- Size: {company.size_estimate}

**Partnership Scoring Guidelines:**
- 0.9-1.0: Excellent fit - Highly complementary services, strong integration opportunities, shared target market
- 0.7-0.8: Strong fit - Good synergies, compatible business models, clear partnership value
- 0.6: Good fit - Some complementary aspects, reasonable partnership potential
- 0.4-0.5: Weak fit - Limited synergies or unclear partnership value
- 0.0-0.3: Poor fit - Direct competitor, conflicting services, or no complementary value

**Evaluation Criteria:**
1. Complementary services (do they offer services that complement ours?)
2. Integration opportunities (could our products/services integrate?)
3. Shared target market (do we serve similar customer segments?)
4. Compatible business models (are our approaches compatible?)
5. NOT direct competitors (avoid companies offering identical services)

**Threshold: Scores >= 0.6 are considered relevant**

Return ONLY a JSON object with your score and brief reasoning:
{{
  "score": 0.85,
  "reasoning": "Brief explanation of partnership potential and complementary fit"
}}
"""

            # Use agent to score
            response = self.agent._generate_content(
                system_prompt=scoring_prompt,
                user_input=f"Score {company.name} as a potential partner",
                operation="score_partner_relevance",
            )

            # Parse score from response
            score = self._parse_score(response)

            # Cache the score
            self._score_cache[cache_key] = score

            logger.info(f"Scored {company.name}: {score:.2f}")
            return score

        except Exception as e:
            error_msg = f"Failed to score partner relevance for {company.name}: {e}"
            logger.error(error_msg)
            # Return neutral score on error to avoid losing candidates
            return 0.5

    def batch_score(
        self,
        companies: List[CompanyInfo],
        context: BusinessContext,
        entity_type: str = "customer",
    ) -> List[Tuple[CompanyInfo, float]]:
        """Score multiple companies efficiently.

        Scores all companies and returns them sorted by score (highest first).

        Args:
            companies: List of CompanyInfo instances to score
            context: BusinessContext to score against
            entity_type: Type of entity ("customer" or "partner")

        Returns:
            list: List of (company, score) tuples sorted by score descending

        Raises:
            ValueError: If companies or context is None

        Example:
            >>> scorer = RelevanceScorer(agent)
            >>> companies = [company1, company2, company3]
            >>> scored = scorer.batch_score(companies, context)
            >>> print(f"Top company: {scored[0][0].name}, score: {scored[0][1]}")
            Top company: ABC Corp, score: 0.92
        """
        if companies is None:
            raise ValueError("companies cannot be None")
        if context is None:
            raise ValueError("context cannot be None")

        logger.info(f"Batch scoring {len(companies)} companies as {entity_type}s")

        scored_companies = []

        for company in companies:
            try:
                if entity_type == "customer":
                    score = self.score_customer_relevance(company, context)
                elif entity_type == "partner":
                    score = self.score_partner_relevance(company, context)
                else:
                    logger.warning(f"Unknown entity_type '{entity_type}', defaulting to customer")
                    score = self.score_customer_relevance(company, context)

                scored_companies.append((company, score))

            except Exception as e:
                logger.warning(f"Failed to score {company.name}: {e}")
                # Add with neutral score to avoid losing the company
                scored_companies.append((company, 0.5))

        # Sort by score descending
        scored_companies.sort(key=lambda x: x[1], reverse=True)

        logger.info(
            f"Batch scoring complete. Top score: {scored_companies[0][1]:.2f}, "
            f"Lowest score: {scored_companies[-1][1]:.2f}"
        )

        return scored_companies

    def filter_by_threshold(
        self,
        scored_companies: List[Tuple[CompanyInfo, float]],
        threshold: float = RELEVANCE_THRESHOLD,
    ) -> List[CompanyInfo]:
        """Filter scored companies by relevance threshold.

        Args:
            scored_companies: List of (company, score) tuples
            threshold: Minimum score to keep (default: 0.6)

        Returns:
            list: Filtered list of CompanyInfo instances with score >= threshold

        Example:
            >>> scored = [(company1, 0.9), (company2, 0.5), (company3, 0.7)]
            >>> filtered = scorer.filter_by_threshold(scored, threshold=0.3)
            >>> print(len(filtered))
            2
        """
        filtered = [company for company, score in scored_companies if score >= threshold]

        logger.info(
            f"Filtered {len(scored_companies)} companies to {len(filtered)} "
            f"with threshold >= {threshold:.2f}"
        )

        return filtered

    def _parse_score(self, response: str) -> float:
        """Parse relevance score from agent response.

        Extracts the numeric score from the agent's response. Handles both
        JSON format and plain text formats.

        Args:
            response: Agent response text

        Returns:
            float: Parsed score (0.0-1.0), or 0.5 if parsing fails

        Example:
            >>> score = scorer._parse_score('{"score": 0.85, "reasoning": "..."}')
            >>> print(score)
            0.85
        """
        import json
        import re

        try:
            # Try to parse as JSON first
            if "{" in response and "}" in response:
                json_start = response.index("{")
                json_end = response.rindex("}") + 1
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                if "score" in data:
                    score = float(data["score"])
                    # Clamp to 0.0-1.0 range
                    return max(0.0, min(1.0, score))

            # Try to find a decimal number in the response
            score_pattern = r'\b([0-1]?\.\d+|0|1)\b'
            matches = re.findall(score_pattern, response)

            if matches:
                # Take the first match that's in valid range
                for match in matches:
                    score = float(match)
                    if 0.0 <= score <= 1.0:
                        return score

            # If no valid score found, return neutral score
            logger.warning(f"Could not parse score from response: {response[:100]}")
            return 0.5

        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            logger.warning(f"Score parsing failed: {e}")
            return 0.5

    def _make_cache_key(
        self, company: CompanyInfo, context: BusinessContext, entity_type: str
    ) -> str:
        """Create a cache key for score caching.

        Args:
            company: CompanyInfo instance
            context: BusinessContext instance
            entity_type: Type of entity ("customer" or "partner")

        Returns:
            str: Cache key string
        """
        # Simple cache key based on company name and context industry
        key = f"{entity_type}:{company.name.lower()}:{context.industry.lower()}"
        return key

    def clear_cache(self) -> None:
        """Clear the score cache.

        Useful when you want to re-score companies with updated context.
        """
        self._score_cache.clear()
        logger.info("Score cache cleared")

    def get_cache_size(self) -> int:
        """Get the number of cached scores.

        Returns:
            int: Number of cached score entries
        """
        return len(self._score_cache)
