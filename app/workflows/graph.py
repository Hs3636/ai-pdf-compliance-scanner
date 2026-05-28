from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, START, END
from app.utils.logger import get_logger
from app.services.pdf_parser import parse_pdf
from app.utils.storage import save_json
import os

logger = get_logger(__name__)

# 1. Define the workflow state schema
class WorkflowState(TypedDict):
    file_path: str
    extracted_pages: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    report_paths: Dict[str, str]
    errors: List[str]

# 2. Define Nodes

def extract_text_node(state: WorkflowState) -> WorkflowState:
    logger.info("Executing node: extract_text_node")
    try:
        pages = parse_pdf(state["file_path"])
        
        # Save intermediate JSON as in Phase 2
        json_filename = f"{os.path.basename(state['file_path']).split('.')[0]}_parsed.json"
        json_filepath = os.path.join("data/processed", json_filename)
        save_json(pages, json_filepath)
        
        return {"extracted_pages": pages}
    except Exception as e:
        logger.error(f"Error in extract_text_node: {e}")
        return {"errors": state.get("errors", []) + [str(e)]}

def compliance_checks_node(state: WorkflowState) -> WorkflowState:
    logger.info("Executing node: compliance_checks_node")
    
    # Run PII Agent
    from app.agents.pii_agent import run_pii_scan
    pii_violations = run_pii_scan(state["extracted_pages"])
    
    # Run Confidentiality Agent
    from app.agents.confidential_agent import run_confidentiality_scan
    confidential_violations = run_confidentiality_scan(state["extracted_pages"])
    
    # Run Encoding Agent
    from app.agents.encoding_agent import run_encoding_scan
    encoding_violations = run_encoding_scan(state["extracted_pages"])
    
    # Run Toxicity Agent
    from app.agents.toxicity_agent import run_toxicity_scan
    toxicity_violations = run_toxicity_scan(state["extracted_pages"])
    
    # Run Custom Rules Agent
    from app.agents.custom_agent import run_custom_rules_scan
    custom_violations = run_custom_rules_scan(state["extracted_pages"])
    
    # Combine violations
    all_violations = (
        state.get("violations", []) + 
        pii_violations + 
        confidential_violations + 
        encoding_violations + 
        toxicity_violations +
        custom_violations
    )
    
    return {"violations": all_violations}

def report_generation_node(state: WorkflowState) -> WorkflowState:
    logger.info("Executing node: report_generation_node")
    from app.reports.generator import generate_report
    
    report_paths = generate_report(state)
    
    return {"report_paths": report_paths}

# 3. Build Graph
def build_graph() -> StateGraph:
    """Builds and returns the compliance orchestration state graph."""
    graph = StateGraph(WorkflowState)
    
    graph.add_node("extract_text", extract_text_node)
    graph.add_node("compliance_checks", compliance_checks_node)
    graph.add_node("report_generation", report_generation_node)
    
    graph.add_edge(START, "extract_text")
    graph.add_edge("extract_text", "compliance_checks")
    graph.add_edge("compliance_checks", "report_generation")
    graph.add_edge("report_generation", END)
    
    return graph.compile()
