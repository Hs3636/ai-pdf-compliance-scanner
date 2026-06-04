from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.utils.logger import get_logger
from app.prompts.unified_prompt import UNIFIED_SYSTEM_PROMPT
from langfuse.langchain import CallbackHandler
from app.agents.evaluator import run_evaluations_async
import os

logger = get_logger(__name__)

class UnifiedViolation(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning explaining why this text violates the rule. Think before extracting the value.")
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
        ("system", UNIFIED_SYSTEM_PROMPT),
        ("human", "Text Batch to scan:\n\n{text_batch}")
    ]).partial(
        format_instructions=parser.get_format_instructions(),
        rules_text=rules_text if rules_text else "No custom rules enabled.",
        core_rules_text=core_rules_text
    )
    
    return prompt | llm | parser

def run_unified_scan(pages: List[Dict[str, Any]], custom_rules: List[Dict[str, Any]], core_rules: Dict[str, Dict[str, Any]], file_name: str = "Unknown Document") -> Dict[str, Any]:
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
        
    # Setup Langfuse handler if keys exist
    callbacks = []
    langfuse_handler = None
    if os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"):
        try:
            langfuse_handler = CallbackHandler()
            callbacks.append(langfuse_handler)
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse CallbackHandler: {e}")

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
                batch_text_parts.append(f"<page number=\"{page_num}\">\n{text}\n</page>")
                
        if not batch_text_parts:
            continue
            
        batch_text = "<document>\n" + "\n".join(batch_text_parts) + "\n</document>"
        
        try:
            logger.info(f"Scanning batch (Pages {batch[0].get('page_number')} to {batch[-1].get('page_number')})...")
            
            invoke_config = {
                "run_name": f"Scan: {file_name}",
                "metadata": {"session_id": f"Session_{file_name}"}
            }
            if callbacks:
                invoke_config["callbacks"] = callbacks
                
            result = chain.invoke({"text_batch": batch_text}, config=invoke_config)
            
            extracted_violations = result.get("violations", [])
            for v in extracted_violations:
                all_violations.append({
                    "reasoning": v.get("reasoning", ""),
                    "type": v.get("type", "Unknown"),
                    "subtype": v.get("subtype", "Unknown"),
                    "value": v.get("value", ""),
                    "page": v.get("page", 0),
                    "severity": v.get("severity", "High"),
                    "confidence_score": v.get("confidence_score", 1.0)
                })
                
            # Trigger asynchronous evaluation
            if langfuse_handler and extracted_violations:
                try:
                    trace_id = getattr(langfuse_handler, "last_trace_id", None)
                    if trace_id:
                        logger.info(f"Retrieved root trace_id: {trace_id}")
                        run_evaluations_async(trace_id, extracted_violations, batch_text)
                    else:
                        logger.warning("Could not fetch last_trace_id from langfuse_handler.")
                except Exception as eval_err:
                    logger.warning(f"Failed to trigger evaluation: {eval_err}")
                
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
