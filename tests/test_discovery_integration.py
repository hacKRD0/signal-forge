"""Integration tests for discovery pipeline with scoring and rationale.

This module tests the complete end-to-end integration of the discovery
pipeline with scoring and rationale generation.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.discovery.customer_discovery import CustomerDiscovery
from src.discovery.partner_discovery import PartnerDiscovery
from src.models.business_context import BusinessContext
from src.models.discovery_results import CompanyInfo, DiscoveryResult
from src.models.match_score import MatchScore
from src.models.rationale import Rationale
from src.agent.discovery_agent import DiscoveryAgent
from src.agent.query_builder import QueryBuilder
from src.discovery.web_search import WebSearchEngine
from src.scoring.match_scorer import MatchScorer
from src.scoring.rationale_generator import RationaleGenerator


@pytest.fixture
def mock_business_context():
    """Create a mock business context for testing."""
    return BusinessContext(
        industry="SaaS - Marketing Automation",
        products_services=["Email Marketing", "Marketing Analytics"],
        target_market="B2B - SMB marketing agencies",
        geography=["North America"],
    )


@pytest.fixture
def mock_companies():
    """Create mock company data for testing."""
    return [
        CompanyInfo(
            name="Company A",
            website="companya.com",
            description="Marketing automation platform",
            locations=["United States"],
            size_estimate="Medium",
        ),
        CompanyInfo(
            name="Company B",
            website="companyb.com",
            description="Email marketing solution",
            locations=["Canada"],
            size_estimate="Small",
        ),
        CompanyInfo(
            name="Company C",
            website="companyc.com",
            description="Analytics platform",
            locations=["Mexico"],
            size_estimate="Large",
        ),
    ]


@pytest.fixture
def mock_match_scores():
    """Create mock match scores for testing."""
    return [
        MatchScore(
            overall_score=85.0,
            relevance_score=90.0,
            geographic_fit=80.0,
            size_appropriateness=85.0,
            strategic_alignment=85.0,
            confidence="High",
        ),
        MatchScore(
            overall_score=75.0,
            relevance_score=80.0,
            geographic_fit=70.0,
            size_appropriateness=75.0,
            strategic_alignment=75.0,
            confidence="Medium",
        ),
        MatchScore(
            overall_score=65.0,
            relevance_score=70.0,
            geographic_fit=60.0,
            size_appropriateness=65.0,
            strategic_alignment=65.0,
            confidence="Medium",
        ),
    ]


@pytest.fixture
def mock_rationales():
    """Create mock rationales for testing."""
    return [
        Rationale(
            summary="Excellent strategic fit with strong market alignment",
            key_strengths=[
                "Perfect geographic match in North America",
                "Right size company for our target market",
                "Strong relevance to our product offerings",
            ],
            fit_explanation="This company scores 85/100 overall with high confidence.",
            potential_concerns=["None identified"],
            recommendation="Strong Match",
        ),
        Rationale(
            summary="Good fit with moderate alignment",
            key_strengths=[
                "Good geographic match in North America",
                "Acceptable size for target market",
            ],
            fit_explanation="This company scores 75/100 overall with medium confidence.",
            potential_concerns=["Some gaps in strategic alignment"],
            recommendation="Good Match",
        ),
        Rationale(
            summary="Fair match with some gaps",
            key_strengths=["Relevant industry presence"],
            fit_explanation="This company scores 65/100 overall with medium confidence.",
            potential_concerns=["Geographic and size concerns"],
            recommendation="Good Match",
        ),
    ]


class TestCustomerDiscoveryIntegration:
    """Test customer discovery with scoring integration."""

    def test_customer_discovery_with_scoring(
        self, mock_business_context, mock_companies, mock_match_scores, mock_rationales
    ):
        """Test that customer discovery integrates scoring and rationale properly."""
        # Setup mocks
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_search_engine = Mock(spec=WebSearchEngine)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_scorer = Mock(spec=MatchScorer)
        mock_rationale_gen = Mock(spec=RationaleGenerator)

        # Configure mock behaviors
        mock_query_builder.build_customer_queries.return_value = ["test query"]
        mock_search_engine.search_and_parse.return_value = mock_companies.copy()

        # Mock scoring to return different scores for each company
        mock_scorer.score_match.side_effect = mock_match_scores

        # Mock rationale generation
        mock_rationale_gen.generate_rationale.side_effect = mock_rationales

        # Mock enrichment (return same company)
        mock_agent._generate_content.return_value = "{}"

        # Create CustomerDiscovery instance
        discovery = CustomerDiscovery(
            agent=mock_agent,
            search_engine=mock_search_engine,
            query_builder=mock_query_builder,
            scorer=mock_scorer,
            rationale_gen=mock_rationale_gen,
        )

        # Mock the relevance scorer to return all candidates
        with patch.object(discovery, "_filter_by_relevance") as mock_filter:
            mock_filter.return_value = mock_companies.copy()

            # Execute discovery
            result = discovery.discover(mock_business_context, target_count=3)

            # Verify result
            assert isinstance(result, DiscoveryResult)
            assert result.entity_type == "customer"
            assert result.scored is True
            assert len(result.companies) == 3

            # Verify each company has match_score and rationale
            for company in result.companies:
                assert company.match_score is not None
                assert company.rationale is not None
                assert isinstance(company.match_score, MatchScore)
                assert isinstance(company.rationale, Rationale)

            # Verify results are sorted by score (descending)
            scores = [c.match_score.overall_score for c in result.companies]
            assert scores == sorted(scores, reverse=True)

            # Verify average score calculation
            expected_avg = sum(s.overall_score for s in mock_match_scores) / 3
            assert result.avg_score == expected_avg

            # Verify scoring was called with correct entity_type
            for call_args in mock_scorer.score_match.call_args_list:
                args, kwargs = call_args
                # entity_type should be the third positional argument
                assert args[2] == "customer"

    def test_customer_discovery_sorting(
        self, mock_business_context, mock_companies, mock_match_scores, mock_rationales
    ):
        """Test that results are sorted correctly by score."""
        # Setup mocks
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_search_engine = Mock(spec=WebSearchEngine)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_scorer = Mock(spec=MatchScorer)
        mock_rationale_gen = Mock(spec=RationaleGenerator)

        # Configure mock behaviors
        mock_query_builder.build_customer_queries.return_value = ["test query"]
        mock_search_engine.search_and_parse.return_value = mock_companies.copy()
        mock_scorer.score_match.side_effect = mock_match_scores
        mock_rationale_gen.generate_rationale.side_effect = mock_rationales
        mock_agent._generate_content.return_value = "{}"

        # Create discovery instance
        discovery = CustomerDiscovery(
            agent=mock_agent,
            search_engine=mock_search_engine,
            query_builder=mock_query_builder,
            scorer=mock_scorer,
            rationale_gen=mock_rationale_gen,
        )

        # Mock relevance filter
        with patch.object(discovery, "_filter_by_relevance") as mock_filter:
            mock_filter.return_value = mock_companies.copy()

            # Execute discovery
            result = discovery.discover(mock_business_context, target_count=3)

            # Verify sorting (highest score first)
            assert result.companies[0].match_score.overall_score == 85.0
            assert result.companies[1].match_score.overall_score == 75.0
            assert result.companies[2].match_score.overall_score == 65.0


class TestPartnerDiscoveryIntegration:
    """Test partner discovery with scoring integration."""

    def test_partner_discovery_with_scoring(
        self, mock_business_context, mock_companies, mock_match_scores, mock_rationales
    ):
        """Test that partner discovery integrates scoring and rationale properly."""
        # Setup mocks
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_search_engine = Mock(spec=WebSearchEngine)
        mock_query_builder = Mock(spec=QueryBuilder)
        mock_scorer = Mock(spec=MatchScorer)
        mock_rationale_gen = Mock(spec=RationaleGenerator)

        # Configure mock behaviors
        mock_query_builder.build_partner_queries.return_value = ["test partner query"]
        mock_search_engine.search_and_parse.return_value = mock_companies.copy()
        mock_scorer.score_match.side_effect = mock_match_scores
        mock_rationale_gen.generate_rationale.side_effect = mock_rationales
        mock_agent._generate_content.return_value = "{}"

        # Create PartnerDiscovery instance
        discovery = PartnerDiscovery(
            agent=mock_agent,
            search_engine=mock_search_engine,
            query_builder=mock_query_builder,
            scorer=mock_scorer,
            rationale_gen=mock_rationale_gen,
        )

        # Mock the partnership potential filter
        with patch.object(discovery, "_filter_by_partnership_potential") as mock_filter:
            mock_filter.return_value = mock_companies.copy()

            # Execute discovery
            result = discovery.discover(mock_business_context, target_count=3)

            # Verify result
            assert isinstance(result, DiscoveryResult)
            assert result.entity_type == "partner"
            assert result.scored is True
            assert len(result.companies) == 3

            # Verify each company has match_score and rationale
            for company in result.companies:
                assert company.match_score is not None
                assert company.rationale is not None
                assert isinstance(company.match_score, MatchScore)
                assert isinstance(company.rationale, Rationale)

            # Verify results are sorted by score (descending)
            scores = [c.match_score.overall_score for c in result.companies]
            assert scores == sorted(scores, reverse=True)

            # Verify average score calculation
            expected_avg = sum(s.overall_score for s in mock_match_scores) / 3
            assert result.avg_score == expected_avg

            # Verify scoring was called with correct entity_type
            for call_args in mock_scorer.score_match.call_args_list:
                args, kwargs = call_args
                # entity_type should be the third positional argument
                assert args[2] == "partner"


class TestScoreBasedSorting:
    """Test score-based sorting functionality."""

    def test_score_based_sorting(self):
        """Test that companies are sorted correctly by overall score."""
        # Create companies with different scores
        companies = [
            CompanyInfo(name="Company A", website="a.com", match_score=MatchScore(overall_score=60.0)),
            CompanyInfo(name="Company B", website="b.com", match_score=MatchScore(overall_score=90.0)),
            CompanyInfo(name="Company C", website="c.com", match_score=MatchScore(overall_score=75.0)),
        ]

        # Sort by score (descending)
        sorted_companies = sorted(
            companies,
            key=lambda c: c.match_score.overall_score if c.match_score else 0.0,
            reverse=True,
        )

        # Verify order
        assert sorted_companies[0].name == "Company B"  # 90.0
        assert sorted_companies[1].name == "Company C"  # 75.0
        assert sorted_companies[2].name == "Company A"  # 60.0

    def test_sorting_with_none_scores(self):
        """Test sorting handles companies with None scores."""
        companies = [
            CompanyInfo(name="Company A", website="a.com", match_score=MatchScore(overall_score=75.0)),
            CompanyInfo(name="Company B", website="b.com", match_score=None),
            CompanyInfo(name="Company C", website="c.com", match_score=MatchScore(overall_score=85.0)),
        ]

        # Sort by score (descending)
        sorted_companies = sorted(
            companies,
            key=lambda c: c.match_score.overall_score if c.match_score else 0.0,
            reverse=True,
        )

        # Companies with scores should come first
        assert sorted_companies[0].name == "Company C"  # 85.0
        assert sorted_companies[1].name == "Company A"  # 75.0
        assert sorted_companies[2].name == "Company B"  # None (0.0)


class TestAvgScoreCalculation:
    """Test average score calculation."""

    def test_avg_score_calculation(self):
        """Test that average score is calculated correctly."""
        # Create companies with known scores
        companies = [
            CompanyInfo(
                name="Company A",
                website="a.com",
                match_score=MatchScore(overall_score=80.0),
            ),
            CompanyInfo(
                name="Company B",
                website="b.com",
                match_score=MatchScore(overall_score=70.0),
            ),
            CompanyInfo(
                name="Company C",
                website="c.com",
                match_score=MatchScore(overall_score=90.0),
            ),
        ]

        # Calculate average
        total_score = sum(c.match_score.overall_score for c in companies if c.match_score)
        avg_score = total_score / len(companies)

        # Verify
        assert avg_score == 80.0  # (80 + 70 + 90) / 3

    def test_avg_score_with_empty_list(self):
        """Test average score calculation with empty company list."""
        companies = []

        # Calculate average
        total_score = sum(c.match_score.overall_score for c in companies if c.match_score)
        avg_score = total_score / len(companies) if companies else 0.0

        # Verify
        assert avg_score == 0.0

    def test_avg_score_with_mixed_scores(self):
        """Test average score calculation with some None scores."""
        companies = [
            CompanyInfo(
                name="Company A",
                website="a.com",
                match_score=MatchScore(overall_score=80.0),
            ),
            CompanyInfo(
                name="Company B",
                website="b.com",
                match_score=None,
            ),
            CompanyInfo(
                name="Company C",
                website="c.com",
                match_score=MatchScore(overall_score=90.0),
            ),
        ]

        # Calculate average (only counting companies with scores)
        total_score = sum(c.match_score.overall_score for c in companies if c.match_score)
        avg_score = total_score / len(companies)

        # Verify - divides by total companies, not just scored ones
        # In the actual implementation, we divide by len(companies), not count of scored
        assert avg_score == (80.0 + 90.0) / 3  # 56.67
