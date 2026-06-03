# AI-Powered PDF Compliance Scanner

## Project Overview

This project is an AI-powered PDF Compliance Scanning System that analyzes uploaded PDFs and checks them against configurable compliance policies using Generative AI and rule-based validations.

The system provides:
- PDF upload UI
- AI-driven compliance analysis
- LangGraph-based orchestration pipeline
- Page-wise compliance violation detection
- Configurable compliance rules via UI
- Downloadable compliance reports
- Live demo + presentation-ready architecture

The application focuses on text-based English PDFs and performs both deterministic and LLM-powered validations.

---

# Primary Objectives

The system should:

1. Upload and process PDFs
2. Extract page-wise text
3. Run compliance checks
4. Flag violations page-wise
5. Generate structured reports
6. Allow updating compliance rules dynamically
7. Provide explainable outputs using GenAI

---

# Compliance Checks

## 1. PII / Personal Information Detection
Detect:
- Emails
- Phone numbers
- Addresses
- IDs
- Names (optional enhancement)

Approach:
- Lightweight GLiNER NER Model (`urchade/gliner_small-v2.1`) running locally in-memory.

---

## 2. Confidential / Sensitive Information Detection

Detect:
- Internal company secrets
- Intellectual property references
- Financial information
- Proprietary business information
- Confidential keywords

Approach:
- LLM classification
- Keyword/rule matching
- Configurable rule sets

---

## 3. UTF-8 Encoding Consistency Validation

Validate:
- Text extraction compatibility
- Unsupported characters
- Corrupted encoding patterns
- English-only validation

Approach:
- Encoding validation utilities
- Character-set inspection
- Unicode normalization checks

---

## 4. Abusive / Unlawful Content Detection

Detect:
- Hate speech
- Abusive language
- Toxic content
- Illegal/unlawful references

Approach:
- Moderation prompt
- Toxicity classification
- Rule-based keyword validation

---

# Tech Stack

## Frontend
- Streamlit

## Backend / Orchestration
- Python
- LangGraph
- LangChain

## AI Models
- Groq-hosted models (Llama 3.3 for reasoning)
- GLiNER (Local lightweight NER for PII)

## PDF Processing
- PyMuPDF (fitz)

## Storage
- Local file system initially
- SQLite / JSON metadata storage

---

# High-Level Architecture

User Uploads PDF
        ↓
Streamlit UI
        ↓
LangGraph Workflow
        ↓
PDF Text Extraction
        ↓
Page-wise Processing
        ↓
Compliance Agents
    ├── PII Checker (GLiNER Agent)
    ├── Confidential Info Checker (Groq LLM)
    ├── UTF-8 Validator
    └── Toxic Content Checker (Groq LLM)
        ↓
Violation Aggregator
        ↓
Report Generator
        ↓
UI Report Download

---

# LangGraph Workflow Nodes

Suggested nodes:

1. upload_pdf
2. extract_text
3. preprocess_text
4. detect_pii
5. detect_confidential_info
6. validate_encoding
7. detect_abusive_content
8. aggregate_results
9. generate_report
10. persist_results
11. ui_response

---

# Suggested Project Structure

```text
pdf-compliance-scanner/
│
├── app/
│   ├── ui/
│   ├── workflows/
│   ├── agents/
│   ├── services/
│   ├── utils/
│   ├── prompts/
│   ├── reports/
│   └── config/
│
├── data/
│   ├── uploads/
│   ├── processed/
│   └── reports/
│
├── tests/
│
├── docs/
│
├── requirements.txt
├── .env
├── README.md
└── main.py