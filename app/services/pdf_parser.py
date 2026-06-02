import fitz
from typing import Dict, Any, List
from app.utils.logger import get_logger
import pytesseract
from PIL import Image
import io

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
        
        if len(doc) > 150:
            logger.error(f"PDF exceeds 150-page limit (Pages: {len(doc)}).")
            return {"errors": [f"PDF exceeds the 150-page limit (Current pages: {len(doc)})."]}
            
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text().strip()
            
            # OCR Fallback if no text found
            if not text:
                logger.info(f"No text found on page {page_num + 1}, attempting OCR...")
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img).strip()
                
            extracted_pages.append({
                "page_number": page_num + 1,
                "text": text
            })
            
        logger.info(f"Successfully extracted text from {len(doc)} pages.")
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        return {"errors": [f"PDF parsing error: {e}"]}
        
    return {"extracted_pages": extracted_pages}

def highlight_pdf_violations(pdf_bytes: bytes, violations: List[Dict[str, Any]]) -> bytes:
    """
    Highlights the detected violations within the PDF document based on the text value and page number.
    Returns the new PDF as bytes.
    """
    logger.info("Highlighting violations in PDF...")
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for v in violations:
            page_num = v.get("page", 0) - 1 # 1-indexed to 0-indexed
            value = v.get("value", "")
            severity = v.get("severity", "High")
            
            if 0 <= page_num < len(doc) and value:
                page = doc[page_num]
                # Search for the exact text snippet on the page
                text_instances = page.search_for(value)
                
                for inst in text_instances:
                    annot = page.add_highlight_annot(inst)
                    # Color coding based on severity
                    if severity == "Critical":
                        annot.set_colors(stroke=(0.54, 0.36, 0.96)) # Violet
                    elif severity == "High":
                        annot.set_colors(stroke=(0.93, 0.26, 0.26)) # Red
                    elif severity == "Medium":
                        annot.set_colors(stroke=(0.91, 0.7, 0.03))  # Yellow
                    else:
                        annot.set_colors(stroke=(0.13, 0.77, 0.36)) # Green
                    annot.update()
                    
        return doc.write()
    except Exception as e:
        logger.error(f"Error highlighting PDF: {e}")
        return pdf_bytes
