# Roadmap: Customer & Partner Discovery Prototype

## Overview

Build a working Google ADK prototype that discovers potential customers and partners by analyzing internal business documents and searching public data sources. The journey: set up foundation and document processing → build intelligent agent core → implement discovery engine → add scoring and rationale generation → create Streamlit UI → finalize with tracing and documentation.

## Phases

- [x] **Phase 1: Foundation & Document Processing** - Project setup, dependencies, document parsers
- [x] **Phase 2: Agent Core** - Google ADK agent with context understanding and query formulation
- [x] **Phase 3: Discovery Engine** - Customer and partner discovery using web search
- [ ] **Phase 4: Rationale & Scoring Agent** - Match scoring and rationale generation
- [ ] **Phase 5: UI & Presentation** - Streamlit interface with file upload and results display
- [ ] **Phase 6: Tracing & Documentation** - Prompt tracing, run reports, README

## Phase Details

### Phase 1: Foundation & Document Processing
**Goal**: Runnable project structure with parsers for all file formats (DOCX, PDF, CSV, PPTX)
**Depends on**: Nothing (first phase)
**Plans**: 3 plans

Plans:
- [x] 01-01: Project structure, dependencies, Google ADK setup (2025-12-13)
- [x] 01-02: Document parsers (DOCX, PDF) (2025-12-13)
- [x] 01-03: Document parsers (CSV, PPTX) + unified interface (2025-12-13)

### Phase 2: Agent Core
**Goal**: Google ADK agent that understands business context and formulates discovery queries
**Depends on**: Phase 1
**Plans**: 3 plans

Plans:
- [x] 02-01: Google ADK agent setup with system prompts (2025-12-13)
- [x] 02-02: Context extraction from parsed documents (2025-12-13)
- [x] 02-03: Query formulation logic for customer/partner discovery (2025-12-13)

### Phase 3: Discovery Engine
**Goal**: Working discovery system that finds customers and partners using web search
**Depends on**: Phase 2
**Plans**: 3 plans

Plans:
- [x] 03-01: Web search integration with Google ADK + result parsing (2025-12-13)
- [x] 03-02: Customer discovery logic (search, filter, enrich) (2025-12-13)
- [x] 03-03: Partner discovery logic (search, filter, enrich) (2025-12-13)

### Phase 4: Rationale & Scoring Agent
**Goal**: Intelligent scoring and rationale generation for all discovered entities
**Depends on**: Phase 3
**Plans**: 3 plans

Plans:
- [x] 04-01: Scoring algorithm design + implementation (2025-12-13)
- [ ] 04-02: Rationale generation agent with Google ADK
- [ ] 04-03: Integration with discovery results pipeline

### Phase 5: UI & Presentation
**Goal**: Complete Streamlit interface for file upload, queries, and results display
**Depends on**: Phase 4
**Plans**: 3 plans

Plans:
- [ ] 05-01: Streamlit app structure + file upload component
- [ ] 05-02: Query input interface + filters (geography, industry)
- [ ] 05-03: Results table with all fields (name, website, locations, size, rationale, sources)

### Phase 6: Tracing & Documentation
**Goal**: Complete tracing artifacts, documentation, and final polish
**Depends on**: Phase 5
**Plans**: 3 plans

Plans:
- [ ] 06-01: Prompt tracing to JSONL + run reports with timestamps
- [ ] 06-02: README with setup/run instructions + requirements.txt
- [ ] 06-03: Final testing, polish, and verification

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Document Processing | 3/3 | Complete | 2025-12-13 |
| 2. Agent Core | 3/3 | Complete | 2025-12-13 |
| 3. Discovery Engine | 3/3 | Complete | 2025-12-13 |
| 4. Rationale & Scoring Agent | 1/3 | In progress | - |
| 5. UI & Presentation | 0/3 | Not started | - |
| 6. Tracing & Documentation | 0/3 | Not started | - |
