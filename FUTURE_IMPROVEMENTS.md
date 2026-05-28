# Future Improvements & Architectural Roadmap

This document outlines standard practices and architectural shifts required to transition the AI PDF Compliance Scanner from a local prototype to a production-ready, scalable application.

## 1. Deployment & Environment Setup
- **Platform Migration**: Transition away from serverless platforms (like Vercel) which are incompatible with persistent WebSocket applications. Deploy via containerized environments such as **Render**, **Heroku**, **AWS App Runner**, or **Hugging Face Spaces**.
- **Stateless Operation**: Modify the Streamlit app to operate without a local filesystem dependency. 
  - **Ephemeral Storage**: Ensure uploaded PDFs and generated reports are held in memory or temporary directories and immediately destroyed post-processing.
  - **Object Storage**: If historical persistence is required, integrate an S3-compatible object storage service to store PDFs securely.

## 2. Multi-User Concurrency & State Management
- **In-Memory Rules**: Currently, `data/rules.json` is a shared local file. To support multiple simultaneous users without overlapping rule sets, transition rule storage directly into `st.session_state`.
- **User Authentication**: Implement an authentication layer (e.g., Supabase, Auth0, or Firebase). 
- **Database Integration**: Store custom rules and historical JSON reports in a managed database (PostgreSQL/MongoDB) tied strictly to unique `user_id` identifiers.

## 3. Cost & Performance Optimization (API Calls)
- **Local Lightweight Models**: Offload generic compliance checks from expensive LLMs to local, open-source models:
  - **PII**: Integrate **Microsoft Presidio** (Regex/NLP based) to flag PII at zero API cost.
  - **Toxicity**: Utilize a lightweight local Hugging Face transformer (e.g., `distilbert-toxic`).
- **Mega-Prompt Aggregation**: Instead of executing separate LangGraph nodes for Confidentiality, Toxicity, and custom checks, combine them into a single comprehensive LLM prompt to reduce API calls by 75%.
- **Text Chunking**: Batch multiple PDF pages together (e.g., 5 pages per API call) to maximize the context window and minimize network overhead.

## 4. CLI Wrapper Development
- **Decoupled Interface**: Leverage the existing LangGraph orchestration (`app/workflows/graph.py`) to build a Command Line Interface using `argparse` or `Click`.
- **Example Usage**: `python cli.py scan report.pdf --rules custom.json --out ./reports`
- **CI/CD Integration**: A CLI wrapper enables the scanner to run headlessly in automated environments (e.g., GitHub Actions scanning PRs for compliance violations).
