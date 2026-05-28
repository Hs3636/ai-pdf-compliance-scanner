from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.utils.logger import get_logger
import os

logger = get_logger(__name__)

class ToxicityViolation(BaseModel):
    subtype: str = Field(description="The type of toxic info (e.g., Hate Speech, Abusive Language, Illegal Content, Toxicity)")
    value: str = Field(description="The exact text of the extracted toxic or unlawful information")
    severity: str = Field(description="Severity of the violation (High or Critical)")
    explanation: str = Field(description="A brief justification of why this text was flagged as toxic/unlawful")

class ToxicityViolationsList(BaseModel):
    violations: List[ToxicityViolation]

def get_toxicity_chain():
    """Initializes the LLM chain for Toxicity extraction."""
    if not os.environ.get("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY not found in environment!")
        
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
    )
    
    parser = JsonOutputParser(pydantic_object=ToxicityViolationsList)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an expert Trust & Safety Content Moderator. "
         "Your task is to scan the text for Hate Speech, Abusive Language, Toxic Content, Targeted Harassment, and Unlawful/Illegal Activity references. "
         "If you find any such content, extract the exact text, classify the subtype, and provide a clear explanation of why it violates safety guidelines.\n\n"
         "If no toxic or unlawful information is found, return an empty list of violations.\n\n"
         "Format your output strictly according to these instructions:\n{format_instructions}"),
        ("human", "Text to scan:\n\n{text}")
    ]).partial(
        format_instructions=parser.get_format_instructions()
    )
    
    chain = prompt | llm | parser
    return chain

def run_toxicity_scan(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs the Toxicity detection chain on each page of text.
    Returns a list of formatted violation dictionaries.
    """
    logger.info("Starting Toxicity Scan across all pages.")
    all_violations = []
    
    try:
        chain = get_toxicity_chain()
    except Exception as e:
        logger.error(f"Failed to initialize Toxicity chain: {e}")
        return [{"type": "Toxicity", "subtype": "Error", "value": "Failed to initialize LLM", "page": 0, "severity": "High", "explanation": "API Error"}]

    for page in pages:
        page_num = page.get("page_number", 0)
        text = page.get("text", "")
        
        if not text.strip():
            continue
            
        try:
            logger.info(f"Scanning page {page_num} for Toxic/Unlawful Information...")
            result = chain.invoke({"text": text})
            
            extracted_violations = result.get("violations", [])
            
            for v in extracted_violations:
                all_violations.append({
                    "type": "Toxicity",
                    "subtype": v.get("subtype", "Unknown"),
                    "value": v.get("value", ""),
                    "page": page_num,
                    "severity": v.get("severity", "Critical"),
                    "explanation": v.get("explanation", "No explanation provided.")
                })
                
        except Exception as e:
            logger.error(f"Error scanning page {page_num} for Toxic Info: {e}")
            
    logger.info(f"Toxicity Scan complete. Found {len(all_violations)} violations.")
    return all_violations
