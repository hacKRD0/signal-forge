"""Rationale generation for customer and partner matches.

This module implements the RationaleGenerator class which uses AI to create
structured, human-readable explanations for match scores.
"""

import json
import logging
from typing import List, Tuple

from ..agent.discovery_agent import DiscoveryAgent
from ..models.rationale import Rationale
from ..models.discovery_results import CompanyInfo
from ..models.business_context import BusinessContext
from ..models.match_score import MatchScore
from .rationale_prompts import CUSTOMER_RATIONALE_PROMPT, PARTNER_RATIONALE_PROMPT


logger = logging.getLogger(__name__)


class RationaleGenerator:
    """Generate structured rationales explaining match scores.

    This class uses AI to create detailed, entity-specific explanations of why
    discovered companies are good customer or partner matches. Rationales are
    grounded in match score breakdowns and use appropriate language for each
    entity type.

    Attributes:
        agent: DiscoveryAgent instance for AI-powered rationale generation
    """

    def __init__(self, agent: DiscoveryAgent):
        """Initialize the rationale generator.

        Args:
            agent: DiscoveryAgent instance for AI-powered generation
        """
        self.agent = agent
        logger.info("RationaleGenerator initialized")

    def generate_rationale(
        self,
        company: CompanyInfo,
        context: BusinessContext,
        score: MatchScore,
        entity_type: str = "customer"
    ) -> Rationale:
        """Generate a rationale explaining why a company is a good match.

        This method uses AI to analyze the company information, business context,
        and match scores to create a structured, human-readable explanation.

        Args:
            company: The discovered company to explain
            context: Business context for comparison
            score: Match score with component breakdown
            entity_type: Type of entity ("customer" or "partner")

        Returns:
            Rationale: Structured explanation with summary, strengths, and recommendation

        Example:
            >>> generator = RationaleGenerator(agent)
            >>> rationale = generator.generate_rationale(
            ...     company, context, score, "customer"
            ... )
            >>> print(rationale.recommendation)
            Strong Match
        """
        logger.info(
            f"Generating {entity_type} rationale for {company.name} "
            f"(score: {score.overall_score:.1f})"
        )

        try:
            # Select appropriate prompt based on entity type
            if entity_type.lower() == "partner":
                system_prompt = PARTNER_RATIONALE_PROMPT
            else:
                system_prompt = CUSTOMER_RATIONALE_PROMPT

            # Format input information
            user_input = self._format_rationale_input(company, context, score, entity_type)

            # Generate rationale using agent
            response_text = self.agent._generate_content(
                system_prompt=system_prompt,
                user_input=user_input,
                operation=f"generate_{entity_type}_rationale"
            )

            # Parse response into Rationale instance
            rationale = self._parse_rationale_response(response_text, score.overall_score)

            logger.info(
                f"Rationale generated for {company.name}: {rationale.recommendation}"
            )
            return rationale

        except Exception as e:
            logger.error(f"Failed to generate rationale for {company.name}: {e}")
            # Return a fallback rationale
            return self._create_fallback_rationale(company, score, entity_type)

    def batch_generate(
        self,
        companies_with_scores: List[Tuple[CompanyInfo, MatchScore]],
        context: BusinessContext,
        entity_type: str = "customer"
    ) -> List[Rationale]:
        """Generate rationales for multiple companies.

        This method processes a batch of companies and their scores, generating
        a rationale for each one.

        Args:
            companies_with_scores: List of (CompanyInfo, MatchScore) tuples
            context: Business context for comparison
            entity_type: Type of entity ("customer" or "partner")

        Returns:
            list: List of Rationale instances, one per company

        Example:
            >>> generator = RationaleGenerator(agent)
            >>> rationales = generator.batch_generate(
            ...     [(company1, score1), (company2, score2)],
            ...     context,
            ...     "customer"
            ... )
            >>> print(len(rationales))
            2
        """
        logger.info(
            f"Batch generating {len(companies_with_scores)} {entity_type} rationales"
        )

        rationales = []
        for company, score in companies_with_scores:
            rationale = self.generate_rationale(company, context, score, entity_type)
            rationales.append(rationale)

        logger.info(f"Batch generation complete: {len(rationales)} rationales created")
        return rationales

    def _format_rationale_input(
        self,
        company: CompanyInfo,
        context: BusinessContext,
        score: MatchScore,
        entity_type: str
    ) -> str:
        """Format input information for rationale generation.

        Args:
            company: Company information
            context: Business context
            score: Match score breakdown
            entity_type: Entity type for context

        Returns:
            str: Formatted input string for the agent
        """
        input_text = f"""**Company Information:**
Name: {company.name}
Description: {company.description}
Locations: {', '.join(company.locations) if company.locations else 'Unknown'}
Size: {company.size_estimate}
Website: {company.website}

**Business Context:**
{context.to_prompt_string()}

**Match Score Breakdown:**
Overall Score: {score.overall_score:.1f}/100
- Relevance Score: {score.relevance_score:.1f}/100
- Geographic Fit: {score.geographic_fit:.1f}/100
- Size Appropriateness: {score.size_appropriateness:.1f}/100
- Strategic Alignment: {score.strategic_alignment:.1f}/100
Confidence: {score.confidence}

**Task:**
Generate a rationale explaining why {company.name} is a {'good ' + entity_type + ' match' if score.overall_score >= 60 else entity_type + ' prospect to consider'}."""

        return input_text

    def _parse_rationale_response(self, response_text: str, overall_score: float) -> Rationale:
        """Parse agent response into a Rationale instance.

        This method extracts JSON from the response and creates a Rationale object,
        ensuring the recommendation level matches the overall score.

        Args:
            response_text: Raw response from agent
            overall_score: Overall match score for recommendation determination

        Returns:
            Rationale: Parsed rationale instance

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Extract JSON from response
            if "{" in response_text and "}" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

            # Create Rationale instance
            rationale = Rationale.from_dict(data)

            # Ensure recommendation matches score threshold
            rationale.recommendation = self._determine_recommendation(overall_score)

            return rationale

        except Exception as e:
            logger.error(f"Failed to parse rationale response: {e}")
            raise ValueError(f"Could not parse rationale: {e}")

    def _determine_recommendation(self, overall_score: float) -> str:
        """Determine recommendation level based on overall score.

        Args:
            overall_score: Overall match score (0-100)

        Returns:
            str: Recommendation level (Strong Match/Good Match/Fair Match)
        """
        if overall_score >= 80:
            return "Strong Match"
        elif overall_score >= 60:
            return "Good Match"
        else:
            return "Fair Match"

    def _create_fallback_rationale(
        self,
        company: CompanyInfo,
        score: MatchScore,
        entity_type: str
    ) -> Rationale:
        """Create a fallback rationale when AI generation fails.

        This creates a basic rationale based on score components without AI.

        Args:
            company: Company information
            score: Match score
            entity_type: Entity type

        Returns:
            Rationale: Fallback rationale instance
        """
        logger.warning(f"Creating fallback rationale for {company.name}")

        # Determine recommendation
        recommendation = self._determine_recommendation(score.overall_score)

        # Build basic summary
        if entity_type.lower() == "partner":
            summary = f"Partnership opportunity with {company.name} based on score analysis"
        else:
            summary = f"Customer prospect {company.name} identified through scoring"

        # Build key strengths from top scores
        key_strengths = []
        if score.relevance_score >= 70:
            key_strengths.append(
                f"High relevance score ({score.relevance_score:.0f}/100) indicates strong business fit"
            )
        if score.geographic_fit >= 70:
            key_strengths.append(
                f"Good geographic alignment ({score.geographic_fit:.0f}/100)"
            )
        if score.size_appropriateness >= 70:
            key_strengths.append(
                f"Appropriate company size ({score.size_appropriateness:.0f}/100)"
            )
        if score.strategic_alignment >= 70:
            key_strengths.append(
                f"Strong strategic fit ({score.strategic_alignment:.0f}/100)"
            )

        if not key_strengths:
            key_strengths.append(f"Overall match score of {score.overall_score:.0f}/100")

        # Build fit explanation
        fit_explanation = (
            f"With an overall score of {score.overall_score:.1f}/100, this "
            f"{entity_type} shows {recommendation.lower()} potential. "
            f"Score confidence: {score.confidence}."
        )

        # Build concerns
        potential_concerns = []
        if score.confidence == "Low":
            potential_concerns.append("Limited data available for comprehensive assessment")

        return Rationale(
            summary=summary,
            key_strengths=key_strengths,
            fit_explanation=fit_explanation,
            potential_concerns=potential_concerns,
            recommendation=recommendation
        )
