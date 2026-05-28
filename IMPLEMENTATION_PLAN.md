# Phase 1 — Project Setup & Scaffolding

## Goal
Initialize the project structure and development environment.

## Tasks
- Create repository structure
- Setup virtual environment
- Install dependencies
- Configure environment variables
- Setup Streamlit starter app
- Setup LangGraph starter workflow
- Add logging utilities

## Deliverables
- Working project scaffold
- Basic Streamlit app
- LangGraph test workflow

---

# Phase 2 — PDF Processing Module

## Goal
Extract clean page-wise text from PDFs.

## Tasks
- Integrate PyMuPDF
- Upload PDF from UI
- Extract page-wise text
- Store extracted text
- Add preprocessing utilities
- Handle extraction failures

## Deliverables
- Functional PDF parser
- Page-wise extraction pipeline

---

# Phase 3 — LangGraph Workflow Design

## Goal
Build orchestrated compliance workflow.

## Tasks
- Define workflow state
- Create graph nodes
- Add sequential execution
- Add error handling
- Add execution tracing

## Suggested Nodes
- extract_text
- preprocess_text
- compliance_checks
- report_generation

## Deliverables
- End-to-end LangGraph pipeline

---

# Phase 4 — PII Detection Agent

## Goal
Detect personal information.

## Tasks
- Build regex detectors
- Integrate LLM validation
- Detect:
  - emails
  - phone numbers
  - addresses
- Add page references

## Deliverables
- PII detection module

---

# Phase 5 — Confidential Information Agent

## Goal
Detect sensitive/internal information.

## Tasks
- Create prompt templates
- Build LLM classification flow
- Add configurable keywords
- Add severity classification

## Deliverables
- Confidentiality checker

---

# Phase 6 — UTF-8 Validation Module

## Goal
Validate encoding consistency.

## Tasks
- Validate UTF-8 compatibility
- Detect corrupted characters
- Enforce English-only support
- Add normalization checks

## Deliverables
- Encoding validation module

---

# Phase 7 — Toxic/Unlawful Content Detection

## Goal
Detect abusive or unlawful content.

## Tasks
- Create moderation prompts
- Add toxicity keyword checks
- Add LLM moderation layer
- Generate explanations

## Deliverables
- Toxicity detection module

---

# Phase 8 — Report Generation

## Goal
Generate structured compliance reports.

## Tasks
- Aggregate violations
- Create severity scoring
- Generate JSON report
- Generate downloadable PDF/Markdown report
- Add timestamps and metadata

## Deliverables
- Downloadable reports

---

# Phase 9 — Streamlit UI Development

## Goal
Build interactive frontend.

## Features
- PDF upload
- Scan trigger
- Workflow progress
- Violation visualization
- Report download
- Rules management

## Deliverables
- Fully working UI

---

# Phase 10 — Dynamic Rules Management

## Goal
Allow compliance rules update from UI.

## Tasks
- Rules editor UI
- JSON/YAML-based rules
- Persist configuration
- Reload rules dynamically

## Deliverables
- Dynamic rule management

---

# Phase 11 — Testing & Validation

## Goal
Ensure reliability and correctness.

## Tasks
- Unit tests
- Integration tests
- Sample PDFs
- Failure handling tests
- Performance checks

## Deliverables
- Tested pipeline

---

# Phase 12 — Demo & Presentation Preparation

## Goal
Prepare final submission assets.

## Tasks
- Create architecture diagrams
- Record demo flow
- Prepare screenshots
- Create 10-slide PPT
- Finalize README

## PPT Suggested Sections
1. Problem Statement
2. Objectives
3. Architecture
4. LangGraph Workflow
5. AI Compliance Agents
6. Tech Stack
7. Demo Flow
8. Report Generation
9. Challenges & Enhancements
10. Conclusion

## Deliverables
- Final presentation
- Demo-ready application

---

# Suggested Development Order

1. Setup
2. PDF extraction
3. LangGraph workflow
4. PII checker
5. Toxicity checker
6. Confidential info checker
7. Encoding validator
8. Reporting
9. UI
10. Rules engine
11. Testing
12. PPT/demo

---

# Recommended Milestones

## Milestone 1
Basic upload + extraction working

## Milestone 2
LangGraph orchestration complete

## Milestone 3
All compliance agents functional

## Milestone 4
Report generation complete

## Milestone 5
UI fully integrated

## Milestone 6
Demo & PPT ready

---

# Suggested APIs / Models

## OpenAI
- GPT-4o-mini
- GPT-4.1

## Gemini
- Gemini 1.5 Flash
- Gemini 2.0 Flash

## Claude
- Claude Sonnet

## Groq
- Llama 3
- Mixtral

---

# Suggested Enhancements (Optional)

- Multi-PDF batch processing
- OCR support
- Async queues
- Docker deployment
- CI/CD pipeline
- User authentication
- Audit trail
- Vector database integration
- Human review workflow

---

# Success Criteria

The project is successful if:
- PDFs upload successfully
- All compliance checks execute correctly
- Violations are page-wise
- Reports are downloadable
- Rules can be updated dynamically
- LangGraph orchestration is visible
- Demo runs end-to-end successfully