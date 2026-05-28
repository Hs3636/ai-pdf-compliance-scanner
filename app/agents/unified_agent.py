from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.utils.logger import get_logger
import os

logger = get_logger(__name__)

class UnifiedViolation(BaseModel):
    type: str = Field(description="The primary category: 'PII', 'Confidentiality', 'Toxicity', or 'CustomRule'")
    subtype: str = Field(description="Specific type, e.g., 'SSN', 'Project Titan', 'Hate Speech', or the exact Rule Name.")
    value: str = Field(description="The exact text snippet that violated the rule.")
    page: int = Field(description="The integer page number where this violation was found.")
    severity: str = Field(description="Severity classification: 'Critical', 'High', 'Medium', or 'Low'.")

class UnifiedViolationsList(BaseModel):
    violations: List[UnifiedViolation]

def get_unified_chain(active_rules: List[Dict[str, Any]]):
    """Initializes the Unified Mega-Prompt LLM chain."""
    if not os.environ.get("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY not found in environment!")
        
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
    )
    
    parser = JsonOutputParser(pydantic_object=UnifiedViolationsList)
    
    # Format custom rules for prompt
    rules_text = ""
    for r in active_rules:
        sev_instruction = f"Target Severity: {r['severity']} (If 'Auto', you decide)" if 'severity' in r and r['severity'] else "Target Severity: Auto"
        rules_text += f"- Rule Name: {r.get('name')}\n  Description: {r.get('description')}\n  {sev_instruction}\n\n"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a strict Unified Compliance & Security Auditor scanning document batches. "
         "Your task is to evaluate the provided text against multiple compliance domains simultaneously.\n\n"
         
         "DOMAINS TO CHECK:\n"
         "1. PII: Extract ANY Personally Identifiable Information (SSNs, Emails, Phone Numbers, Credit Cards). Severity MUST be 'High' or 'Critical'.\n"
         "2. Confidentiality: Flag mentions of 'Internal Use Only', 'Proprietary', 'Trade Secret', or unreleased financials. Severity MUST be 'Critical'.\n"
         "3. Toxicity: Detect abusive, hateful, discriminatory, or unlawful language. Severity depends on context.\n"
         "4. Encoding: Detect suspicious obfuscation like Base64 blocks or garbled Unicode strings. Severity can be 'Low', 'Medium', or 'High'.\n"
         "5. Custom Rules: Evaluate against the following user-defined rules:\n"
         "{rules_text}\n"
         
         "INSTRUCTIONS:\n"
         "- Read the document text which is separated by --- PAGE X --- markers.\n"
         "- For every violation found across ANY domain, extract the exact text as the 'value'.\n"
         "- Set 'type' to one of ['PII', 'Confidentiality', 'Toxicity', 'Encoding', 'CustomRule'].\n"
         "- Determine 'severity' per the domain rules above. For CustomRules, override with the user's explicit Target Severity if it is not 'Auto'.\n"
         "- CRITICAL: Ensure the 'page' field correctly matches the --- PAGE X --- marker the text was found under.\n"
         "- If no rules are violated in the entire batch, return an empty list of violations.\n\n"
         
         "Format your output strictly according to these instructions:\n{format_instructions}"),
        ("human", "Text Batch to scan:\n\n{text_batch}")
    ]).partial(
        format_instructions=parser.get_format_instructions(),
        rules_text=rules_text if rules_text else "No custom rules enabled."
    )
    
    return prompt | llm | parser

def run_unified_scan(pages: List[Dict[str, Any]], custom_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batches pages and runs the Unified Agent to heavily reduce API calls.
    """
    logger.info("Starting Unified Mega-Scan across all pages.")
    all_violations = []
    
    active_rules = [r for r in custom_rules if r.get("enabled", False)]
    
    try:
        chain = get_unified_chain(active_rules)
    except Exception as e:
        logger.error(f"Failed to initialize Unified chain: {e}")
        return [{"type": "SystemError", "subtype": "Error", "value": "Failed to initialize LLM", "page": 0, "severity": "High"}]

    # Batching logic: 5 pages per batch
    BATCH_SIZE = 5
    for i in range(0, len(pages), BATCH_SIZE):
        batch = pages[i:i + BATCH_SIZE]
        
        # Construct the batch text with page markers
        batch_text_parts = []
        for page in batch:
            page_num = page.get("page_number", 0)
            text = page.get("text", "").strip()
            if text:
                batch_text_parts.append(f"--- PAGE {page_num} ---\n{text}\n")
                
        if not batch_text_parts:
            continue
            
        batch_text = "\n".join(batch_text_parts)
        
        try:
            logger.info(f"Scanning batch (Pages {batch[0].get('page_number')} to {batch[-1].get('page_number')})...")
            result = chain.invoke({"text_batch": batch_text})
            
            extracted_violations = result.get("violations", [])
            for v in extracted_violations:
                all_violations.append({
                    "type": v.get("type", "Unknown"),
                    "subtype": v.get("subtype", "Unknown"),
                    "value": v.get("value", ""),
                    "page": v.get("page", 0),
                    "severity": v.get("severity", "High")
                })
                
        except Exception as e:
            logger.error(f"Error scanning batch: {e}")
            
    logger.info(f"Unified Scan complete. Found {len(all_violations)} total violations.")
    return all_violations
