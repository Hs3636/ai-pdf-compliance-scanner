from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.utils.logger import get_logger
from app.config.rules import load_rules
import os

logger = get_logger(__name__)

class CustomViolation(BaseModel):
    subtype: str = Field(description="The name of the rule that was violated")
    value: str = Field(description="The exact text of the extracted violation")
    severity: str = Field(description="Severity of the violation (Low, Medium, High, or Critical)")

class CustomViolationsList(BaseModel):
    violations: List[CustomViolation]

def get_custom_rules_chain(active_rules: List[Dict[str, Any]]):
    """Initializes the LLM chain for custom dynamic rules."""
    if not os.environ.get("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY not found in environment!")
        
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
    )
    
    parser = JsonOutputParser(pydantic_object=CustomViolationsList)
    
    # Format rules for prompt
    rules_text = "\n".join([f"- Rule Name: {r.get('name')}\n  Description: {r.get('description')}" for r in active_rules])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a strict Compliance & Security Auditor scanning documents. "
         "Your task is to evaluate the text against the following specific custom rules:\n\n"
         "{rules_text}\n\n"
         "If the text violates any of these rules, extract the exact text as the 'value'. "
         "Use the 'Rule Name' exactly as the 'subtype'. "
         "Autonomously determine the 'severity' (Low, Medium, High, or Critical) based on context and potential impact. "
         "If no rules are violated, return an empty list of violations.\n\n"
         "Format your output strictly according to these instructions:\n{format_instructions}"),
        ("human", "Text to scan:\n\n{text}")
    ]).partial(
        format_instructions=parser.get_format_instructions(),
        rules_text=rules_text
    )
    
    chain = prompt | llm | parser
    return chain

def run_custom_rules_scan(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs the custom dynamic rules detection chain on each page of text.
    Returns a list of formatted violation dictionaries.
    """
    logger.info("Starting Custom Rules Scan across all pages.")
    all_violations = []
    
    # Load and filter enabled rules
    rules = load_rules()
    active_rules = [r for r in rules if r.get("enabled", False)]
    
    if not active_rules:
        logger.info("No custom rules enabled. Skipping scan.")
        return []
    
    try:
        chain = get_custom_rules_chain(active_rules)
    except Exception as e:
        logger.error(f"Failed to initialize Custom Rules chain: {e}")
        return [{"type": "CustomRule", "subtype": "Error", "value": "Failed to initialize LLM", "page": 0, "severity": "High"}]

    for page in pages:
        page_num = page.get("page_number", 0)
        text = page.get("text", "")
        
        if not text.strip():
            continue
            
        try:
            logger.info(f"Scanning page {page_num} against {len(active_rules)} custom rules...")
            result = chain.invoke({"text": text})
            
            extracted_violations = result.get("violations", [])
            
            for v in extracted_violations:
                all_violations.append({
                    "type": "CustomRule",
                    "subtype": v.get("subtype", "Unknown"),
                    "value": v.get("value", ""),
                    "page": page_num,
                    "severity": v.get("severity", "High")
                })
                
        except Exception as e:
            logger.error(f"Error scanning page {page_num} for custom rules: {e}")
            
    logger.info(f"Custom Rules Scan complete. Found {len(all_violations)} violations.")
    return all_violations
