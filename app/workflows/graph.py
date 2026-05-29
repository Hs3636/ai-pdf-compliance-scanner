from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, START, END
from app.utils.logger import get_logger
import os

logger = get_logger(__name__)

# 1. Define the workflow state schema
class WorkflowState(TypedDict):
    file_name: str
    pdf_bytes: bytes
    extracted_pages: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    report_pdf_bytes: bytes
    report_json_str: str
    errors: List[str]
    custom_rules: List[Dict[str, Any]]
    core_rules: Dict[str, Dict[str, Any]]

# 2. Define Nodes

def extract_text_node(state: WorkflowState) -> WorkflowState:
    logger.info("Executing node: extract_text_node")
    try:
        from app.services.pdf_parser import extract_text_from_pdf
        
        result = extract_text_from_pdf(state)
        
        if result.get("errors"):
            return {"errors": state.get("errors", []) + result["errors"]}
            
        return {"extracted_pages": result.get("extracted_pages", [])}
    except Exception as e:
        logger.error(f"Error in extract_text_node: {e}")
        return {"errors": state.get("errors", []) + [str(e)]}

def compliance_checks_node(state: WorkflowState) -> Dict[str, Any]:
    logger.info("Executing node: compliance_checks_node")
    
    from app.agents.unified_agent import run_unified_scan
    
    all_violations = state.get("violations", [])
    current_errors = state.get("errors", [])
    
    # Run the mega-agent over batched pages
    result = run_unified_scan(
        state["extracted_pages"], 
        state.get("custom_rules", []),
        state.get("core_rules", {})
    )
    
    all_violations.extend(result.get("violations", []))
    if result.get("errors"):
        current_errors.extend(result["errors"])
    
    return {"violations": all_violations, "errors": current_errors}

def report_generation_node(state: WorkflowState) -> Dict[str, Any]:
    logger.info("Executing node: report_generation_node")
    from app.reports.generator import generate_reports
    
    result = generate_reports(state)
        
    return result

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
