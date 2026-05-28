import fitz  # PyMuPDF
from typing import List, Dict
from app.utils.logger import get_logger

logger = get_logger(__name__)

def preprocess_text(text: str) -> str:
    """
    Applies basic text preprocessing.
    Currently just strips leading/trailing whitespaces and removes excessive newlines.
    """
    if not text:
        return ""
    
    # Basic strip
    cleaned = text.strip()
    
    # Replace multiple spaces/newlines with single spaces if necessary,
    # but for PDFs we often want to keep paragraphs, so we'll just stick to basic stripping for now
    # as per phase 2 plan.
    return cleaned

def parse_pdf(file_path: str) -> List[Dict[str, str]]:
    """
    Opens a PDF file and extracts text page by page.
    Returns a list of dictionaries, where each dict represents a page.
    """
    pages_data = []
    
    try:
        logger.info(f"Starting PDF extraction for: {file_path}")
        # Open document
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            
            cleaned_text = preprocess_text(text)
            
            pages_data.append({
                "page_number": page_num + 1,
                "text": cleaned_text
            })
            
        doc.close()
        logger.info(f"Successfully extracted {len(pages_data)} pages from {file_path}")
        return pages_data
        
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        raise
