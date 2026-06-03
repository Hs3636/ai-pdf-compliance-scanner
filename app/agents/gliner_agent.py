import os
import torch
from typing import List, Dict, Any

# EXTREMELY IMPORTANT for 512MB RAM limits:
# PyTorch will try to allocate a thread for every CPU core on the host machine.
# On a cloud server, this could be 32+ cores, instantly causing an Out Of Memory (OOM) crash.
# Restricting to 1 thread keeps memory usage tiny.
torch.set_num_threads(1)
os.environ["MALLOC_ARENA_MAX"] = "2" # Reduces memory fragmentation

from gliner import GLiNER
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Load model globally so it stays in memory after the first load
try:
    logger.info("Loading GLiNER-PII model...")
    model = GLiNER.from_pretrained("urchade/gliner_small-v2.1")
except Exception as e:
    logger.error(f"Failed to load GLiNER model: {e}")
    model = None

def run_gliner_pii_scan(pages: List[Dict[str, Any]], severity: str = "High") -> Dict[str, Any]:
    """
    Scans extracted PDF pages for PII using the in-memory GLiNER model.
    """
    logger.info("Starting GLiNER PII Scan...")
    violations = []
    errors = []

    if not model:
        return {"violations": [], "errors": ["GLiNER model failed to load. Cannot perform PII scan."]}

    # Labels for standard PII
    labels = ["person", "email", "phone number", "credit card", "social security number", "passport number"]

    try:
        for page in pages:
            page_num = page.get("page_number", 0)
            text = page.get("text", "").strip()
            if not text:
                continue
            
            # Predict entities
            entities = model.predict_entities(text, labels)
            
            for entity in entities:
                violations.append({
                    "reasoning": f"Identified PII entity of type '{entity['label']}' via GLiNER NER model.",
                    "type": "PII Detection",
                    "subtype": entity["label"].title(),
                    "value": entity["text"],
                    "page": page_num,
                    "severity": severity,
                    "confidence_score": round(float(entity["score"]), 2)
                })
                
    except Exception as e:
        logger.error(f"Error during GLiNER PII scan: {e}")
        errors.append(f"GLiNER PII scan failed: {e}")

    logger.info(f"GLiNER Scan complete. Found {len(violations)} PII violations.")
    return {"violations": violations, "errors": errors}
