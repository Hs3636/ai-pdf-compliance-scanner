import os
import threading
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.utils.logger import get_logger
from langfuse import Langfuse

logger = get_logger(__name__)

class EvaluationScores(BaseModel):
    faithfulness: float = Field(description="Score from 0.0 to 1.0 indicating if the violation text is perfectly grounded in the source text.")
    rule_relevance: float = Field(description="Score from 0.0 to 1.0 indicating if the text truly violates the described rule.")
    severity_accuracy: float = Field(description="Score from 0.0 to 1.0 indicating if the assigned severity is appropriate.")
    context_quality: float = Field(description="Score from 0.0 to 1.0 indicating if the extracted text has the right amount of context (not too much, not too little).")
    reasoning: str = Field(description="Brief explanation of the scores.")

EVAL_PROMPT = """You are an expert AI compliance evaluator.
Your task is to evaluate a single extracted compliance violation against the original source text.

Source Text:
{source_text}

Rule Details:
Rule Name: {rule_name}
Assigned Severity: {assigned_severity}

Extracted Violation Value:
{violation_value}
Extracted Reasoning:
{violation_reasoning}

Evaluate the extraction on the following 4 metrics (0.0 to 1.0):
1. faithfulness: Is the "Extracted Violation Value" actually present in the source text without hallucination? (1.0 if perfectly present, 0.0 if fabricated).
2. rule_relevance: Does the extracted value truly violate the "Rule Name" described? (1.0 if clear violation, 0.0 if false positive).
3. severity_accuracy: Is the "Assigned Severity" appropriate for this violation? (1.0 if perfect, 0.0 if completely wrong).
4. context_quality: Did the extraction grab the right amount of text? (1.0 if precise, 0.0 if it grabbed a whole irrelevant paragraph or too little to understand).

{format_instructions}
"""

def evaluate_violation(trace_id: str, violation: Dict[str, Any], source_text: str):
    """
    Evaluates a single violation and pushes scores to Langfuse.
    """
    try:
        host = os.environ.get("LANGFUSE_HOST") or os.environ.get("LANGFUSE_BASE_URL")
        langfuse = Langfuse(
            public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
            host=host
        )
        
        llm = ChatGroq(
            model="llama-3.1-8b-instant", # Use faster model for eval
            temperature=0,
        )
        parser = JsonOutputParser(pydantic_object=EvaluationScores)
        
        prompt = ChatPromptTemplate.from_template(EVAL_PROMPT).partial(
            format_instructions=parser.get_format_instructions()
        )
        
        chain = prompt | llm | parser
        
        logger.info(f"Evaluating violation for rule: {violation.get('subtype')}")
        result = chain.invoke({
            "source_text": source_text,
            "rule_name": violation.get("subtype", "Unknown"),
            "assigned_severity": violation.get("severity", "Unknown"),
            "violation_value": violation.get("value", ""),
            "violation_reasoning": violation.get("reasoning", "")
        })
        
        # Push scores to Langfuse
        langfuse.create_score(
            trace_id=trace_id,
            name="Faithfulness",
            value=result["faithfulness"],
            comment=result["reasoning"]
        )
        langfuse.create_score(
            trace_id=trace_id,
            name="Rule Relevance",
            value=result["rule_relevance"],
            comment=result["reasoning"]
        )
        langfuse.create_score(
            trace_id=trace_id,
            name="Severity Accuracy",
            value=result["severity_accuracy"],
            comment=result["reasoning"]
        )
        langfuse.create_score(
            trace_id=trace_id,
            name="Context Quality",
            value=result["context_quality"],
            comment=result["reasoning"]
        )
        
        logger.info(f"Successfully pushed eval scores to Langfuse trace {trace_id}")
        langfuse.flush()
        
    except Exception as e:
        logger.error(f"Error evaluating violation: {e}")

def run_evaluations_async(trace_id: str, violations: List[Dict[str, Any]], source_text: str):
    """
    Runs evaluation for a sample or all violations in a background thread
    so it doesn't block the UI.
    """
    if not os.environ.get("LANGFUSE_PUBLIC_KEY") or not trace_id:
        return
        
    # To save costs, we evaluate a maximum of 3 violations per trace.
    sample_violations = violations[:3]
    
    def target():
        for v in sample_violations:
            evaluate_violation(trace_id, v, source_text)
            
    thread = threading.Thread(target=target)
    thread.start()
