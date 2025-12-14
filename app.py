"""Main Streamlit application for Customer & Partner Discovery.

This is the entry point for the Streamlit web interface. It provides file upload,
business context extraction, discovery query input, and results display.

Run with: streamlit run app.py
"""

import streamlit as st
import os
import logging
from dotenv import load_dotenv

from src.ui.components import render_header, render_file_uploader, render_context_summary, render_discovery_input
from src.ui.document_processor import process_uploaded_files
from src.ui.discovery_runner import run_discovery
from src.ui.error_handler import handle_discovery_error, validate_discovery_preconditions, show_discovery_info
from src.agent.discovery_agent import DiscoveryAgent
from src.agent.context_extractor import ContextExtractor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Customer & Partner Discovery",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "uploaded_context" not in st.session_state:
    st.session_state.uploaded_context = None
if "discovery_results_customers" not in st.session_state:
    st.session_state.discovery_results_customers = None
if "discovery_results_partners" not in st.session_state:
    st.session_state.discovery_results_partners = None

# Initialize agent and extractor (cached to avoid recreation on every rerun)
@st.cache_resource
def get_context_extractor():
    """Get or create the ContextExtractor instance.

    This is cached to avoid recreating the agent on every Streamlit rerun.
    """
    agent = DiscoveryAgent()
    return ContextExtractor(agent)

# Render header
render_header()

# Sidebar
with st.sidebar:
    st.header("Configuration")
    st.markdown(
        """
        **About this tool:**

        This application helps discover potential customers and partners
        by analyzing your business documents and searching public data sources.

        **How to use:**
        1. Upload business documents
        2. Process documents to extract context
        3. Enter discovery queries
        4. View matched results
        """
    )

    st.markdown("---")

    # Clear All button
    if st.button("Clear All", type="secondary", use_container_width=True):
        st.session_state.uploaded_context = None
        st.session_state.discovery_results_customers = None
        st.session_state.discovery_results_partners = None
        st.success("All data cleared!")
        st.rerun()

# Main content area
st.header("1. Upload Business Documents")

# File upload section
uploaded_files = render_file_uploader()

if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) uploaded successfully")

    # Display uploaded file names
    with st.expander("View uploaded files"):
        for file in uploaded_files:
            st.write(f"- {file.name} ({file.type})")

    # Process documents button
    if st.button("Process Documents", type="primary"):
        try:
            with st.spinner("Processing documents..."):
                # Get the context extractor
                context_extractor = get_context_extractor()

                # Process the uploaded files
                context = process_uploaded_files(uploaded_files, context_extractor)

                # Store in session state
                st.session_state.uploaded_context = context

                # Show success message
                st.success(
                    f"Successfully extracted business context for "
                    f"{context.company_name or 'your business'}!"
                )

        except Exception as e:
            st.error(f"Error processing documents: {e}")
            import logging
            logging.error(f"Document processing error: {e}", exc_info=True)

# Display extracted context if available
if st.session_state.uploaded_context:
    st.markdown("---")
    render_context_summary(st.session_state.uploaded_context)

    # Discovery query section
    st.header("2. Discovery Query")

    # Validate preconditions
    if not validate_discovery_preconditions():
        st.stop()

    # Show info about discovery process
    show_discovery_info()

    # Get discovery input
    entity_type, filters = render_discovery_input()

    # Generate button
    if st.button("Generate", type="primary", use_container_width=True):
        try:
            # Show processing spinner
            with st.spinner(f"Discovering {entity_type}s..."):
                # Run discovery
                result = run_discovery(
                    entity_type=entity_type,
                    context=st.session_state.uploaded_context,
                    filters=filters,
                    target_count=10
                )

                # Store result in appropriate session state
                if entity_type == "Customer":
                    st.session_state.discovery_results_customers = result
                else:  # Partner
                    st.session_state.discovery_results_partners = result

                # Show success message
                st.success(f"Found {len(result.companies)} {entity_type.lower()}s!")

        except Exception as e:
            handle_discovery_error(e, entity_type)
            logger.error(f"Discovery error: {e}", exc_info=True)

else:
    # Query input section (only show if context exists)
    st.header("2. Discovery Query")
    st.info("Upload and process documents first to enable discovery")

# Results section (placeholder for now)
st.header("3. Discovery Results")
st.info("Results will be displayed here after running discovery")
