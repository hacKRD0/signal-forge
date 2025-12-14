"""UI components for the Streamlit application.

This module provides reusable UI components including the header, file uploader,
context summary display, and discovery input.
"""

import streamlit as st
from typing import List, Tuple, Dict, Any
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.models.business_context import BusinessContext


def render_header():
    """Render the application header with title and description.

    Displays the main title and a brief description of what the application does.
    This should be called once at the top of the main app.
    """
    st.title("Customer & Partner Discovery")
    st.markdown(
        """
        Upload your business documents to discover potential customers and partners
        using AI-powered analysis. This tool analyzes your business context and
        searches for relevant matches using publicly available data.
        """
    )


def render_file_uploader() -> List[UploadedFile]:
    """Render the multi-file uploader widget.

    Displays a file uploader that accepts DOCX, PDF, CSV, and PPTX files.
    Users can upload multiple files at once to build comprehensive business context.

    Returns:
        List of UploadedFile objects, or empty list if no files uploaded.

    Example:
        >>> uploaded_files = render_file_uploader()
        >>> if uploaded_files:
        ...     st.write(f"Uploaded {len(uploaded_files)} files")
    """
    uploaded_files = st.file_uploader(
        "Upload Business Documents",
        type=["docx", "pdf", "csv", "pptx"],
        accept_multiple_files=True,
        help="Upload documents that describe your business (company overview, product catalogs, etc.)"
    )

    # Return empty list instead of None if no files
    return uploaded_files if uploaded_files else []


def render_context_summary(context: BusinessContext):
    """Display the extracted business context in an expandable section.

    Shows the business context information extracted from uploaded documents
    in a nicely formatted, expandable section. This allows users to review
    and verify the extracted information.

    Args:
        context: BusinessContext object containing extracted information.

    Example:
        >>> context = BusinessContext(company_name="Acme Corp", industry="SaaS")
        >>> render_context_summary(context)
    """
    with st.expander("Business Context Summary", expanded=True):
        st.markdown("### Extracted Business Information")

        if context.company_name:
            st.markdown(f"**Company Name:** {context.company_name}")

        if context.industry:
            st.markdown(f"**Industry:** {context.industry}")

        if context.products_services:
            st.markdown("**Products/Services:**")
            for product in context.products_services:
                st.markdown(f"- {product}")

        if context.target_market:
            st.markdown(f"**Target Market:** {context.target_market}")

        if context.geography:
            st.markdown("**Geography:**")
            for location in context.geography:
                st.markdown(f"- {location}")

        if context.key_strengths:
            st.markdown("**Key Strengths:**")
            for strength in context.key_strengths:
                st.markdown(f"- {strength}")

        if context.additional_notes:
            st.markdown(f"**Additional Notes:** {context.additional_notes}")

        # If no information is available
        if not any([
            context.company_name,
            context.industry,
            context.products_services,
            context.target_market,
            context.geography,
            context.key_strengths,
            context.additional_notes
        ]):
            st.info("No business context information extracted yet.")


def render_discovery_input() -> Tuple[str, Dict[str, Any]]:
    """Render the discovery input form with entity type and optional filters.

    Displays a form for selecting the type of entity to discover (Customer or Partner)
    and optional filters for geography and industry. Returns the selected entity type
    and a dictionary of filters.

    Returns:
        Tuple containing:
        - entity_type: str - Either "Customer" or "Partner"
        - filters: dict - Dictionary with optional keys:
            - "geography": list of selected regions
            - "industry": list of selected industries
            - Empty dict if no filters selected

    Example:
        >>> entity_type, filters = render_discovery_input()
        >>> if entity_type:
        ...     st.write(f"Discovering {entity_type}s")
        ...     if filters:
        ...         st.write(f"Filters: {filters}")
    """
    # Entity type selector
    entity_type = st.radio(
        "Discovery Type",
        options=["Customer", "Partner"],
        help="Select whether you want to discover potential customers or partners"
    )

    # Natural language request (optional, for future use)
    st.text_input(
        "Natural Language Request (Optional)",
        help="Describe any specific requirements or preferences for discovery",
        value=""
    )

    # Optional filters
    filters: Dict[str, Any] = {}

    with st.expander("Optional Filters"):
        # Geography filter
        geography_options = [
            "North America",
            "Europe",
            "Asia",
            "Latin America",
            "Middle East & Africa",
            "Oceania"
        ]
        selected_geography = st.multiselect(
            "Geography",
            options=geography_options,
            help="Select geographic regions to focus discovery"
        )
        if selected_geography:
            filters["geography"] = selected_geography

        # Industry filter
        industry_options = [
            "Technology",
            "Healthcare",
            "Finance",
            "Manufacturing",
            "Retail",
            "Energy",
            "Telecommunications",
            "Transportation",
            "Education",
            "Real Estate",
            "Hospitality",
            "Media & Entertainment"
        ]
        selected_industry = st.multiselect(
            "Industry",
            options=industry_options,
            help="Select industries to focus discovery"
        )
        if selected_industry:
            filters["industry"] = selected_industry

    return entity_type, filters
