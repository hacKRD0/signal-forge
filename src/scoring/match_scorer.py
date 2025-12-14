"""Match scoring algorithm for customer and partner discovery.

This module implements multi-dimensional scoring for discovered companies,
evaluating relevance, geographic fit, size appropriateness, and strategic alignment.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher

from ..models.match_score import MatchScore
from ..models.discovery_results import CompanyInfo
from ..models.business_context import BusinessContext
from ..agent.discovery_agent import DiscoveryAgent


logger = logging.getLogger(__name__)


class MatchScorer:
    """Multi-dimensional scoring algorithm for discovered companies.

    This class evaluates how well discovered customers or partners match the
    business context across four key dimensions:
    - Relevance: AI-powered assessment of business relevance
    - Geographic fit: Location alignment with target geography
    - Size appropriateness: Company size fit with target market
    - Strategic alignment: Strategic fit and complementary capabilities

    The overall score is a weighted average:
    - Relevance: 40%
    - Geographic fit: 20%
    - Size appropriateness: 20%
    - Strategic alignment: 20%

    Attributes:
        agent: DiscoveryAgent instance for AI-powered scoring
        weights: Dictionary of component weights for overall score calculation
    """

    # Default weights for score components
    DEFAULT_WEIGHTS = {
        "relevance": 0.40,
        "geographic": 0.20,
        "size": 0.20,
        "strategic": 0.20,
    }

    def __init__(self, agent: DiscoveryAgent):
        """Initialize the match scorer.

        Args:
            agent: DiscoveryAgent instance for AI-powered relevance scoring
        """
        self.agent = agent
        self.weights = self.DEFAULT_WEIGHTS.copy()
        logger.info("MatchScorer initialized with default weights")

    def score_match(
        self,
        company: CompanyInfo,
        context: BusinessContext,
        entity_type: str = "customer"
    ) -> MatchScore:
        """Calculate comprehensive match score for a discovered company.

        This method evaluates the company across all scoring dimensions and
        computes a weighted overall score with confidence level.

        Args:
            company: The discovered company to score
            context: Business context for comparison
            entity_type: Type of entity ("customer" or "partner")

        Returns:
            MatchScore: Complete match score with component breakdown

        Example:
            >>> scorer = MatchScorer(agent)
            >>> score = scorer.score_match(company, context, "customer")
            >>> print(f"Match score: {score.overall_score}%")
            Match score: 85.0%
        """
        logger.info(f"Scoring {entity_type} match for company: {company.name}")

        # Calculate individual component scores
        relevance_score = self._calculate_relevance_score(company, context, entity_type)
        geographic_fit = self._calculate_geographic_fit(company.locations, context.geography)
        size_fit = self._calculate_size_fit(company.size_estimate, context)
        strategic_fit = self._calculate_strategic_alignment(company, context, entity_type)

        # Calculate weighted overall score
        overall_score = (
            self.weights["relevance"] * relevance_score +
            self.weights["geographic"] * geographic_fit +
            self.weights["size"] * size_fit +
            self.weights["strategic"] * strategic_fit
        )

        # Determine confidence level based on data completeness
        confidence = self._determine_confidence(company, context)

        # Create score breakdown
        score_breakdown = {
            "relevance": relevance_score,
            "geographic": geographic_fit,
            "size": size_fit,
            "strategic": strategic_fit,
        }

        # Create MatchScore instance
        match_score = MatchScore(
            overall_score=overall_score,
            relevance_score=relevance_score,
            geographic_fit=geographic_fit,
            size_appropriateness=size_fit,
            strategic_alignment=strategic_fit,
            score_breakdown=score_breakdown,
            confidence=confidence,
        )

        logger.info(
            f"Scoring complete for {company.name}: "
            f"overall={overall_score:.1f}, confidence={confidence}"
        )

        return match_score

    def _calculate_relevance_score(
        self,
        company: CompanyInfo,
        context: BusinessContext,
        entity_type: str
    ) -> float:
        """Calculate AI-powered relevance score.

        Uses the DiscoveryAgent to evaluate how relevant the company is to
        the business context and needs.

        Args:
            company: The discovered company
            context: Business context
            entity_type: Type of entity ("customer" or "partner")

        Returns:
            float: Relevance score (0-100)
        """
        try:
            # Create a prompt for relevance scoring
            prompt = f"""Evaluate the relevance of this company as a potential {entity_type}.

Business Context:
{context.to_prompt_string()}

Company Information:
Name: {company.name}
Description: {company.description}
Locations: {', '.join(company.locations) if company.locations else 'Unknown'}
Size: {company.size_estimate}

Rate the relevance on a scale of 0-100, where:
- 0-20: Not relevant at all
- 21-40: Slightly relevant
- 41-60: Moderately relevant
- 61-80: Highly relevant
- 81-100: Extremely relevant

Provide ONLY a numeric score between 0 and 100."""

            # Use agent to generate relevance score
            response = self.agent._generate_content(
                system_prompt="You are a business analyst evaluating company matches.",
                user_input=prompt,
                operation="calculate_relevance"
            )

            # Extract numeric score from response
            score = self._extract_numeric_score(response)
            logger.debug(f"AI relevance score for {company.name}: {score}")
            return score

        except Exception as e:
            logger.warning(f"Failed to calculate AI relevance score: {e}. Using fallback.")
            # Fallback: Use description similarity if AI scoring fails
            return self._fallback_relevance_score(company, context)

    def _extract_numeric_score(self, response: str) -> float:
        """Extract numeric score from agent response.

        Args:
            response: Agent response text

        Returns:
            float: Extracted score (0-100), defaults to 50 if extraction fails
        """
        try:
            # Try to find a number in the response
            import re
            numbers = re.findall(r'\b\d+(?:\.\d+)?\b', response)
            if numbers:
                score = float(numbers[0])
                # Clamp to 0-100 range
                return max(0.0, min(100.0, score))
        except Exception:
            pass

        # Default to middle score if extraction fails
        logger.warning("Could not extract numeric score from response, using default 50")
        return 50.0

    def _fallback_relevance_score(self, company: CompanyInfo, context: BusinessContext) -> float:
        """Fallback relevance scoring using text similarity.

        Args:
            company: The discovered company
            context: Business context

        Returns:
            float: Relevance score (0-100) based on text similarity
        """
        # Combine context information into a single string
        context_text = " ".join([
            context.industry,
            " ".join(context.products_services),
            context.target_market,
        ]).lower()

        # Combine company information
        company_text = f"{company.description} {company.name}".lower()

        # Calculate similarity ratio
        similarity = SequenceMatcher(None, context_text, company_text).ratio()

        # Convert to 0-100 scale
        score = similarity * 100
        logger.debug(f"Fallback relevance score for {company.name}: {score}")
        return score

    def _calculate_geographic_fit(
        self,
        company_locations: List[str],
        context_geography: List[str]
    ) -> float:
        """Calculate geographic fit score.

        Compares company locations with business context geography using
        fuzzy matching to handle variations in location names.

        Args:
            company_locations: List of company locations
            context_geography: List of target geographic regions from context

        Returns:
            float: Geographic fit score (0-100)
                - 100: Exact location overlap
                - 70-99: Partial or fuzzy match
                - 0-69: No clear overlap, scaled by similarity
        """
        if not company_locations or not context_geography:
            # No location data available
            logger.debug("Missing location data for geographic fit calculation")
            return 50.0  # Neutral score when data is missing

        # Normalize locations to lowercase for comparison
        company_locs = [loc.lower().strip() for loc in company_locations]
        context_locs = [loc.lower().strip() for loc in context_geography]

        # Check for exact matches
        exact_matches = set(company_locs) & set(context_locs)
        if exact_matches:
            logger.debug(f"Exact geographic match found: {exact_matches}")
            return 100.0

        # Check for partial matches (substring matching)
        max_similarity = 0.0
        for company_loc in company_locs:
            for context_loc in context_locs:
                # Check if one location is contained in another
                if company_loc in context_loc or context_loc in company_loc:
                    max_similarity = max(max_similarity, 0.85)
                else:
                    # Use fuzzy matching for similarity
                    similarity = SequenceMatcher(None, company_loc, context_loc).ratio()
                    max_similarity = max(max_similarity, similarity)

        # Convert similarity to score (0-100 scale)
        score = max_similarity * 100
        logger.debug(f"Geographic fit score: {score}")
        return score

    def _calculate_size_fit(self, company_size: str, context: BusinessContext) -> float:
        """Calculate size appropriateness score.

        Evaluates if the company size matches the target market described
        in the business context.

        Args:
            company_size: Company size estimate (Small/Medium/Large/Unknown)
            context: Business context with target market information

        Returns:
            float: Size fit score (0-100)
                - 100: Perfect size match
                - 70-99: Acceptable size match
                - 0-69: Size mismatch
        """
        if not company_size or company_size.lower() == "unknown":
            # No size data available
            logger.debug("Unknown company size, using neutral score")
            return 50.0

        # Normalize size
        size_normalized = company_size.lower().strip()

        # Extract target market indicators from context
        target_market = context.target_market.lower()

        # Define size matching rules
        size_indicators = {
            "small": ["smb", "small", "startup", "entrepreneur", "small business", "local"],
            "medium": ["mid-market", "medium", "growing", "regional", "middle market"],
            "large": ["enterprise", "large", "fortune", "global", "multinational", "corporation"],
        }

        # Determine target size from context
        target_size = None
        for size, indicators in size_indicators.items():
            if any(indicator in target_market for indicator in indicators):
                target_size = size
                break

        if not target_size:
            # Can't determine target size from context
            logger.debug("Cannot determine target size from context, using neutral score")
            return 50.0

        # Map company size to score based on target
        size_map = {
            "small": 0,
            "medium": 1,
            "large": 2,
        }

        company_size_value = size_map.get(size_normalized, 1)  # Default to medium
        target_size_value = size_map.get(target_size, 1)

        # Calculate score based on size difference
        size_difference = abs(company_size_value - target_size_value)

        if size_difference == 0:
            # Perfect match
            score = 100.0
        elif size_difference == 1:
            # One size off (acceptable)
            score = 70.0
        else:
            # Two sizes off (poor match)
            score = 30.0

        logger.debug(
            f"Size fit: company={size_normalized}, target={target_size}, score={score}"
        )
        return score

    def _calculate_strategic_alignment(
        self,
        company: CompanyInfo,
        context: BusinessContext,
        entity_type: str
    ) -> float:
        """Calculate strategic alignment score.

        Evaluates strategic fit based on complementary capabilities,
        market overlap, and partnership potential.

        Args:
            company: The discovered company
            context: Business context
            entity_type: Type of entity ("customer" or "partner")

        Returns:
            float: Strategic alignment score (0-100)
        """
        # For customers: Evaluate if they would benefit from our products/services
        # For partners: Evaluate complementary capabilities and synergies

        # Start with a base score
        score = 50.0

        # Factor 1: Industry alignment
        if context.industry and company.description:
            context_industry = context.industry.lower()
            company_desc = company.description.lower()

            # Extract industry keywords
            industry_keywords = context_industry.split()
            matching_keywords = sum(
                1 for keyword in industry_keywords
                if len(keyword) > 3 and keyword in company_desc
            )

            if matching_keywords > 0:
                # Boost score based on keyword matches
                score += min(30.0, matching_keywords * 10)

        # Factor 2: Product/service alignment
        if context.products_services and company.description:
            company_desc = company.description.lower()
            matching_products = 0

            for product in context.products_services:
                product_lower = product.lower()
                # Check for product mentions or related terms
                if product_lower in company_desc:
                    matching_products += 1

            if matching_products > 0:
                score += min(20.0, matching_products * 10)

        # Ensure score is within bounds
        score = max(0.0, min(100.0, score))

        logger.debug(f"Strategic alignment score for {company.name}: {score}")
        return score

    def _determine_confidence(self, company: CompanyInfo, context: BusinessContext) -> str:
        """Determine confidence level based on data completeness.

        Args:
            company: The discovered company
            context: Business context

        Returns:
            str: Confidence level ("High", "Medium", or "Low")
        """
        # Count available data points
        data_points = 0
        total_points = 0

        # Company data
        total_points += 4
        if company.name:
            data_points += 1
        if company.description:
            data_points += 1
        if company.locations:
            data_points += 1
        if company.size_estimate and company.size_estimate.lower() != "unknown":
            data_points += 1

        # Context data
        total_points += 4
        if context.industry:
            data_points += 1
        if context.products_services:
            data_points += 1
        if context.target_market:
            data_points += 1
        if context.geography:
            data_points += 1

        # Calculate completeness ratio
        completeness = data_points / total_points if total_points > 0 else 0

        # Determine confidence level
        if completeness >= 0.75:
            confidence = "High"
        elif completeness >= 0.50:
            confidence = "Medium"
        else:
            confidence = "Low"

        logger.debug(
            f"Confidence determination: {data_points}/{total_points} "
            f"data points available ({completeness:.1%}) -> {confidence}"
        )

        return confidence
