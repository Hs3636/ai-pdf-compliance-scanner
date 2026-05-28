import unicodedata
from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)

def run_encoding_scan(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs deterministic text encoding checks to flag corruption, obfuscation,
    or significant non-English content.
    """
    logger.info("Starting Encoding Scan across all pages.")
    all_violations = []
    
    for page in pages:
        page_num = page.get("page_number", 0)
        text = page.get("text", "")
        
        if not text.strip():
            continue
            
        # 1. Check for Corrupted Characters
        # '\ufffd' is the standard unicode replacement character ()
        replacement_char_count = text.count('\ufffd')
        if replacement_char_count > 0:
            all_violations.append({
                "type": "Encoding",
                "subtype": "Corrupted Characters",
                "value": f"Found {replacement_char_count} replacement characters ()",
                "page": page_num,
                "severity": "Low"
            })
            
        # 2. English-Only Heuristics (Basic Latin/ASCII Ratio)
        # We expect a standard English document to be overwhelmingly ASCII printable chars.
        # Allowing some unicode punctuation.
        if len(text) > 50:  # Only check if there's substantial text
            ascii_count = sum(1 for char in text if ord(char) < 128)
            ratio = ascii_count / len(text)
            
            # If less than 85% is basic ASCII, it might be foreign or heavily symbol-based
            if ratio < 0.85:
                all_violations.append({
                    "type": "Encoding",
                    "subtype": "Non-English Content",
                    "value": f"Only {ratio*100:.1f}% basic Latin characters",
                    "page": page_num,
                    "severity": "Low"
                })
                
        # 3. Unicode Normalization Check (Obfuscation)
        # If NFKC normalization significantly changes the length, it implies weird unicode tricks.
        normalized = unicodedata.normalize('NFKC', text)
        if abs(len(normalized) - len(text)) > (len(text) * 0.1): # 10% change
            all_violations.append({
                "type": "Encoding",
                "subtype": "Irregular Normalization",
                "value": "Text significantly altered by NFKC normalization (potential obfuscation)",
                "page": page_num,
                "severity": "Medium"
            })
            
    logger.info(f"Encoding Scan complete. Found {len(all_violations)} violations.")
    return all_violations
