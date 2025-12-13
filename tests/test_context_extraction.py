"""Tests for context extraction components.

This module tests the BusinessContext data model and ContextExtractor class
functionality, including serialization, deserialization, and context extraction
with mocked agent responses.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.models.business_context import BusinessContext
from src.agent.context_extractor import ContextExtractor
from src.agent.discovery_agent import DiscoveryAgent


class TestBusinessContextSerialization:
    """Test BusinessContext data model serialization and deserialization."""

    def test_to_dict(self):
        """Test converting BusinessContext to dictionary."""
        context = BusinessContext(
            company_name="Acme Corp",
            industry="SaaS - Marketing Automation",
            products_services=["Email platform", "Analytics"],
            target_market="B2B - SMB marketing agencies",
            geography=["North America", "Europe"],
            key_strengths=["AI-powered optimization", "Easy integration"],
            additional_notes="Series A funded, 50-100 employees",
        )

        data = context.to_dict()

        assert isinstance(data, dict)
        assert data["company_name"] == "Acme Corp"
        assert data["industry"] == "SaaS - Marketing Automation"
        assert data["products_services"] == ["Email platform", "Analytics"]
        assert data["target_market"] == "B2B - SMB marketing agencies"
        assert data["geography"] == ["North America", "Europe"]
        assert data["key_strengths"] == [
            "AI-powered optimization",
            "Easy integration",
        ]
        assert data["additional_notes"] == "Series A funded, 50-100 employees"

    def test_from_dict(self):
        """Test creating BusinessContext from dictionary."""
        data = {
            "company_name": "Test Company",
            "industry": "Healthcare",
            "products_services": ["Product A", "Product B"],
            "target_market": "B2C",
            "geography": ["Asia", "Europe"],
            "key_strengths": ["Innovation"],
            "additional_notes": "Fast growing",
        }

        context = BusinessContext.from_dict(data)

        assert context.company_name == "Test Company"
        assert context.industry == "Healthcare"
        assert context.products_services == ["Product A", "Product B"]
        assert context.target_market == "B2C"
        assert context.geography == ["Asia", "Europe"]
        assert context.key_strengths == ["Innovation"]
        assert context.additional_notes == "Fast growing"

    def test_from_dict_with_missing_fields(self):
        """Test from_dict handles missing fields gracefully."""
        data = {
            "company_name": "Partial Corp",
            "industry": "Tech",
        }

        context = BusinessContext.from_dict(data)

        assert context.company_name == "Partial Corp"
        assert context.industry == "Tech"
        # Missing fields should have defaults
        assert context.products_services == []
        assert context.target_market == ""
        assert context.geography == []
        assert context.key_strengths == []
        assert context.additional_notes == ""

    def test_from_dict_with_extra_fields(self):
        """Test from_dict ignores extra fields not in the dataclass."""
        data = {
            "company_name": "Extra Corp",
            "industry": "Finance",
            "unknown_field": "should be ignored",
            "another_extra": 123,
        }

        context = BusinessContext.from_dict(data)

        assert context.company_name == "Extra Corp"
        assert context.industry == "Finance"
        # Extra fields should be ignored
        assert not hasattr(context, "unknown_field")
        assert not hasattr(context, "another_extra")

    def test_to_prompt_string(self):
        """Test converting BusinessContext to readable prompt string."""
        context = BusinessContext(
            company_name="Prompt Corp",
            industry="Education",
            products_services=["LMS", "Analytics"],
            target_market="Higher Education",
            geography=["USA", "Canada"],
            key_strengths=["User-friendly"],
            additional_notes="Established 2020",
        )

        prompt_str = context.to_prompt_string()

        assert isinstance(prompt_str, str)
        assert "Company: Prompt Corp" in prompt_str
        assert "Industry: Education" in prompt_str
        assert "Products/Services: LMS, Analytics" in prompt_str
        assert "Target Market: Higher Education" in prompt_str
        assert "Geography: USA, Canada" in prompt_str
        assert "Key Strengths: User-friendly" in prompt_str
        assert "Additional Notes: Established 2020" in prompt_str

    def test_to_prompt_string_empty_context(self):
        """Test to_prompt_string with empty context."""
        context = BusinessContext()

        prompt_str = context.to_prompt_string()

        assert prompt_str == "No business context available"

    def test_to_prompt_string_partial_context(self):
        """Test to_prompt_string with partial context."""
        context = BusinessContext(
            company_name="Partial Corp",
            industry="Tech",
        )

        prompt_str = context.to_prompt_string()

        assert "Company: Partial Corp" in prompt_str
        assert "Industry: Tech" in prompt_str
        # Should not include empty fields
        assert "Products/Services:" not in prompt_str
        assert "Target Market:" not in prompt_str

    def test_roundtrip_serialization(self):
        """Test roundtrip: BusinessContext -> dict -> BusinessContext."""
        original = BusinessContext(
            company_name="Roundtrip Corp",
            industry="Logistics",
            products_services=["Shipping", "Tracking"],
            target_market="E-commerce",
            geography=["Global"],
            key_strengths=["Speed", "Reliability"],
            additional_notes="Founded 2015",
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = BusinessContext.from_dict(data)

        # Should be identical
        assert restored.company_name == original.company_name
        assert restored.industry == original.industry
        assert restored.products_services == original.products_services
        assert restored.target_market == original.target_market
        assert restored.geography == original.geography
        assert restored.key_strengths == original.key_strengths
        assert restored.additional_notes == original.additional_notes


class TestContextExtractorInitialization:
    """Test ContextExtractor initialization."""

    def test_initialization_with_valid_agent(self):
        """Test ContextExtractor initializes with valid agent."""
        mock_agent = Mock(spec=DiscoveryAgent)

        extractor = ContextExtractor(mock_agent)

        assert extractor.agent is mock_agent

    def test_initialization_with_none_agent(self):
        """Test ContextExtractor raises ValueError with None agent."""
        with pytest.raises(ValueError, match="agent cannot be None"):
            ContextExtractor(None)


class TestContextExtractorWithMocks:
    """Test ContextExtractor methods with mocked agent responses."""

    def test_extract_from_text_mock(self):
        """Test extract_from_text with mocked agent response."""
        # Create mock agent
        mock_agent = Mock(spec=DiscoveryAgent)

        # Mock agent.extract_context to return structured data
        mock_response = {
            "company_name": "Mock Corp",
            "industry": "SaaS",
            "products_services": ["Product 1", "Product 2"],
            "target_market": "B2B - Enterprise",
            "geography": ["North America"],
            "key_strengths": ["Innovation", "Support"],
            "additional_notes": "Well-funded",
        }
        mock_agent.extract_context.return_value = mock_response

        # Create extractor
        extractor = ContextExtractor(mock_agent)

        # Extract from text
        text = "Sample business document text..."
        context = extractor.extract_from_text(text)

        # Verify agent was called
        mock_agent.extract_context.assert_called_once_with(text)

        # Verify context fields
        assert isinstance(context, BusinessContext)
        assert context.company_name == "Mock Corp"
        assert context.industry == "SaaS"
        assert context.products_services == ["Product 1", "Product 2"]
        assert context.target_market == "B2B - Enterprise"
        assert context.geography == ["North America"]
        assert context.key_strengths == ["Innovation", "Support"]
        assert "Well-funded" in context.additional_notes

    def test_extract_from_text_with_empty_text(self):
        """Test extract_from_text raises ValueError with empty text."""
        mock_agent = Mock(spec=DiscoveryAgent)
        extractor = ContextExtractor(mock_agent)

        with pytest.raises(ValueError, match="text cannot be empty"):
            extractor.extract_from_text("")

        with pytest.raises(ValueError, match="text cannot be empty"):
            extractor.extract_from_text("   ")

    def test_extract_from_text_with_raw_response(self):
        """Test extract_from_text handles raw_response format."""
        mock_agent = Mock(spec=DiscoveryAgent)

        # Mock agent returns raw_response (unparsed JSON)
        raw_json = """
        {
            "company_name": "Raw Corp",
            "industry": "Manufacturing"
        }
        """
        mock_response = {"raw_response": raw_json}
        mock_agent.extract_context.return_value = mock_response

        extractor = ContextExtractor(mock_agent)
        context = extractor.extract_from_text("Sample text")

        # Should parse the JSON from raw_response
        assert context.company_name == "Raw Corp"
        assert context.industry == "Manufacturing"

    def test_extract_from_text_with_partial_fields(self):
        """Test extract_from_text handles partial response gracefully."""
        mock_agent = Mock(spec=DiscoveryAgent)

        # Mock agent returns only some fields
        mock_response = {
            "company_name": "Partial Corp",
            "industry": "Retail",
        }
        mock_agent.extract_context.return_value = mock_response

        extractor = ContextExtractor(mock_agent)
        context = extractor.extract_from_text("Sample text")

        assert context.company_name == "Partial Corp"
        assert context.industry == "Retail"
        # Missing fields should have defaults
        assert context.products_services == []
        assert context.target_market == ""

    def test_extract_from_files_mock(self):
        """Test extract_from_files with mocked document parsing and agent."""
        mock_agent = Mock(spec=DiscoveryAgent)

        # Mock agent response
        mock_response = {
            "company_name": "Multi-Doc Corp",
            "industry": "Consulting",
        }
        mock_agent.extract_context.return_value = mock_response

        # Mock parse_document function
        with patch("src.agent.context_extractor.parse_document") as mock_parse:
            mock_parse.side_effect = [
                "Document 1 content...",
                "Document 2 content...",
            ]

            extractor = ContextExtractor(mock_agent)
            context = extractor.extract_from_files(["doc1.pdf", "doc2.docx"])

            # Verify parsing was called for each file
            assert mock_parse.call_count == 2
            mock_parse.assert_any_call("doc1.pdf")
            mock_parse.assert_any_call("doc2.docx")

            # Verify agent was called with combined text
            mock_agent.extract_context.assert_called_once()
            call_args = mock_agent.extract_context.call_args[0][0]
            assert "Document 1 content..." in call_args
            assert "Document 2 content..." in call_args

            # Verify context
            assert context.company_name == "Multi-Doc Corp"
            assert context.industry == "Consulting"

    def test_extract_from_files_with_empty_list(self):
        """Test extract_from_files raises ValueError with empty file list."""
        mock_agent = Mock(spec=DiscoveryAgent)
        extractor = ContextExtractor(mock_agent)

        with pytest.raises(ValueError, match="file_paths cannot be empty"):
            extractor.extract_from_files([])

    def test_extract_from_files_skips_empty_documents(self):
        """Test extract_from_files skips empty documents gracefully."""
        mock_agent = Mock(spec=DiscoveryAgent)

        mock_response = {"company_name": "Test Corp"}
        mock_agent.extract_context.return_value = mock_response

        # Mock parse_document to return empty for first file, content for second
        with patch("src.agent.context_extractor.parse_document") as mock_parse:
            mock_parse.side_effect = ["", "Valid document content"]

            extractor = ContextExtractor(mock_agent)
            context = extractor.extract_from_files(["empty.pdf", "valid.docx"])

            # Should skip empty document and process valid one
            assert mock_parse.call_count == 2

            # Agent should be called with only valid document content
            call_args = mock_agent.extract_context.call_args[0][0]
            assert "Valid document content" in call_args
            assert context.company_name == "Test Corp"

    def test_extract_from_files_handles_parse_errors(self):
        """Test extract_from_files continues when individual file parsing fails."""
        mock_agent = Mock(spec=DiscoveryAgent)

        mock_response = {"company_name": "Resilient Corp"}
        mock_agent.extract_context.return_value = mock_response

        # Mock parse_document: first fails, second succeeds
        with patch("src.agent.context_extractor.parse_document") as mock_parse:
            mock_parse.side_effect = [
                FileNotFoundError("File not found"),
                "Valid content",
            ]

            extractor = ContextExtractor(mock_agent)
            context = extractor.extract_from_files(["missing.pdf", "valid.docx"])

            # Should continue after error
            assert mock_parse.call_count == 2

            # Should process the valid file
            call_args = mock_agent.extract_context.call_args[0][0]
            assert "Valid content" in call_args
            assert context.company_name == "Resilient Corp"

    def test_parse_agent_response_with_alternative_field_names(self):
        """Test _parse_agent_response handles alternative field names."""
        mock_agent = Mock(spec=DiscoveryAgent)
        extractor = ContextExtractor(mock_agent)

        # Response with alternative field names
        response = {
            "company": "Alt Corp",  # Alternative to company_name
            "sector": "Technology",  # Alternative to industry
            "products": ["P1", "P2"],  # Alternative to products_services
        }

        context = extractor._parse_agent_response(response)

        assert context.company_name == "Alt Corp"
        assert context.industry == "Technology"
        assert context.products_services == ["P1", "P2"]

    def test_parse_agent_response_converts_string_to_list(self):
        """Test _parse_agent_response converts comma-separated strings to lists."""
        mock_agent = Mock(spec=DiscoveryAgent)
        extractor = ContextExtractor(mock_agent)

        # Response with comma-separated strings for list fields
        response = {
            "products_services": "Product A, Product B, Product C",
            "geography": "USA, Canada, Mexico",
        }

        context = extractor._parse_agent_response(response)

        assert context.products_services == ["Product A", "Product B", "Product C"]
        assert context.geography == ["USA", "Canada", "Mexico"]

    def test_parse_agent_response_adds_extra_fields_to_notes(self):
        """Test _parse_agent_response adds company_size and business_model to notes."""
        mock_agent = Mock(spec=DiscoveryAgent)
        extractor = ContextExtractor(mock_agent)

        # Response with extra fields
        response = {
            "company_name": "Extra Corp",
            "company_size": "100-200 employees",
            "business_model": "Subscription",
            "technology_stack": ["Python", "React"],
        }

        context = extractor._parse_agent_response(response)

        assert context.company_name == "Extra Corp"
        # Extra fields should be in additional_notes
        assert "Company Size: 100-200 employees" in context.additional_notes
        assert "Business Model: Subscription" in context.additional_notes
        assert "Technology Stack: Python, React" in context.additional_notes
