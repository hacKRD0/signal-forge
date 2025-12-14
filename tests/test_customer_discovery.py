"""Tests for customer discovery orchestration.

This module tests the CustomerDiscovery class and its integration with
RelevanceScorer, WebSearchEngine, and QueryBuilder.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.discovery.customer_discovery import CustomerDiscovery
from src.discovery.relevance_scorer import RelevanceScorer
from src.agent.discovery_agent import DiscoveryAgent
from src.agent.query_builder import QueryBuilder
from src.discovery.web_search import WebSearchEngine
from src.models.business_context import BusinessContext
from src.models.discovery_results import CompanyInfo, DiscoveryResult


class TestCustomerDiscoveryInitialization:
    """Tests for CustomerDiscovery initialization."""

    def test_customer_discovery_initialization(self):
        """Test that CustomerDiscovery initializes correctly."""
        # Create mock dependencies
        agent = Mock(spec=DiscoveryAgent)
        search_engine = Mock(spec=WebSearchEngine)
        query_builder = Mock(spec=QueryBuilder)

        # Initialize CustomerDiscovery
        discovery = CustomerDiscovery(agent, search_engine, query_builder)

        # Verify initialization
        assert discovery.agent is agent
        assert discovery.search_engine is search_engine
        assert discovery.query_builder is query_builder
        assert isinstance(discovery.relevance_scorer, RelevanceScorer)

    def test_initialization_requires_agent(self):
        """Test that initialization fails without agent."""
        search_engine = Mock(spec=WebSearchEngine)
        query_builder = Mock(spec=QueryBuilder)

        with pytest.raises(ValueError, match="agent cannot be None"):
            CustomerDiscovery(None, search_engine, query_builder)

    def test_initialization_requires_search_engine(self):
        """Test that initialization fails without search_engine."""
        agent = Mock(spec=DiscoveryAgent)
        query_builder = Mock(spec=QueryBuilder)

        with pytest.raises(ValueError, match="search_engine cannot be None"):
            CustomerDiscovery(agent, None, query_builder)

    def test_initialization_requires_query_builder(self):
        """Test that initialization fails without query_builder."""
        agent = Mock(spec=DiscoveryAgent)
        search_engine = Mock(spec=WebSearchEngine)

        with pytest.raises(ValueError, match="query_builder cannot be None"):
            CustomerDiscovery(agent, search_engine, None)


class TestCustomerDiscoveryWorkflow:
    """Tests for customer discovery workflow with mocks."""

    def test_discover_workflow_mock(self):
        """Test the complete discover workflow with mocked dependencies."""
        # Create mock dependencies
        agent = Mock(spec=DiscoveryAgent)
        search_engine = Mock(spec=WebSearchEngine)
        query_builder = Mock(spec=QueryBuilder)

        # Setup mock data
        context = BusinessContext(
            company_name="Test Corp",
            industry="SaaS - Marketing Automation",
            products_services=["Email platform", "Analytics"],
            target_market="B2B - SMB marketing agencies",
            geography=["North America"],
        )

        # Mock query generation
        mock_queries = ["SMB marketing agencies in North America", "marketing automation customers"]
        query_builder.build_customer_queries.return_value = mock_queries

        # Mock search results (20 candidates)
        mock_candidates = [
            CompanyInfo(
                name=f"Company {i}",
                website=f"https://company{i}.com",
                description=f"Marketing agency {i}",
                locations=["New York"],
                size_estimate="Small",
            )
            for i in range(20)
        ]
        search_engine.search_and_parse.return_value = mock_candidates

        # Mock agent enrichment responses
        agent._generate_content.return_value = '{"description": "Enriched description", "locations": ["New York, NY"], "size_estimate": "50-100 employees"}'

        # Create discovery instance
        discovery = CustomerDiscovery(agent, search_engine, query_builder)

        # Mock the relevance scorer to return high scores for first 15 companies
        with patch.object(discovery.relevance_scorer, 'batch_score') as mock_batch_score:
            # Create scored candidates (first 15 have high scores, rest have low scores)
            scored = [(company, 0.8 if i < 15 else 0.4) for i, company in enumerate(mock_candidates)]
            mock_batch_score.return_value = scored

            # Execute discovery
            result = discovery.discover(context, target_count=10)

            # Verify workflow steps
            # 1. Query generation was called
            query_builder.build_customer_queries.assert_called_once_with(context, {})

            # 2. Search was executed with queries
            search_engine.search_and_parse.assert_called_once_with(mock_queries)

            # 3. Relevance scoring was performed
            mock_batch_score.assert_called_once()

            # 4. Result is DiscoveryResult
            assert isinstance(result, DiscoveryResult)
            assert result.entity_type == "customer"

            # 5. Result contains companies (up to 10)
            assert len(result.companies) <= 10
            assert all(isinstance(c, CompanyInfo) for c in result.companies)

            # 6. Enrichment was called for each final candidate
            # (agent._generate_content called for each enrichment)
            assert agent._generate_content.call_count == len(result.companies)

    def test_discover_with_filters(self):
        """Test discovery with filters applied."""
        # Create mock dependencies
        agent = Mock(spec=DiscoveryAgent)
        search_engine = Mock(spec=WebSearchEngine)
        query_builder = Mock(spec=QueryBuilder)

        context = BusinessContext(industry="SaaS")
        filters = {"geography": "Europe", "industry": "Healthcare"}

        # Mock query generation
        query_builder.build_customer_queries.return_value = ["Healthcare SaaS in Europe"]

        # Mock search results
        search_engine.search_and_parse.return_value = []

        # Create discovery instance
        discovery = CustomerDiscovery(agent, search_engine, query_builder)

        # Execute discovery with filters
        result = discovery.discover(context, filters=filters, target_count=5)

        # Verify filters were passed to query builder
        query_builder.build_customer_queries.assert_called_once_with(context, filters)

        # Verify result
        assert isinstance(result, DiscoveryResult)
        assert len(result.companies) == 0  # No results from mock

    def test_discover_no_candidates_found(self):
        """Test discovery when no candidates are found."""
        # Create mock dependencies
        agent = Mock(spec=DiscoveryAgent)
        search_engine = Mock(spec=WebSearchEngine)
        query_builder = Mock(spec=QueryBuilder)

        context = BusinessContext(industry="SaaS")

        # Mock query generation
        mock_queries = ["SaaS companies"]
        query_builder.build_customer_queries.return_value = mock_queries

        # Mock search returns no results
        search_engine.search_and_parse.return_value = []

        # Create discovery instance
        discovery = CustomerDiscovery(agent, search_engine, query_builder)

        # Execute discovery
        result = discovery.discover(context, target_count=10)

        # Verify result is empty but valid
        assert isinstance(result, DiscoveryResult)
        assert result.entity_type == "customer"
        assert len(result.companies) == 0
        assert result.query_used == ", ".join(mock_queries)


class TestRelevanceFiltering:
    """Tests for relevance filtering logic."""

    def test_relevance_filtering(self):
        """Test that relevance filtering keeps high-relevance, removes low-relevance."""
        # Create mock dependencies
        agent = Mock(spec=DiscoveryAgent)
        search_engine = Mock(spec=WebSearchEngine)
        query_builder = Mock(spec=QueryBuilder)

        # Create discovery instance
        discovery = CustomerDiscovery(agent, search_engine, query_builder)

        # Create mock companies with varied relevance
        context = BusinessContext(industry="SaaS")
        companies = [
            CompanyInfo(name="High Relevance 1", website="high1.com"),
            CompanyInfo(name="High Relevance 2", website="high2.com"),
            CompanyInfo(name="Low Relevance 1", website="low1.com"),
            CompanyInfo(name="Low Relevance 2", website="low2.com"),
            CompanyInfo(name="High Relevance 3", website="high3.com"),
        ]

        # Mock the relevance scorer
        with patch.object(discovery.relevance_scorer, 'batch_score') as mock_batch_score, \
             patch.object(discovery.relevance_scorer, 'filter_by_threshold') as mock_filter:

            # Mock batch_score returns scores
            scored = [
                (companies[0], 0.9),  # High
                (companies[1], 0.8),  # High
                (companies[2], 0.4),  # Low (below 0.6)
                (companies[3], 0.3),  # Low (below 0.6)
                (companies[4], 0.7),  # High
            ]
            mock_batch_score.return_value = scored

            # Mock filter_by_threshold returns only high-relevance
            high_relevance = [companies[0], companies[1], companies[4]]
            mock_filter.return_value = high_relevance

            # Call filter method
            filtered = discovery._filter_by_relevance(companies, context)

            # Verify batch_score was called
            mock_batch_score.assert_called_once_with(companies, context, entity_type="customer")

            # Verify filter_by_threshold was called
            mock_filter.assert_called_once_with(scored, threshold=RelevanceScorer.RELEVANCE_THRESHOLD)

            # Verify only high-relevance companies returned
            assert len(filtered) == 3
            assert all(c.name.startswith("High Relevance") for c in filtered)


class TestEnrichment:
    """Tests for company enrichment."""

    def test_enrich_company_info(self):
        """Test enriching a single company."""
        # Create mock dependencies
        agent = Mock(spec=DiscoveryAgent)
        search_engine = Mock(spec=WebSearchEngine)
        query_builder = Mock(spec=QueryBuilder)

        # Create discovery instance
        discovery = CustomerDiscovery(agent, search_engine, query_builder)

        # Create company to enrich
        company = CompanyInfo(
            name="Test Corp",
            website="testcorp.com",
            description="Original description",
            locations=["Unknown"],
            size_estimate="Unknown",
        )

        # Mock enrichment response
        enrichment_json = {
            "description": "Test Corp is a leading provider of test solutions",
            "locations": ["San Francisco, CA", "New York, NY"],
            "size_estimate": "200-500 employees"
        }
        agent._generate_content.return_value = f'{enrichment_json}'

        # Enrich company
        enriched = discovery._enrich_company_info(company)

        # Verify enrichment was called
        assert agent._generate_content.called

        # Verify company is returned (even if enrichment fails)
        assert enriched is company

    def test_enrich_handles_failure_gracefully(self):
        """Test that enrichment failure doesn't break the pipeline."""
        # Create mock dependencies
        agent = Mock(spec=DiscoveryAgent)
        search_engine = Mock(spec=WebSearchEngine)
        query_builder = Mock(spec=QueryBuilder)

        # Create discovery instance
        discovery = CustomerDiscovery(agent, search_engine, query_builder)

        # Create company to enrich
        company = CompanyInfo(name="Test Corp", website="testcorp.com")

        # Mock enrichment to raise exception
        agent._generate_content.side_effect = Exception("Enrichment failed")

        # Enrich company - should not raise exception
        enriched = discovery._enrich_company_info(company)

        # Verify original company is returned
        assert enriched is company
        assert enriched.name == "Test Corp"


@pytest.mark.skip(reason="Requires API key - integration test")
class TestCustomerDiscoveryIntegration:
    """Integration tests for customer discovery (requires API key)."""

    def test_full_customer_discovery_integration(self):
        """Test full customer discovery workflow with real components.

        This test is skipped by default as it requires:
        - Valid Google ADK API key
        - Network access for web search
        - May take several minutes to complete

        To run: pytest tests/test_customer_discovery.py::TestCustomerDiscoveryIntegration -v
        """
        # Create real components (requires API key)
        agent = DiscoveryAgent(enable_web_search=True)
        query_builder = QueryBuilder()
        search_engine = WebSearchEngine(agent)
        discovery = CustomerDiscovery(agent, search_engine, query_builder)

        # Create test context
        context = BusinessContext(
            company_name="Test Marketing Platform",
            industry="SaaS - Marketing Automation",
            products_services=["Email marketing", "Social media management"],
            target_market="B2B - Small marketing agencies",
            geography=["United States"],
        )

        # Execute discovery (target 5 for faster test)
        result = discovery.discover(context, target_count=5)

        # Verify results
        assert isinstance(result, DiscoveryResult)
        assert result.entity_type == "customer"
        assert len(result.companies) <= 5
        assert all(isinstance(c, CompanyInfo) for c in result.companies)

        # Verify companies have required fields
        for company in result.companies:
            assert company.name
            assert company.website or company.description
