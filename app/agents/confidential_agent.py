from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.utils.logger import get_logger
import os

logger = get_logger(__name__)

# Hardcoded keywords for Phase 5
SENSITIVE_KEYWORDS = [
    "Project Titan", 
    "Internal Use Only", 
    "Confidential", 
    "Proprietary", 
    "Q4 Projections",
    "Unreleased Financials",
    "Trade Secret"
]

class ConfidentialViolation(BaseModel):
    subtype: str = Field(description="The type of confidential info (e.g., Intellectual Property, Internal Secret, Financial Data)")
    value: str = Field(description="The exact text of the extracted confidential information")
    severity: str = Field(description="Severity of the leak (Medium, High, or Critical)")

class ConfidentialViolationsList(BaseModel):
    violations: List[ConfidentialViolation]

def get_confidentiality_chain():
    """Initializes the LLM chain for Confidential Information extraction."""
    if not os.environ.get("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY not found in environment!")
        
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
    )
    
    parser = JsonOutputParser(pydantic_object=ConfidentialViolationsList)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a Corporate Security Officer scanning documents for data leaks. "
         "Your task is to extract all Confidential, Sensitive, Proprietary, or Internal-Only information. "
         "Pay special attention to the following sensitive keywords/topics if they appear: {keywords}\n\n"
         "If no confidential information is found, return an empty list of violations.\n\n"
         "Format your output strictly according to these instructions:\n{format_instructions}"),
        ("human", "Text to scan:\n\n{text}")
    ]).partial(
        format_instructions=parser.get_format_instructions(),
        keywords=", ".join(SENSITIVE_KEYWORDS)
    )
    
    chain = prompt | llm | parser
    return chain

def run_confidentiality_scan(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs the Confidentiality detection chain on each page of text.
    Returns a list of formatted violation dictionaries.
    """
    logger.info("Starting Confidentiality Scan across all pages.")
    all_violations = []
    
    try:
        chain = get_confidentiality_chain()
    except Exception as e:
        logger.error(f"Failed to initialize Confidentiality chain: {e}")
        return [{"type": "Confidentiality", "subtype": "Error", "value": "Failed to initialize LLM", "page": 0, "severity": "High"}]

    for page in pages:
        page_num = page.get("page_number", 0)
        text = page.get("text", "")
        
        if not text.strip():
            continue
            
        try:
            logger.info(f"Scanning page {page_num} for Confidential Information...")
            result = chain.invoke({"text": text})
            
            extracted_violations = result.get("violations", [])
            
            for v in extracted_violations:
                all_violations.append({
                    "type": "Confidentiality",
                    "subtype": v.get("subtype", "Unknown"),
                    "value": v.get("value", ""),
                    "page": page_num,
                    "severity": v.get("severity", "High")
                })
                
        except Exception as e:
            logger.error(f"Error scanning page {page_num} for Confidential Info: {e}")
            
    logger.info(f"Confidentiality Scan complete. Found {len(all_violations)} violations.")
    return all_violations
