"""Results display components for showing discovered companies and details.

This module provides UI components for displaying discovery results in a comprehensive,
user-friendly format with tables, detail views, and export functionality.
"""

import streamlit as st
import pandas as pd
from typing import Optional, List
from src.models.discovery_results import CompanyInfo, DiscoveryResult


def render_results_table(results: DiscoveryResult, entity_type: str):
    """Display a table of discovered companies with summary metrics.

    Shows a pandas DataFrame table with columns: Rank, Company Name, Match Score,
    Size, Locations, Website. Includes color-coded score formatting and summary
    statistics.

    Args:
        results: DiscoveryResult object containing companies to display
        entity_type: Type of entity ("Customer" or "Partner") for the title

    Example:
        >>> result = DiscoveryResult(entity_type="Customer", companies=[...])
        >>> render_results_table(result, "Customer")
    """
    if not results or not results.companies:
        st.info(f"No {entity_type.lower()} results to display")
        return

    # Display title with result count
    st.subheader(f"Discovered {entity_type}s ({len(results.companies)} results)")

    # Display summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Results", len(results.companies))
    with col2:
        if results.avg_score > 0:
            st.metric("Average Match Score", f"{results.avg_score:.1f}")
        else:
            st.metric("Average Match Score", "N/A")
    with col3:
        if results.scored:
            st.metric("Results Scored", "Yes")
        else:
            st.metric("Results Scored", "No")

    # Prepare data for table
    table_data = []
    for rank, company in enumerate(results.companies, 1):
        score = company.match_score.overall_score if company.match_score else 0.0

        # Determine score category for color coding
        if score >= 80:
            score_category = "🟢 Strong"  # Green
        elif score >= 60:
            score_category = "🟡 Good"    # Yellow
        else:
            score_category = "⚪ Fair"    # Gray

        locations_str = ", ".join(company.locations) if company.locations else "N/A"

        table_data.append({
            "Rank": rank,
            "Company Name": company.name,
            "Match Score": f"{score:.1f}" if score > 0 else "N/A",
            "Score Category": score_category,
            "Size": company.size_estimate,
            "Locations": locations_str,
            "Website": company.website if company.website else "N/A"
        })

    # Create and display DataFrame
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Add sort/filter info
    with st.expander("Sort & Filter Options"):
        st.info(
            "Use the table above to sort by clicking column headers. "
            "For detailed information about each company, expand the company detail sections below."
        )


def render_company_detail(company: CompanyInfo, index: int = 1):
    """Display detailed information about a discovered company in an expander.

    Shows all company fields, match score breakdown, rationale with strengths
    and concerns, and clickable source links.

    Args:
        company: CompanyInfo object with company details
        index: Position index for the expander (for ordering)

    Example:
        >>> company = CompanyInfo(name="Acme Corp", website="https://acme.com", ...)
        >>> render_company_detail(company, 1)
    """
    # Use company name and score for expander title
    score = company.match_score.overall_score if company.match_score else 0.0
    score_str = f"{score:.1f}" if score > 0 else "N/A"

    expander_title = f"{index}. {company.name} - Score: {score_str}"

    with st.expander(expander_title, expanded=False):
        # Company Information Section
        st.markdown("### Company Information")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Company Name:** {company.name}")
            st.markdown(f"**Size:** {company.size_estimate}")
        with col2:
            # Make website clickable
            if company.website:
                st.markdown(f"**Website:** [Visit Website]({company.website})")
            else:
                st.markdown("**Website:** N/A")

        # Locations
        if company.locations:
            st.markdown("**Locations:**")
            location_str = ", ".join(company.locations)
            st.markdown(location_str)

        # Description
        if company.description:
            st.markdown("**Description:**")
            st.markdown(company.description)

        st.divider()

        # Match Score Breakdown Section
        if company.match_score:
            st.markdown("### Match Score Breakdown")

            score = company.match_score

            # Overall score with color coding
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Overall Score",
                    f"{score.overall_score:.1f}",
                    help="Weighted average of all components"
                )
            with col2:
                st.metric(
                    "Relevance",
                    f"{score.relevance_score:.1f}",
                    help="Business relevance alignment"
                )
            with col3:
                st.metric(
                    "Geographic Fit",
                    f"{score.geographic_fit:.1f}",
                    help="Location alignment"
                )
            with col4:
                st.metric(
                    "Size Fit",
                    f"{score.size_appropriateness:.1f}",
                    help="Company size alignment"
                )

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Strategic Alignment",
                    f"{score.strategic_alignment:.1f}",
                    help="Strategic fit and capabilities"
                )
            with col2:
                st.metric(
                    "Confidence",
                    score.confidence,
                    help="Confidence level in the score"
                )

            # Detailed score breakdown
            if score.score_breakdown:
                with st.expander("Detailed Score Breakdown"):
                    breakdown_df = pd.DataFrame(
                        list(score.score_breakdown.items()),
                        columns=["Component", "Score"]
                    )
                    st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

            st.divider()

        # Rationale Section
        if company.rationale:
            st.markdown("### Match Rationale")

            rationale = company.rationale

            # Recommendation level
            recommendation = rationale.recommendation
            if recommendation == "Strong Match":
                rec_icon = "🟢"
            elif recommendation == "Good Match":
                rec_icon = "🟡"
            else:
                rec_icon = "⚪"

            st.markdown(f"**Recommendation:** {rec_icon} {recommendation}")

            # Summary
            if rationale.summary:
                st.markdown(f"**Summary:** {rationale.summary}")

            # Key Strengths
            if rationale.key_strengths:
                st.markdown("**Key Strengths:**")
                for strength in rationale.key_strengths:
                    st.markdown(f"- {strength}")

            # Fit Explanation
            if rationale.fit_explanation:
                st.markdown("**Fit Explanation:**")
                st.markdown(rationale.fit_explanation)

            # Potential Concerns
            if rationale.potential_concerns:
                st.markdown("**Potential Concerns:**")
                for concern in rationale.potential_concerns:
                    st.markdown(f"- {concern}")

            st.divider()

        # Sources Section
        if company.sources:
            st.markdown("### Sources")
            st.markdown("**Information Sources:**")
            for i, source in enumerate(company.sources, 1):
                # Make sources clickable
                source_display = source if len(source) <= 80 else source[:77] + "..."
                st.markdown(f"{i}. [View Source]({source})")


def render_results_downloads(results: DiscoveryResult, entity_type: str):
    """Provide CSV and JSON download buttons for discovery results.

    Allows users to export the results table as CSV or the full results
    (with scores and rationales) as JSON.

    Args:
        results: DiscoveryResult object to export
        entity_type: Type of entity ("Customer" or "Partner") for filename

    Example:
        >>> result = DiscoveryResult(entity_type="Customer", companies=[...])
        >>> render_results_downloads(result, "Customer")
    """
    if not results or not results.companies:
        return

    st.markdown("### Download Results")

    col1, col2 = st.columns(2)

    # CSV Export - summary table only
    with col1:
        # Create CSV data from companies
        csv_data = []
        for rank, company in enumerate(results.companies, 1):
            score = company.match_score.overall_score if company.match_score else 0.0
            locations_str = ", ".join(company.locations) if company.locations else ""

            csv_data.append({
                "Rank": rank,
                "Company Name": company.name,
                "Website": company.website,
                "Match Score": f"{score:.1f}" if score > 0 else "",
                "Size": company.size_estimate,
                "Locations": locations_str,
                "Description": company.description
            })

        df_csv = pd.DataFrame(csv_data)
        csv_str = df_csv.to_csv(index=False)

        st.download_button(
            label="📥 Download as CSV",
            data=csv_str,
            file_name=f"{entity_type.lower()}_results.csv",
            mime="text/csv"
        )

    # JSON Export - full results with all details
    with col2:
        import json
        json_data = results.to_dict()
        json_str = json.dumps(json_data, indent=2, default=str)

        st.download_button(
            label="📥 Download as JSON",
            data=json_str,
            file_name=f"{entity_type.lower()}_results.json",
            mime="application/json"
        )
