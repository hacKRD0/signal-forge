"""Tests for query formulation logic."""

import pytest
from src.agent.query_builder import QueryBuilder
from src.models.business_context import BusinessContext


class TestQueryBuilder:
    """Test suite for QueryBuilder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = QueryBuilder()

        # Sample business context for SaaS company
        self.saas_context = BusinessContext(
            company_name="CloudFlow",
            industry="SaaS - Marketing Automation",
            products_services=["Email marketing platform", "Lead scoring tools", "Analytics dashboard"],
            target_market="B2B - Small to medium-sized marketing agencies",
            geography=["North America", "Europe"],
            key_strengths=["AI-powered optimization", "Easy integration"],
            additional_notes="Series A funded, 50-100 employees"
        )

    def test_customer_query_generation(self):
        """Test generating customer search queries."""
        queries = self.builder.build_customer_queries(self.saas_context)

        # Should return 3-5 queries
        assert 3 <= len(queries) <= 5, f"Expected 3-5 queries, got {len(queries)}"

        # Queries should not be empty
        assert all(queries), "All queries should be non-empty strings"

        # Queries should be unique
        assert len(queries) == len(set(queries)), "Queries should be unique"

        # Queries should contain relevant context information
        queries_text = " ".join(queries).lower()
        assert any(term in queries_text for term in ["marketing", "b2b", "agencies"]), \
            "Queries should contain relevant context terms"

    def test_partner_query_generation(self):
        """Test generating partner search queries."""
        queries = self.builder.build_partner_queries(self.saas_context)

        # Should return 3-5 queries
        assert 3 <= len(queries) <= 5, f"Expected 3-5 queries, got {len(queries)}"

        # Queries should not be empty
        assert all(queries), "All queries should be non-empty strings"

        # Queries should be unique
        assert len(queries) == len(set(queries)), "Queries should be unique"

        # Partner queries should differ from customer queries in focus
        queries_text = " ".join(queries).lower()
        # Should focus on partnerships, integration, complementary
        assert any(term in queries_text for term in ["partner", "integration", "integrating", "complementary"]), \
            "Partner queries should focus on partnership concepts"

    def test_customer_vs_partner_queries_differ(self):
        """Test that customer and partner queries have different strategies."""
        customer_queries = self.builder.build_customer_queries(self.saas_context)
        partner_queries = self.builder.build_partner_queries(self.saas_context)

        # The sets should not be identical
        assert set(customer_queries) != set(partner_queries), \
            "Customer and partner queries should use different strategies"

    def test_query_refinement_with_geography_filter(self):
        """Test query refinement with geography filter."""
        base_query = "marketing agencies"
        filters = {"geography": "California"}

        refined = self.builder.refine_query(base_query, filters)

        assert "California" in refined, "Refined query should include geography"
        assert "marketing agencies" in refined, "Refined query should retain base query"

    def test_query_refinement_with_industry_filter(self):
        """Test query refinement with industry filter."""
        base_query = "companies needing automation"
        filters = {"industry": "Healthcare"}

        refined = self.builder.refine_query(base_query, filters)

        assert "Healthcare" in refined, "Refined query should include industry"
        assert "automation" in refined, "Refined query should retain base query"

    def test_query_refinement_with_multiple_filters(self):
        """Test query refinement with multiple filters."""
        base_query = "marketing agencies"
        filters = {
            "geography": "North America",
            "industry": "Technology"
        }

        refined = self.builder.refine_query(base_query, filters)

        # Should include at least one filter
        assert "North America" in refined or "Technology" in refined, \
            "Refined query should include filter information"

    def test_empty_filters_handling(self):
        """Test that empty filters don't cause errors."""
        # Test with None filters
        queries = self.builder.build_customer_queries(self.saas_context, filters=None)
        assert len(queries) >= 3, "Should generate queries with None filters"

        # Test with empty dict filters
        queries = self.builder.build_customer_queries(self.saas_context, filters={})
        assert len(queries) >= 3, "Should generate queries with empty filters"

        # Test refine_query with empty filters
        refined = self.builder.refine_query("test query", {})
        assert refined == "test query", "Should return original query with empty filters"

    def test_customer_queries_with_geography_filter(self):
        """Test customer queries with geography filter."""
        filters = {"geography": "Europe"}
        queries = self.builder.build_customer_queries(self.saas_context, filters)

        # At least some queries should mention geography
        queries_text = " ".join(queries).lower()
        assert "europe" in queries_text, "Queries should incorporate geography filter"

    def test_customer_queries_with_industry_filter(self):
        """Test customer queries with industry filter."""
        filters = {"industry": ["Healthcare", "Finance"]}
        queries = self.builder.build_customer_queries(self.saas_context, filters)

        # At least some queries should mention the filtered industries
        queries_text = " ".join(queries).lower()
        assert any(term in queries_text for term in ["healthcare", "finance"]), \
            "Queries should incorporate industry filter"

    def test_partner_queries_with_partnership_type_filter(self):
        """Test partner queries with partnership_type filter."""
        filters = {"partnership_type": "technology"}
        queries = self.builder.build_partner_queries(self.saas_context, filters)

        # Should include the partnership type in queries
        queries_text = " ".join(queries).lower()
        assert "technology" in queries_text, \
            "Partner queries should incorporate partnership_type filter"

    def test_minimal_context(self):
        """Test query generation with minimal business context."""
        minimal_context = BusinessContext(
            industry="Technology"
        )

        # Should still generate queries without errors
        customer_queries = self.builder.build_customer_queries(minimal_context)
        assert len(customer_queries) >= 3, "Should generate queries with minimal context"

        partner_queries = self.builder.build_partner_queries(minimal_context)
        assert len(partner_queries) >= 3, "Should generate queries with minimal context"

    def test_no_duplicate_queries(self):
        """Test that no duplicate queries are generated."""
        # Run multiple times to check consistency
        for _ in range(3):
            customer_queries = self.builder.build_customer_queries(self.saas_context)
            assert len(customer_queries) == len(set(customer_queries)), \
                "Customer queries should not contain duplicates"

            partner_queries = self.builder.build_partner_queries(self.saas_context)
            assert len(partner_queries) == len(set(partner_queries)), \
                "Partner queries should not contain duplicates"

    def test_query_length_reasonable(self):
        """Test that queries are not too long (reduces search effectiveness)."""
        customer_queries = self.builder.build_customer_queries(self.saas_context)
        partner_queries = self.builder.build_partner_queries(self.saas_context)

        all_queries = customer_queries + partner_queries

        # Queries should generally be under 100 characters for best search results
        for query in all_queries:
            assert len(query) < 150, f"Query too long: {query} ({len(query)} chars)"

    def test_geography_list_handling(self):
        """Test handling of geography as a list in filters."""
        filters = {"geography": ["United States", "Canada", "Mexico"]}
        queries = self.builder.build_customer_queries(self.saas_context, filters)

        queries_text = " ".join(queries)
        # Should include at least the first couple of geographies
        assert any(geo in queries_text for geo in ["United States", "Canada"]), \
            "Should handle geography list in filters"
