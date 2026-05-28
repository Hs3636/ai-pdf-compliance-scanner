import fitz
from typing import Dict, Any, List
from app.utils.logger import get_logger

logger = get_logger(__name__)

def extract_text_from_pdf(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts text from a PDF document in memory using PyMuPDF.
    """
    logger.info("Starting PDF text extraction...")
    pdf_bytes = state.get("pdf_bytes")
    
    if not pdf_bytes:
        logger.error("No PDF bytes provided in the state.")
        return {"errors": ["No PDF bytes provided"]}
        
    extracted_pages = []
    
    try:
        # Open PDF from memory stream
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            extracted_pages.append({
                "page_number": page_num + 1,
                "text": text
            })
            
        logger.info(f"Successfully extracted text from {len(doc)} pages.")
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        return {"errors": [f"PDF parsing error: {e}"]}
        
    return {"extracted_pages": extracted_pages}
