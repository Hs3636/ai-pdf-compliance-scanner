# 📄 AI-Powered PDF Compliance Scanner

A blazingly fast, fully stateless, AI-driven compliance engine built to autonomously scan PDF documents for sensitive data, toxicity, and custom policy violations.

## 🚀 Features

- **100% Stateless Architecture**: No documents or parsed text are ever saved to disk. Uploads, analysis, and report generation occur entirely in memory, making it highly secure and natively safe for concurrent multi-user cloud deployments (like Render or Vercel).
- **Hybrid AI Architecture**: Powered by LangGraph, the backend utilizes two specialized models:
  - **GLiNER (Local NER)**: A lightweight, in-memory model (`urchade/gliner_small-v2.1`) dedicated solely to high-speed PII Detection (SSNs, Emails, Phone Numbers, Credit Cards, etc.).
  - **Unified Mega-Agent**: A Groq-powered LLM (`llama-3.3-70b-versatile`) utilizing a single highly optimized "Mega-Prompt" to simultaneously evaluate complex compliance domains:
    - **Confidentiality**: Trade secrets, proprietary flags, and unreleased financials.
    - **Toxicity**: Hate speech and unlawful language.
    - **Custom Rules**: Your own company-specific guidelines.
- **Smart Page Batching**: Slashes LLM API costs by 95% by grouping and processing 5 PDF pages per batch for the LLM agent.
- **Beautiful PDF Reporting**: Generates a visually stunning, downloadable PDF report via `ReportLab` complete with metadata, a grey summary tally, and color-coded tables grouping violations by Severity (Critical, High, Medium, Low).
- **Interactive Rules Engine**: A sleek Streamlit UI allows you to add, edit, and toggle custom rules on the fly, including explicit Target Severity overrides. 
- **Telemetry & Evaluation**: Deep integration with Langfuse. Tracks tokens, API calls, latencies, and uses an asynchronous LLM-as-a-judge evaluator to score extractions on Faithfulness, Relevance, Severity, and Context Quality. You can build powerful dashboards natively in the Langfuse UI.

## 🏗️ Architecture Stack

- **Frontend**: Streamlit
- **Agent Orchestration**: LangGraph
- **LLM Integration**: LangChain & ChatGroq (`llama-3.3-70b-versatile`)
- **PII Detection Model**: GLiNER (`urchade/gliner_small-v2.1`) running locally in-memory
- **PDF Extraction**: PyMuPDF (`fitz`)
- **Report Generation**: ReportLab

## 📸 Architecture Diagram

![Architecture Diagram](docs/architecture_diagram.png)

## 🛠️ Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/ai-pdf-compliance.git
   cd ai-pdf-compliance
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables:**
   Create a `.env` file in the root directory and add your keys:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_HOST="https://cloud.langfuse.com" # Or your self-hosted URL
   ```

5. **Run the Application:**
   ```bash
   python -m streamlit run app/ui/main.py
   ```

## 🔒 Security & Privacy
This application does not persist data. When a user closes their browser tab, their session state (including custom rules) vanishes. Uploaded PDFs are instantly converted to byte streams and destroyed from memory the moment the response is dispatched.

---
*Built with LangGraph, Streamlit, and Groq.*
