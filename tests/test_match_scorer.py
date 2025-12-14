"""Tests for match scoring algorithm.

This module tests the MatchScore data model and MatchScorer scoring algorithm,
including component scores, overall scoring, and edge cases.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.models.match_score import MatchScore
from src.models.discovery_results import CompanyInfo
from src.models.business_context import BusinessContext
from src.scoring.match_scorer import MatchScorer
from src.agent.discovery_agent import DiscoveryAgent


class TestMatchScoreModel:
    """Tests for MatchScore data model."""

    def test_match_score_creation(self):
        """Test creating a MatchScore instance."""
        score = MatchScore(
            overall_score=85.0,
            relevance_score=90.0,
            geographic_fit=80.0,
            size_appropriateness=85.0,
            strategic_alignment=85.0,
            confidence="High"
        )

        assert score.overall_score == 85.0
        assert score.relevance_score == 90.0
        assert score.geographic_fit == 80.0
        assert score.size_appropriateness == 85.0
        assert score.strategic_alignment == 85.0
        assert score.confidence == "High"

    def test_match_score_range_validation(self):
        """Test that scores are clamped to 0-100 range."""
        # Test upper bound
        score = MatchScore(overall_score=150.0, relevance_score=120.0)
        assert score.overall_score == 100.0
        assert score.relevance_score == 100.0

        # Test lower bound
        score = MatchScore(overall_score=-10.0, geographic_fit=-5.0)
        assert score.overall_score == 0.0
        assert score.geographic_fit == 0.0

    def test_match_score_to_dict(self):
        """Test serialization to dictionary."""
        score = MatchScore(
            overall_score=85.0,
            relevance_score=90.0,
            confidence="High"
        )

        data = score.to_dict()

        assert data["overall_score"] == 85.0
        assert data["relevance_score"] == 90.0
        assert data["confidence"] == "High"
        assert "score_breakdown" in data

    def test_match_score_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "overall_score": 75.0,
            "relevance_score": 80.0,
            "geographic_fit": 70.0,
            "size_appropriateness": 75.0,
            "strategic_alignment": 75.0,
            "confidence": "Medium"
        }

        score = MatchScore.from_dict(data)

        assert score.overall_score == 75.0
        assert score.relevance_score == 80.0
        assert score.confidence == "Medium"

    def test_match_score_default_values(self):
        """Test default values when creating empty MatchScore."""
        score = MatchScore()

        assert score.overall_score == 0.0
        assert score.relevance_score == 0.0
        assert score.geographic_fit == 0.0
        assert score.size_appropriateness == 0.0
        assert score.strategic_alignment == 0.0
        assert score.confidence == "Low"

    def test_match_score_breakdown_populated(self):
        """Test that score_breakdown is automatically populated."""
        score = MatchScore(
            relevance_score=90.0,
            geographic_fit=80.0,
            size_appropriateness=85.0,
            strategic_alignment=85.0
        )

        assert "relevance" in score.score_breakdown
        assert "geographic" in score.score_breakdown
        assert "size" in score.score_breakdown
        assert "strategic" in score.score_breakdown
        assert score.score_breakdown["relevance"] == 90.0


class TestGeographicFitCalculation:
    """Tests for geographic fit scoring."""

    def test_geographic_exact_match(self):
        """Test exact location match returns 100."""
        # Create mock agent
        mock_agent = Mock(spec=DiscoveryAgent)
        scorer = MatchScorer(mock_agent)

        # Test exact match
        company_locations = ["North America", "Europe"]
        context_geography = ["North America", "Asia"]

        score = scorer._calculate_geographic_fit(company_locations, context_geography)

        assert score == 100.0

    def test_geographic_partial_match(self):
        """Test partial location match returns intermediate score."""
        mock_agent = Mock(spec=DiscoveryAgent)
        scorer = MatchScorer(mock_agent)

        # Test partial/substring match with similar names
        company_locations = ["San Francisco"]
        context_geography = ["San Francisco Bay Area"]

        score = scorer._calculate_geographic_fit(company_locations, context_geography)

        # Should be high but not perfect (substring match)
        assert 70.0 <= score <= 99.0

    def test_geographic_no_match(self):
        """Test no location match returns lower score."""
        mock_agent = Mock(spec=DiscoveryAgent)
        scorer = MatchScorer(mock_agent)

        # Test no match
        company_locations = ["Asia"]
        context_geography = ["Europe"]

        score = scorer._calculate_geographic_fit(company_locations, context_geography)

        # Should be lower score
        assert 0.0 <= score < 70.0

    def test_geographic_missing_data(self):
        """Test missing location data returns neutral score."""
        mock_agent = Mock(spec=DiscoveryAgent)
        scorer = MatchScorer(mock_agent)

        # Test with empty locations
        score = scorer._calculate_geographic_fit([], ["North America"])
        assert score == 50.0

        # Test with None
        score = scorer._calculate_geographic_fit(["US"], [])
        assert score == 50.0


class TestSizeAppropriatenessCalculation:
    """Tests for size appropriateness scoring."""

    def test_size_perfect_match(self):
        """Test perfect size match returns 100."""
        mock_agent = Mock(spec=DiscoveryAgent)
        scorer = MatchScorer(mock_agent)

        # Create context targeting SMBs
        context = BusinessContext(
            target_market="B2B - Small businesses and startups"
        )

        # Test small company for SMB target
        score = scorer._calculate_size_fit("Small", context)
        assert score == 100.0

    def test_size_acceptable_match(self):
        """Test acceptable size match returns good score."""
        mock_agent = Mock(spec=DiscoveryAgent)
        scorer = MatchScorer(mock_agent)

        # Create context targeting mid-market
        context = BusinessContext(
            target_market="Mid-market companies"
        )

        # Test small company for mid-market (one size off)
        score = scorer._calculate_size_fit("Small", context)
        assert score == 70.0

    def test_size_poor_match(self):
        """Test poor size match returns low score."""
        mock_agent = Mock(spec=DiscoveryAgent)
        scorer = MatchScorer(mock_agent)

        # Create context targeting enterprise
        context = BusinessContext(
            target_market="Enterprise and Fortune 500 companies"
        )

        # Test small company for enterprise (two sizes off)
        score = scorer._calculate_size_fit("Small", context)
        assert score == 30.0

    def test_size_unknown(self):
        """Test unknown size returns neutral score."""
        mock_agent = Mock(spec=DiscoveryAgent)
        scorer = MatchScorer(mock_agent)

        context = BusinessContext(target_market="SMB")

        score = scorer._calculate_size_fit("Unknown", context)
        assert score == 50.0


class TestScoreMatchWorkflow:
    """Tests for the complete score_match workflow."""

    def test_score_match_returns_valid_match_score(self):
        """Test that score_match returns a valid MatchScore."""
        # Create mock agent with generate_content method
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_agent._generate_content = Mock(return_value="85")

        scorer = MatchScorer(mock_agent)

        # Create test data
        company = CompanyInfo(
            name="Test Company",
            website="https://test.com",
            locations=["North America"],
            size_estimate="Medium",
            description="A test company in the SaaS industry"
        )

        context = BusinessContext(
            industry="SaaS",
            target_market="Mid-market B2B companies",
            geography=["North America"],
            products_services=["Cloud software"]
        )

        # Score the match
        score = scorer.score_match(company, context, "customer")

        # Verify result is a MatchScore
        assert isinstance(score, MatchScore)
        assert 0.0 <= score.overall_score <= 100.0
        assert score.confidence in ["High", "Medium", "Low"]

    def test_score_match_weighted_average(self):
        """Test that overall score is weighted average of components."""
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_agent._generate_content = Mock(return_value="80")

        scorer = MatchScorer(mock_agent)

        company = CompanyInfo(
            name="Test Company",
            website="https://test.com",
            locations=["North America"],
            size_estimate="Medium",
            description="A SaaS company"
        )

        context = BusinessContext(
            industry="SaaS",
            target_market="Mid-market",
            geography=["North America"]
        )

        score = scorer.score_match(company, context, "customer")

        # Calculate expected weighted average
        expected_score = (
            scorer.weights["relevance"] * score.relevance_score +
            scorer.weights["geographic"] * score.geographic_fit +
            scorer.weights["size"] * score.size_appropriateness +
            scorer.weights["strategic"] * score.strategic_alignment
        )

        # Should be close to expected (allowing for rounding)
        assert abs(score.overall_score - expected_score) < 0.1

    def test_score_match_has_score_breakdown(self):
        """Test that score_match includes component breakdown."""
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_agent._generate_content = Mock(return_value="75")

        scorer = MatchScorer(mock_agent)

        company = CompanyInfo(
            name="Test Company",
            website="https://test.com",
            description="Test description"
        )

        context = BusinessContext(industry="Technology")

        score = scorer.score_match(company, context, "partner")

        # Verify breakdown exists and has all components
        assert "relevance" in score.score_breakdown
        assert "geographic" in score.score_breakdown
        assert "size" in score.score_breakdown
        assert "strategic" in score.score_breakdown


class TestConfidenceLevels:
    """Tests for confidence level determination."""

    def test_high_confidence_complete_data(self):
        """Test that complete data produces high confidence."""
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_agent._generate_content = Mock(return_value="80")

        scorer = MatchScorer(mock_agent)

        # Create complete company data
        company = CompanyInfo(
            name="Complete Company",
            website="https://complete.com",
            locations=["North America", "Europe"],
            size_estimate="Large",
            description="A comprehensive description of the company"
        )

        # Create complete context
        context = BusinessContext(
            company_name="Our Company",
            industry="SaaS - Marketing",
            products_services=["Email platform", "Analytics"],
            target_market="B2B mid-market",
            geography=["North America"],
            key_strengths=["AI-powered"]
        )

        score = scorer.score_match(company, context, "customer")

        assert score.confidence == "High"

    def test_medium_confidence_partial_data(self):
        """Test that partial data produces medium confidence."""
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_agent._generate_content = Mock(return_value="70")

        scorer = MatchScorer(mock_agent)

        # Create partial company data (missing some fields)
        company = CompanyInfo(
            name="Partial Company",
            website="https://partial.com",
            description="Brief description"
            # Missing: locations, size_estimate
        )

        # Partial context
        context = BusinessContext(
            industry="Technology",
            target_market="B2B"
            # Missing: geography, products_services, etc.
        )

        score = scorer.score_match(company, context, "customer")

        assert score.confidence == "Medium"

    def test_low_confidence_minimal_data(self):
        """Test that minimal data produces low confidence."""
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_agent._generate_content = Mock(return_value="60")

        scorer = MatchScorer(mock_agent)

        # Create minimal company data
        company = CompanyInfo(
            name="Minimal Company",
            website="https://minimal.com"
            # Missing: description, locations, size
        )

        # Minimal context
        context = BusinessContext(
            company_name="Our Company"
            # Missing: most fields
        )

        score = scorer.score_match(company, context, "partner")

        assert score.confidence == "Low"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_missing_company_data(self):
        """Test scoring with missing company data."""
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_agent._generate_content = Mock(return_value="50")

        scorer = MatchScorer(mock_agent)

        # Company with minimal data
        company = CompanyInfo(
            name="Minimal Co",
            website="https://minimal.co"
        )

        context = BusinessContext(
            industry="Technology",
            target_market="B2B"
        )

        # Should not raise an error
        score = scorer.score_match(company, context, "customer")

        assert isinstance(score, MatchScore)
        assert 0.0 <= score.overall_score <= 100.0

    def test_no_geographic_overlap(self):
        """Test scoring when there's no geographic overlap."""
        mock_agent = Mock(spec=DiscoveryAgent)
        mock_agent._generate_content = Mock(return_value="70")

        scorer = MatchScorer(mock_agent)

        company = CompanyInfo(
            name="Asia Company",
            website="https://asia.com",
            locations=["Asia", "Australia"],
            description="An Asian company"
        )

        context = BusinessContext(
            industry="SaaS",
            geography=["North America", "Europe"]
        )

        score = scorer.score_match(company, context, "customer")

        # Geographic fit should be low
        assert score.geographic_fit < 70.0
        # But overall score should still be calculated
        assert 0.0 <= score.overall_score <= 100.0

    def test_ai_scoring_failure_fallback(self):
        """Test that fallback scoring works when AI scoring fails."""
        mock_agent = Mock(spec=DiscoveryAgent)
        # Simulate AI failure
        mock_agent._generate_content = Mock(side_effect=Exception("API error"))

        scorer = MatchScorer(mock_agent)

        company = CompanyInfo(
            name="Test Company",
            website="https://test.com",
            description="SaaS marketing platform"
        )

        context = BusinessContext(
            industry="SaaS - Marketing",
            products_services=["Marketing automation"]
        )

        # Should use fallback scoring and not raise exception
        score = scorer.score_match(company, context, "customer")

        assert isinstance(score, MatchScore)
        # Fallback should still produce a valid score
        assert 0.0 <= score.relevance_score <= 100.0

    def test_empty_context_geography(self):
        """Test geographic scoring with empty context geography."""
        mock_agent = Mock(spec=DiscoveryAgent)
        scorer = MatchScorer(mock_agent)

        score = scorer._calculate_geographic_fit(
            ["North America"],
            []  # Empty context geography
        )

        # Should return neutral score
        assert score == 50.0
