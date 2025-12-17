# SignalForge

**AI-Powered Customer & Partner Discovery Engine**

SignalForge is an intelligent discovery platform that analyzes your business documents and automatically identifies potential customers and partners using advanced AI agents and web intelligence. Upload your business materials, and let AI find your next opportunities.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%202.0-orange.svg)](https://ai.google.dev/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)

---

## Features

- **Multi-Format Document Processing**: Parse DOCX, PDF, CSV, and PPTX files
- **AI Context Extraction**: Automatically understand your business from documents
- **Intelligent Discovery**: Find customers and partners using Google's web search
- **Match Scoring**: 4-dimensional scoring (relevance, geography, size, strategic fit)
- **AI Rationale**: Detailed explanations for why each match is relevant
- **Interactive UI**: Streamlit-based interface with filtering and export capabilities
- **Real-Time Search**: Live web search powered by Google ADK

---

## Architecture Overview

SignalForge uses a multi-agent AI architecture powered by Google's Agent Development Kit (ADK):

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                         │
│         (File Upload → Discovery → Results Display)         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Document Processing Layer                      │
│   • DOCX Parser    • PDF Parser                             │
│   • CSV Parser     • PPTX Parser                            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              AI Agent Core (Google ADK)                     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Context    │  │   Discovery  │  │   Scoring &  │       │
│  │  Extraction  │  │    Engine    │  │  Rationale   │       │
│  │    Agent     │  │  (Web Search)│  │    Agent     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                             │
│         Model: Gemini 2.0 Flash Exp                         │
└─────────────────────────────────────────────────────────────┘
```

### Three Specialized AI Agents

1. **Context Extraction Agent**: Analyzes business documents to extract industry, products, target market, and geography
2. **Discovery Agent**: Formulates search queries and finds potential matches via web search
3. **Scoring & Rationale Agent**: Evaluates match quality and generates detailed explanations

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Google AI API Key ([Get one here](https://ai.google.dev/))
- Git (for cloning the repository)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd easevertical
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**

   Create a `.env` file in the project root:
   ```bash
   GOOGLE_API_KEY=your_api_key_here
   ```

   Or export it as an environment variable:
   ```bash
   # Windows (PowerShell)
   $env:GOOGLE_API_KEY="your_api_key_here"

   # Windows (CMD)
   set GOOGLE_API_KEY=your_api_key_here

   # macOS/Linux
   export GOOGLE_API_KEY=your_api_key_here
   ```

### Running SignalForge

Start the Streamlit application:

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## Usage Guide

### Step 1: Upload Documents
- Click "Browse files" or drag & drop your business documents
- Supported formats: DOCX, PDF, CSV, PPTX
- Upload multiple files for comprehensive context

### Step 2: Review Extracted Context
- SignalForge analyzes your documents automatically
- Review the extracted business context (industry, products, target market)
- The AI understands your business from these materials

### Step 3: Configure Discovery
- Choose entity type: **Customers** or **Partners**
- Optional filters:
  - **Geography**: Target specific regions (e.g., "North America", "Europe")
  - **Industry**: Focus on specific industries (e.g., "SaaS", "Healthcare")
- Click **Generate** to start discovery

### Step 4: Review Results
- Browse discovered companies in tabbed interface
- View match scores (color-coded: Green = High, Yellow = Medium, Gray = Low)
- Expand company details to see:
  - Full description and size estimate
  - Score breakdown (4 dimensions)
  - AI-generated rationale
  - Source links for verification
- Export results as CSV or JSON

---

## Project Structure

```
easevertical/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .env                           # API keys (create this)
├── .planning/                     # Development planning docs
│   ├── ROADMAP.md
│   └── phases/
├── src/
│   ├── agent/                     # AI Agent components
│   │   ├── discovery_agent.py    # Main agent wrapper
│   │   ├── context_extractor.py  # Context extraction logic
│   │   ├── query_builder.py      # Search query formulation
│   │   ├── prompts.py            # System prompts
│   │   └── agent_setup.py        # Google ADK configuration
│   ├── discovery/                 # Discovery engine
│   │   ├── customer_discovery.py # Customer finding logic
│   │   ├── partner_discovery.py  # Partner finding logic
│   │   ├── web_search.py         # Web search integration
│   │   └── search_parser.py      # Result parsing
│   ├── scoring/                   # Match scoring
│   │   ├── match_scorer.py       # Multi-dimensional scoring
│   │   └── rationale_generator.py # AI rationale generation
│   ├── parsers/                   # Document parsers
│   │   ├── docx_parser.py
│   │   ├── pdf_parser.py
│   │   ├── csv_parser.py
│   │   ├── pptx_parser.py
│   │   └── document_parser.py    # Unified interface
│   ├── models/                    # Data models
│   │   ├── business_context.py
│   │   ├── discovery_results.py
│   │   ├── match_score.py
│   │   └── rationale.py
│   ├── ui/                        # Streamlit UI components
│   │   ├── components.py         # UI building blocks
│   │   ├── document_processor.py # File upload handling
│   │   ├── discovery_runner.py   # Discovery integration
│   │   ├── error_handler.py      # Error handling
│   │   └── results_display.py    # Results visualization
│   └── config.py                  # Configuration
└── tests/                         # Test suite
```

---

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google AI API key for Gemini | Yes | None |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |

### Model Configuration

Default model: `gemini-2.0-flash-exp`

To change the model, edit `src/agent/agent_setup.py`:
```python
def create_discovery_agent(
    model: str = "gemini-2.0-flash-exp",  # Change this
    temperature: float = 0.7,
    enable_web_search: bool = True,
):
```

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_discovery_integration.py
```

### Code Structure

SignalForge follows a modular architecture:
- **Parsers**: Independent document processing modules
- **Agents**: AI-powered business logic
- **Discovery**: Search and filtering logic
- **Scoring**: Match evaluation algorithms
- **UI**: Streamlit interface components

---

## Tech Stack

- **AI/ML**: Google Gemini 2.0 Flash Exp via Google ADK
- **Backend**: Python 3.9+
- **Web Framework**: Streamlit
- **Document Processing**: python-docx, PyPDF2, python-pptx, pandas
- **Testing**: pytest

---

## Limitations (Prototype)

This is a prototype version with the following limitations:
- **No persistent storage**: Results are session-based only
- **Single-user**: Not designed for concurrent multi-user access
- **Rate limits**: Subject to Google API rate limits
- **Web search only**: No integration with proprietary databases (LinkedIn, Crunchbase, etc.)
- **No authentication**: Open access (add auth for production)

---

## Roadmap

### Planned Features
- [ ] Vector database integration for semantic search
- [ ] Multi-model ensemble (Gemini + Claude + GPT-4)
- [ ] API endpoints for programmatic access
- [ ] Persistent storage (PostgreSQL)
- [ ] User authentication and multi-tenancy
- [ ] Batch processing for multiple document sets
- [ ] Integration with CRM systems (Salesforce, HubSpot)
- [ ] Advanced filtering (funding stage, tech stack, etc.)

See `.planning/ROADMAP.md` for detailed development phases.

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---
## Acknowledgments

Built with:
- [Google Gemini](https://ai.google.dev/) - AI model and agent framework
- [Streamlit](https://streamlit.io/) - Web UI framework
- [Claude Code](https://claude.ai/claude-code) - Development assistant

---

**SignalForge** - Discover Your Next Opportunity with AI
