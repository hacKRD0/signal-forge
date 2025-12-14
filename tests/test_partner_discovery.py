"""Tests for the PartnerDiscovery class."""

import unittest
from unittest.mock import Mock, MagicMock, patch

from src.discovery.partner_discovery import PartnerDiscovery
from src.agent.discovery_agent import DiscoveryAgent
from src.agent.query_builder import QueryBuilder
from src.discovery.web_search import WebSearchEngine
from src.models.business_context import BusinessContext
from src.models.discovery_results import CompanyInfo, DiscoveryResult


class TestPartnerDiscovery(unittest.TestCase):
    """Test cases for PartnerDiscovery class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock dependencies
        self.mock_agent = Mock(spec=DiscoveryAgent)
        self.mock_search_engine = Mock(spec=WebSearchEngine)
        self.mock_query_builder = Mock(spec=QueryBuilder)

        # Create test business context
        self.test_context = BusinessContext(
            company_name="Test SaaS Co",
            industry="SaaS - Marketing Automation",
            products_services=["Email platform", "Analytics"],
            target_market="B2B - SMB marketing agencies",
            geography=["North America"],
            key_strengths=["AI-powered optimization"],
        )

    def test_partner_discovery_initialization(self):
        """Test PartnerDiscovery initialization."""
        discovery = PartnerDiscovery(
            self.mock_agent, self.mock_search_engine, self.mock_query_builder
        )

        self.assertEqual(discovery.agent, self.mock_agent)
        self.assertEqual(discovery.search_engine, self.mock_search_engine)
        self.assertEqual(discovery.query_builder, self.mock_query_builder)
        self.assertIsNotNone(discovery.relevance_scorer)

    def test_partner_discovery_initialization_null_agent(self):
        """Test PartnerDiscovery raises ValueError with null agent."""
        with self.assertRaises(ValueError) as context:
            PartnerDiscovery(None, self.mock_search_engine, self.mock_query_builder)

        self.assertIn("agent cannot be None", str(context.exception))

    def test_partner_discovery_initialization_null_search_engine(self):
        """Test PartnerDiscovery raises ValueError with null search engine."""
        with self.assertRaises(ValueError) as context:
            PartnerDiscovery(self.mock_agent, None, self.mock_query_builder)

        self.assertIn("search_engine cannot be None", str(context.exception))

    def test_partner_discovery_initialization_null_query_builder(self):
        """Test PartnerDiscovery raises ValueError with null query builder."""
        with self.assertRaises(ValueError) as context:
            PartnerDiscovery(self.mock_agent, self.mock_search_engine, None)

        self.assertIn("query_builder cannot be None", str(context.exception))

    def test_discover_workflow_mock(self):
        """Test the complete partner discovery workflow with mocks."""
        # Setup discovery
        discovery = PartnerDiscovery(
            self.mock_agent, self.mock_search_engine, self.mock_query_builder
        )

        # Mock partner query generation (different from customer queries)
        partner_queries = [
            "companies partnering with SaaS businesses in North America",
            "companies integrating with email platform in North America",
            "technology integration partners in North America",
        ]
        self.mock_query_builder.build_partner_queries.return_value = partner_queries

        # Mock search results
        mock_companies = [
            CompanyInfo(
                name="CRM Integration Co",
                website="https://crmintegration.com",
                description="CRM software with integration APIs",
            ),
            CompanyInfo(
                name="Analytics Platform Inc",
                website="https://analyticsplatform.com",
                description="Data analytics platform for marketing",
            ),
            CompanyInfo(
                name="Email Deliverability Service",
                website="https://emaildelivery.com",
                description="Email deliverability and compliance service",
            ),
        ]
        self.mock_search_engine.search_and_parse.return_value = mock_companies

        # Mock partnership scoring (using partner-specific scoring)
        with patch.object(discovery.relevance_scorer, "batch_score") as mock_batch_score:
            # High scores for complementary businesses
            mock_batch_score.return_value = [
                (mock_companies[0], 0.85),  # CRM - complementary
                (mock_companies[1], 0.75),  # Analytics - complementary
                (mock_companies[2], 0.70),  # Email - complementary
            ]

            with patch.object(
                discovery.relevance_scorer, "filter_by_threshold"
            ) as mock_filter:
                mock_filter.return_value = mock_companies  # All pass threshold

                # Mock enrichment
                with patch.object(discovery, "_enrich_partner_info") as mock_enrich:
                    mock_enrich.side_effect = lambda c: c  # Return unchanged

                    # Execute discovery
                    result = discovery.discover(self.test_context, target_count=3)

                    # Verify partner query generation was used
                    self.mock_query_builder.build_partner_queries.assert_called_once_with(
                        self.test_context, {}
                    )

                    # Verify search was executed
                    self.mock_search_engine.search_and_parse.assert_called_once_with(
                        partner_queries
                    )

                    # Verify partnership scoring was used (not customer scoring)
                    mock_batch_score.assert_called_once()
                    call_args = mock_batch_score.call_args
                    self.assertEqual(call_args[0][1], self.test_context)
                    self.assertEqual(
                        call_args[1]["entity_type"], "partner"
                    )  # Key difference

                    # Verify result
                    self.assertIsInstance(result, DiscoveryResult)
                    self.assertEqual(result.entity_type, "partner")
                    self.assertEqual(len(result.companies), 3)

    def test_partnership_filtering(self):
        """Test that partnership potential filtering works correctly."""
        discovery = PartnerDiscovery(
            self.mock_agent, self.mock_search_engine, self.mock_query_builder
        )

        # Create companies with varied partnership potential
        companies = [
            CompanyInfo(
                name="Direct Competitor Email Co",
                website="https://competitor.com",
                description="Email marketing automation platform",  # Direct competitor
            ),
            CompanyInfo(
                name="Complementary CRM",
                website="https://crm.com",
                description="CRM software with integration APIs",  # Good partner
            ),
            CompanyInfo(
                name="Unrelated Hardware Store",
                website="https://hardware.com",
                description="Hardware retail store",  # No synergy
            ),
        ]

        # Mock scoring with partnership criteria
        with patch.object(discovery.relevance_scorer, "batch_score") as mock_batch_score:
            # Score based on partnership potential (complementary fit, not customer need)
            mock_batch_score.return_value = [
                (companies[1], 0.85),  # Complementary CRM - high score
                (companies[0], 0.30),  # Direct competitor - low score
                (companies[2], 0.20),  # Unrelated - very low score
            ]

            with patch.object(
                discovery.relevance_scorer, "filter_by_threshold"
            ) as mock_filter:
                # Only CRM passes threshold (0.6)
                mock_filter.return_value = [companies[1]]

                # Execute filtering
                result = discovery._filter_by_partnership_potential(
                    companies, self.test_context
                )

                # Verify partnership scoring was used
                mock_batch_score.assert_called_once()
                call_args = mock_batch_score.call_args
                self.assertEqual(call_args[1]["entity_type"], "partner")

                # Verify only complementary partner passed
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].name, "Complementary CRM")

    def test_discover_with_filters(self):
        """Test partner discovery with filters."""
        discovery = PartnerDiscovery(
            self.mock_agent, self.mock_search_engine, self.mock_query_builder
        )

        filters = {
            "geography": "Europe",
            "partnership_type": "technology",
        }

        # Mock query builder with filters
        self.mock_query_builder.build_partner_queries.return_value = [
            "technology partnership opportunities in Europe"
        ]

        # Mock empty search results
        self.mock_search_engine.search_and_parse.return_value = []

        # Execute discovery
        result = discovery.discover(self.test_context, filters=filters, target_count=5)

        # Verify filters were passed to query builder
        self.mock_query_builder.build_partner_queries.assert_called_once_with(
            self.test_context, filters
        )

        # Verify empty result handling
        self.assertEqual(len(result.companies), 0)
        self.assertEqual(result.entity_type, "partner")

    def test_discover_raises_value_error_for_null_context(self):
        """Test discover raises ValueError for null context."""
        discovery = PartnerDiscovery(
            self.mock_agent, self.mock_search_engine, self.mock_query_builder
        )

        with self.assertRaises(ValueError) as context:
            discovery.discover(None)

        self.assertIn("context cannot be None", str(context.exception))

    def test_enrich_partner_info(self):
        """Test partner enrichment focuses on partnership aspects."""
        discovery = PartnerDiscovery(
            self.mock_agent, self.mock_search_engine, self.mock_query_builder
        )

        company = CompanyInfo(
            name="Test Partner Co",
            website="https://testpartner.com",
            description="Short description",
        )

        # Mock agent enrichment response
        enrichment_response = """{
  "description": "Detailed description with partnership info",
  "locations": ["San Francisco", "New York"],
  "size_estimate": "100-200 employees"
}"""
        self.mock_agent._generate_content.return_value = enrichment_response

        # Execute enrichment
        enriched = discovery._enrich_partner_info(company)

        # Verify enrichment was called with partnership-focused prompt
        self.mock_agent._generate_content.assert_called_once()
        call_args = self.mock_agent._generate_content.call_args
        prompt = call_args[1]["system_prompt"]
        self.assertIn("partner", prompt.lower())
        self.assertIn("partnership", prompt.lower())

        # Verify enrichment updated the company
        self.assertEqual(enriched.description, "Detailed description with partnership info")
        self.assertEqual(enriched.locations, ["San Francisco", "New York"])
        self.assertEqual(enriched.size_estimate, "100-200 employees")


if __name__ == "__main__":
    unittest.main()
