from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.utils.logger import get_logger
import os

logger = get_logger(__name__)

class UnifiedViolation(BaseModel):
    type: str = Field(description="The primary category (e.g. 'PII Detection', 'Toxicity Filter', 'CustomRule').")
    subtype: str = Field(description="Specific type, e.g., 'SSN', 'Project Titan', 'Hate Speech', or the exact Rule Name.")
    value: str = Field(description="The exact text snippet that violated the rule.")
    page: int = Field(description="The integer page number where this violation was found.")
    severity: str = Field(description="Severity classification: 'Critical', 'High', 'Medium', or 'Low'.")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0 indicating certainty of the violation.")

class UnifiedViolationsList(BaseModel):
    violations: List[UnifiedViolation]

def get_unified_chain(active_rules: List[Dict[str, Any]], active_core_rules: List[Dict[str, Any]]):
    """Initializes the Unified Mega-Prompt LLM chain with dynamic rules."""
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
        
    # Format core rules for prompt
    core_rules_text = ""
    for idx, r in enumerate(active_core_rules):
        core_rules_text += f"{idx + 1}. {r.get('name')}: {r.get('description')}\n"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a strict Unified Compliance & Security Auditor scanning document batches. "
         "Your task is to evaluate the provided text against multiple compliance domains simultaneously.\n\n"
         
         "DOMAINS TO CHECK:\n"
         "{core_rules_text}"
         "{custom_rules_marker} Custom Rules: Evaluate against the following user-defined rules:\n"
         "{rules_text}\n"
         
         "INSTRUCTIONS:\n"
         "- Read the document text which is separated by --- PAGE X --- markers.\n"
         "- For every violation found across ANY domain, extract the exact text as the 'value'.\n"
         "- Set 'type' to one of the Domain names you evaluated (e.g., 'PII Detection', 'CustomRule').\n"
         "- Determine 'severity' per the domain rules above. For CustomRules, override with the user's explicit Target Severity if it is not 'Auto'.\n"
         "- Provide a 'confidence_score' between 0.0 and 1.0 indicating how certain you are that this is a true violation.\n"
         "- CRITICAL: Ensure the 'page' field correctly matches the --- PAGE X --- marker the text was found under.\n"
         "- If no rules are violated in the entire batch, return an empty list of violations.\n\n"
         
         "Format your output strictly according to these instructions:\n{format_instructions}"),
        ("human", "Text Batch to scan:\n\n{text_batch}")
    ]).partial(
        format_instructions=parser.get_format_instructions(),
        rules_text=rules_text if rules_text else "No custom rules enabled.",
        core_rules_text=core_rules_text,
        custom_rules_marker=f"{len(active_core_rules) + 1}."
    )
    
    return prompt | llm | parser

def run_unified_scan(pages: List[Dict[str, Any]], custom_rules: List[Dict[str, Any]], core_rules: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Batches pages and runs the Unified Agent to heavily reduce API calls.
    Returns a dictionary with 'violations' and 'errors'.
    """
    logger.info("Starting Unified Mega-Scan across all pages.")
    all_violations = []
    errors = []
    
    active_rules = [r for r in custom_rules if r.get("enabled", False)]
    active_core_rules = [r for r in core_rules.values() if r.get("enabled", True)]
    
    if not active_rules and not active_core_rules:
        logger.info("No core or custom rules enabled. Skipping scan.")
        return {"violations": [], "errors": []}
    
    try:
        chain = get_unified_chain(active_rules, active_core_rules)
    except Exception as e:
        logger.error(f"Failed to initialize Unified chain: {e}")
        return {"violations": [], "errors": ["Failed to initialize LLM pipeline. Ensure API keys are correct."]}

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
                    "severity": v.get("severity", "High"),
                    "confidence_score": v.get("confidence_score", 1.0)
                })
                
        except Exception as e:
            err_msg = str(e).lower()
            logger.error(f"Error scanning batch: {e}")
            if "429" in err_msg or "rate limit" in err_msg or "exhausted" in err_msg:
                errors.append("LLM Rate Limit / Token Quota exhausted. Please try again after some time.")
                break # Stop processing further batches if rate limited
            else:
                errors.append(f"LLM API Error on pages {batch[0].get('page_number')}-{batch[-1].get('page_number')}: {e}")
            
    logger.info(f"Unified Scan complete. Found {len(all_violations)} total violations.")
    return {"violations": all_violations, "errors": errors}
