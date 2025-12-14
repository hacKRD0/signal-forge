"""Discovery engine runner for UI integration.

This module provides the run_discovery function that initializes all required
components and executes the discovery pipeline from the UI.
"""

import logging
from typing import Dict, Any, Optional

from src.models.business_context import BusinessContext
from src.models.discovery_results import DiscoveryResult
from src.agent.discovery_agent import DiscoveryAgent
from src.agent.query_builder import QueryBuilder
from src.discovery.web_search import WebSearchEngine
from src.discovery.customer_discovery import CustomerDiscovery
from src.discovery.partner_discovery import PartnerDiscovery
from src.scoring.match_scorer import MatchScorer
from src.scoring.rationale_generator import RationaleGenerator


logger = logging.getLogger(__name__)


def run_discovery(
    entity_type: str,
    context: BusinessContext,
    filters: Optional[Dict[str, Any]] = None,
    target_count: int = 10
) -> DiscoveryResult:
    """Execute the discovery pipeline for customers or partners.

    This function initializes all required components (DiscoveryAgent, QueryBuilder,
    WebSearchEngine, MatchScorer, RationaleGenerator) and runs the appropriate
    discovery engine (CustomerDiscovery or PartnerDiscovery) with the provided
    context and filters.

    Args:
        entity_type: Type of entity to discover - "Customer" or "Partner"
        context: BusinessContext object containing business information
        filters: Optional dictionary with discovery filters:
            - "geography": list of geographic regions
            - "industry": list of industries
        target_count: Number of results to return (default: 10)

    Returns:
        DiscoveryResult: The discovery results including found companies,
                        scores, and rationales

    Raises:
        ValueError: If entity_type is not "Customer" or "Partner"
        RuntimeError: If discovery process fails
    """
    if entity_type not in ["Customer", "Partner"]:
        raise ValueError(f"Invalid entity_type: {entity_type}. Must be 'Customer' or 'Partner'")

    if context is None:
        raise ValueError("context cannot be None")

    if filters is None:
        filters = {}

    logger.info(f"Starting {entity_type} discovery with context: {context.company_name}")
    logger.info(f"Filters: {filters}")

    try:
        # Initialize components
        logger.info("Initializing discovery components...")
        agent = DiscoveryAgent()
        query_builder = QueryBuilder()
        search_engine = WebSearchEngine(agent)
        scorer = MatchScorer(agent)
        rationale_gen = RationaleGenerator(agent)

        # Create appropriate discovery instance
        if entity_type == "Customer":
            logger.info("Using CustomerDiscovery engine")
            discovery = CustomerDiscovery(agent, search_engine, query_builder, scorer, rationale_gen)
        else:  # Partner
            logger.info("Using PartnerDiscovery engine")
            discovery = PartnerDiscovery(agent, search_engine, query_builder, scorer, rationale_gen)

        # Run discovery
        logger.info(f"Running {entity_type} discovery...")
        result = discovery.discover(context, filters=filters, target_count=target_count)

        logger.info(f"Discovery complete. Found {len(result.companies)} {entity_type.lower()}s")
        return result

    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        raise RuntimeError(f"Discovery process failed: {e}") from e
