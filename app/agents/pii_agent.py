from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.utils.logger import get_logger
import os

logger = get_logger(__name__)

# Define the expected JSON structure using Pydantic
class PIIViolation(BaseModel):
    subtype: str = Field(description="The type of PII (e.g., Email, Phone, Address, Name, ID Number, Account Number)")
    value: str = Field(description="The exact text of the extracted PII")

class PIIViolationsList(BaseModel):
    violations: List[PIIViolation]

def get_pii_chain():
    """Initializes the LLM chain for PII extraction."""
    # Ensure API key is present
    if not os.environ.get("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY not found in environment!")
        
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,  # Deterministic output
    )
    
    parser = JsonOutputParser(pydantic_object=PIIViolationsList)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an expert compliance scanner. Your task is to extract all Personally Identifiable Information (PII) from the given text. "
         "PII includes: email addresses, phone numbers, personal names, physical addresses, ID numbers, account numbers, and passport-like identifiers. "
         "If no PII is found, return an empty list of violations.\n\n"
         "Format your output strictly according to these instructions:\n{format_instructions}"),
        ("human", "Text to scan:\n\n{text}")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    chain = prompt | llm | parser
    return chain

def run_pii_scan(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs the PII detection chain on each page of text.
    Returns a list of formatted violation dictionaries.
    """
    logger.info("Starting PII Scan across all pages.")
    all_violations = []
    
    try:
        chain = get_pii_chain()
    except Exception as e:
        logger.error(f"Failed to initialize PII chain: {e}")
        return [{"type": "PII", "subtype": "Error", "value": "Failed to initialize LLM", "page": 0, "severity": "High"}]

    for page in pages:
        page_num = page.get("page_number", 0)
        text = page.get("text", "")
        
        if not text.strip():
            continue
            
        try:
            logger.info(f"Scanning page {page_num} for PII...")
            result = chain.invoke({"text": text})
            
            # Result is parsed as dict matching PIIViolationsList
            extracted_violations = result.get("violations", [])
            
            for v in extracted_violations:
                subtype = v.get("subtype", "Unknown")
                # Default severity is High, but Medium for Names and Addresses
                severity = "High"
                if any(kw in subtype.lower() for kw in ["name", "address"]):
                    severity = "Medium"
                    
                all_violations.append({
                    "type": "PII",
                    "subtype": subtype,
                    "value": v.get("value", ""),
                    "page": page_num,
                    "severity": severity
                })
                
        except Exception as e:
            logger.error(f"Error scanning page {page_num} for PII: {e}")
            
    logger.info(f"PII Scan complete. Found {len(all_violations)} violations.")
    return all_violations
