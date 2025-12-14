"""Tests for rationale generation functionality.

This module tests the RationaleGenerator class and Rationale data model,
ensuring proper rationale generation, entity-type handling, and recommendation logic.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock

from src.models.rationale import Rationale
from src.models.discovery_results import CompanyInfo
from src.models.business_context import BusinessContext
from src.models.match_score import MatchScore
from src.scoring.rationale_generator import RationaleGenerator


class TestRationaleModel:
    """Tests for the Rationale data model."""

    def test_rationale_creation(self):
        """Test creating a Rationale instance."""
        rationale = Rationale(
            summary="Excellent customer fit",
            key_strengths=["High relevance", "Good location", "Right size"],
            fit_explanation="Strong match based on all dimensions",
            potential_concerns=["Limited international presence"],
            recommendation="Strong Match"
        )

        assert rationale.summary == "Excellent customer fit"
        assert len(rationale.key_strengths) == 3
        assert rationale.recommendation == "Strong Match"
        assert len(rationale.potential_concerns) == 1

    def test_rationale_serialization(self):
        """Test Rationale to_dict and from_dict."""
        original = Rationale(
            summary="Test summary",
            key_strengths=["Strength 1", "Strength 2"],
            fit_explanation="Test explanation",
            potential_concerns=["Concern 1"],
            recommendation="Good Match"
        )

        # Convert to dict
        data = original.to_dict()
        assert data["summary"] == "Test summary"
        assert len(data["key_strengths"]) == 2
        assert data["recommendation"] == "Good Match"

        # Convert back from dict
        restored = Rationale.from_dict(data)
        assert restored.summary == original.summary
        assert restored.key_strengths == original.key_strengths
        assert restored.recommendation == original.recommendation

    def test_rationale_default_values(self):
        """Test Rationale with default values."""
        rationale = Rationale()

        assert rationale.summary == ""
        assert rationale.key_strengths == []
        assert rationale.fit_explanation == ""
        assert rationale.potential_concerns == []
        assert rationale.recommendation == "Fair Match"

    def test_invalid_recommendation_defaults_to_fair(self):
        """Test that invalid recommendation defaults to Fair Match."""
        rationale = Rationale(recommendation="Invalid Level")
        assert rationale.recommendation == "Fair Match"


class TestRecommendationLevels:
    """Tests for recommendation level determination."""

    def test_strong_match_threshold(self):
        """Test Strong Match for score >= 80."""
        mock_agent = Mock()
        generator = RationaleGenerator(mock_agent)

        # Test at boundary
        assert generator._determine_recommendation(80.0) == "Strong Match"
        assert generator._determine_recommendation(85.0) == "Strong Match"
        assert generator._determine_recommendation(100.0) == "Strong Match"

    def test_good_match_threshold(self):
        """Test Good Match for score >= 60 and < 80."""
        mock_agent = Mock()
        generator = RationaleGenerator(mock_agent)

        # Test at boundaries
        assert generator._determine_recommendation(60.0) == "Good Match"
        assert generator._determine_recommendation(70.0) == "Good Match"
        assert generator._determine_recommendation(79.9) == "Good Match"

    def test_fair_match_threshold(self):
        """Test Fair Match for score < 60."""
        mock_agent = Mock()
        generator = RationaleGenerator(mock_agent)

        # Test below threshold
        assert generator._determine_recommendation(59.9) == "Fair Match"
        assert generator._determine_recommendation(50.0) == "Fair Match"
        assert generator._determine_recommendation(0.0) == "Fair Match"


class TestRationaleGeneration:
    """Tests for rationale generation logic."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock DiscoveryAgent."""
        agent = Mock()
        return agent

    @pytest.fixture
    def sample_company(self):
        """Create a sample CompanyInfo."""
        return CompanyInfo(
            name="Acme Marketing",
            website="https://acmemarketing.com",
            locations=["San Francisco, CA"],
            size_estimate="Small",
            description="Digital marketing agency for SMBs",
            sources=["https://example.com"]
        )

    @pytest.fixture
    def sample_context(self):
        """Create a sample BusinessContext."""
        return BusinessContext(
            company_name="MarketTech",
            industry="SaaS - Marketing Automation",
            products_services=["Email platform", "Analytics"],
            target_market="B2B - SMB marketing agencies",
            geography=["North America"],
            key_strengths=["AI-powered optimization"],
            additional_notes=""
        )

    @pytest.fixture
    def sample_score(self):
        """Create a sample MatchScore."""
        return MatchScore(
            overall_score=85.0,
            relevance_score=90.0,
            geographic_fit=80.0,
            size_appropriateness=85.0,
            strategic_alignment=85.0,
            score_breakdown={
                "relevance": 90.0,
                "geographic": 80.0,
                "size": 85.0,
                "strategic": 85.0
            },
            confidence="High"
        )

    def test_generate_rationale_customer(self, mock_agent, sample_company, sample_context, sample_score):
        """Test generating a customer rationale."""
        # Mock agent response
        mock_response = json.dumps({
            "summary": "Excellent customer fit for marketing automation needs",
            "key_strengths": [
                "High relevance score (90/100): Active need for automation",
                "Perfect geographic match (80/100): Located in North America",
                "Right size (85/100): SMB agency fits target market"
            ],
            "fit_explanation": "With an overall score of 85/100, this agency demonstrates strong customer potential.",
            "potential_concerns": []
        })
        mock_agent._generate_content = Mock(return_value=mock_response)

        generator = RationaleGenerator(mock_agent)
        rationale = generator.generate_rationale(
            sample_company,
            sample_context,
            sample_score,
            entity_type="customer"
        )

        # Verify rationale structure
        assert isinstance(rationale, Rationale)
        assert rationale.summary != ""
        assert len(rationale.key_strengths) > 0
        assert rationale.fit_explanation != ""
        assert rationale.recommendation == "Strong Match"  # Based on score 85

        # Verify agent was called
        mock_agent._generate_content.assert_called_once()
        call_args = mock_agent._generate_content.call_args
        assert "customer" in call_args[1]["operation"]

    def test_generate_rationale_partner(self, mock_agent, sample_company, sample_context, sample_score):
        """Test generating a partner rationale."""
        # Mock agent response with partner-specific language
        mock_response = json.dumps({
            "summary": "Strong partnership opportunity with complementary capabilities",
            "key_strengths": [
                "Strong strategic alignment (85/100): Complementary services",
                "Good geographic overlap (80/100): Shared market presence",
                "High relevance (90/100): Synergies in marketing automation"
            ],
            "fit_explanation": "With an overall score of 85/100, this firm represents excellent partnership potential through complementary offerings.",
            "potential_concerns": ["May need partnership agreement"]
        })
        mock_agent._generate_content = Mock(return_value=mock_response)

        generator = RationaleGenerator(mock_agent)
        rationale = generator.generate_rationale(
            sample_company,
            sample_context,
            sample_score,
            entity_type="partner"
        )

        # Verify rationale structure
        assert isinstance(rationale, Rationale)
        assert rationale.summary != ""
        assert len(rationale.key_strengths) > 0
        assert rationale.recommendation == "Strong Match"  # Based on score 85

        # Verify partner-specific operation was called
        mock_agent._generate_content.assert_called_once()
        call_args = mock_agent._generate_content.call_args
        assert "partner" in call_args[1]["operation"]

    def test_batch_generation(self, mock_agent, sample_company, sample_context, sample_score):
        """Test batch rationale generation."""
        # Create multiple companies with scores
        company2 = CompanyInfo(
            name="Beta Corp",
            website="https://betacorp.com",
            locations=["New York, NY"],
            size_estimate="Medium",
            description="Enterprise software company"
        )
        score2 = MatchScore(
            overall_score=70.0,
            relevance_score=75.0,
            geographic_fit=70.0,
            size_appropriateness=65.0,
            strategic_alignment=70.0,
            confidence="Medium"
        )

        companies_with_scores = [
            (sample_company, sample_score),
            (company2, score2)
        ]

        # Mock responses
        mock_response1 = json.dumps({
            "summary": "Good customer fit",
            "key_strengths": ["High relevance"],
            "fit_explanation": "Strong match overall",
            "potential_concerns": []
        })
        mock_response2 = json.dumps({
            "summary": "Solid customer prospect",
            "key_strengths": ["Good relevance"],
            "fit_explanation": "Decent match",
            "potential_concerns": ["Size could be better"]
        })
        mock_agent._generate_content = Mock(side_effect=[mock_response1, mock_response2])

        generator = RationaleGenerator(mock_agent)
        rationales = generator.batch_generate(
            companies_with_scores,
            sample_context,
            entity_type="customer"
        )

        # Verify batch processing
        assert len(rationales) == 2
        assert all(isinstance(r, Rationale) for r in rationales)
        assert rationales[0].recommendation == "Strong Match"  # Score 85
        assert rationales[1].recommendation == "Good Match"    # Score 70
        assert mock_agent._generate_content.call_count == 2

    def test_fallback_rationale_creation(self, mock_agent, sample_company, sample_score):
        """Test fallback rationale when AI generation fails."""
        generator = RationaleGenerator(mock_agent)

        # Test fallback for customer
        fallback = generator._create_fallback_rationale(
            sample_company,
            sample_score,
            "customer"
        )

        assert isinstance(fallback, Rationale)
        assert fallback.summary != ""
        assert len(fallback.key_strengths) > 0
        assert fallback.recommendation == "Strong Match"  # Based on score 85
        assert "customer" in fallback.summary.lower()

    def test_fallback_rationale_partner(self, mock_agent, sample_company, sample_score):
        """Test fallback rationale for partner type."""
        generator = RationaleGenerator(mock_agent)

        fallback = generator._create_fallback_rationale(
            sample_company,
            sample_score,
            "partner"
        )

        assert isinstance(fallback, Rationale)
        assert "partner" in fallback.summary.lower()

    def test_format_rationale_input(self, mock_agent, sample_company, sample_context, sample_score):
        """Test input formatting for rationale generation."""
        generator = RationaleGenerator(mock_agent)

        input_text = generator._format_rationale_input(
            sample_company,
            sample_context,
            sample_score,
            "customer"
        )

        # Verify key information is included
        assert sample_company.name in input_text
        assert sample_company.description in input_text
        assert str(sample_score.overall_score) in input_text
        assert "customer" in input_text.lower()

    def test_parse_rationale_response_valid_json(self, mock_agent):
        """Test parsing valid JSON response."""
        generator = RationaleGenerator(mock_agent)

        response_text = json.dumps({
            "summary": "Test summary",
            "key_strengths": ["Strength 1"],
            "fit_explanation": "Test explanation",
            "potential_concerns": []
        })

        rationale = generator._parse_rationale_response(response_text, 85.0)

        assert rationale.summary == "Test summary"
        assert rationale.recommendation == "Strong Match"

    def test_parse_rationale_response_with_extra_text(self, mock_agent):
        """Test parsing JSON embedded in other text."""
        generator = RationaleGenerator(mock_agent)

        response_text = f"""Here is the rationale:

{json.dumps({
    "summary": "Test summary",
    "key_strengths": ["Strength 1"],
    "fit_explanation": "Test explanation",
    "potential_concerns": []
})}

Hope this helps!"""

        rationale = generator._parse_rationale_response(response_text, 70.0)

        assert rationale.summary == "Test summary"
        assert rationale.recommendation == "Good Match"

    def test_parse_rationale_response_invalid(self, mock_agent):
        """Test parsing invalid response raises error."""
        generator = RationaleGenerator(mock_agent)

        with pytest.raises(ValueError):
            generator._parse_rationale_response("No JSON here!", 85.0)

    def test_generate_rationale_handles_errors(self, mock_agent, sample_company, sample_context, sample_score):
        """Test that errors during generation result in fallback rationale."""
        # Make agent raise an exception
        mock_agent._generate_content = Mock(side_effect=Exception("API Error"))

        generator = RationaleGenerator(mock_agent)
        rationale = generator.generate_rationale(
            sample_company,
            sample_context,
            sample_score,
            "customer"
        )

        # Should return fallback rationale instead of raising
        assert isinstance(rationale, Rationale)
        assert rationale.recommendation == "Strong Match"
