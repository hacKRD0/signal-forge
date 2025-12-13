# Customer & Partner Discovery Prototype

**One-liner**: Python prototype using Google ADK that discovers potential customers and partners by analyzing internal documents and searching public data sources.

## Problem

Companies struggle to systematically identify qualified prospects and partners. Existing approaches rely on manual LinkedIn scraping, lack context from internal business documents, and provide no traceability for how recommendations were generated. This prototype demonstrates automated, context-aware discovery using AI agents.

## Success Criteria

How we know it worked:

- [ ] Discovers 10 potential customers + 10 potential partners for a fictitious client
- [ ] Accepts multiple file formats (DOCX, PDF, CSV, PPTX) as internal context
- [ ] Provides rich results: company name, website, locations, size, rationale, sources
- [ ] UX allows natural language queries with optional filters (geography, industry)
- [ ] All prompts and agent outputs traced to local JSONL files with timestamps
- [ ] Complete README with setup/run instructions and requirements.txt
- [ ] Runnable locally without external API keys beyond Google ADK

## Constraints

- Python only
- Must use Google ADK (Agent Development Kit)
- Must use Google ADK's built-in web search tool (no external search APIs)
- No LinkedIn or social network scraping
- Search engine + publicly accessible sources only
- Local deployment only (no cloud hosting for v1.0)
- Streamlit for UX (faster prototyping)

## Out of Scope

What we're NOT building (prevents scope creep):

- LinkedIn scraping or social network integration
- Multi-user authentication or user management
- Cloud deployment or production hosting
- Real-time data streaming or webhooks
- Integration with CRM systems
- Advanced analytics or visualizations beyond basic tables
- Email outreach or contact enrichment
