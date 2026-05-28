import json
import os
from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)

def save_json(data: Any, filepath: str) -> bool:
    """
    Saves data to a JSON file.
    Creates directories if they don't exist.
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Successfully saved data to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON to {filepath}: {e}")
        return False

def load_json(filepath: str) -> Any:
    """
    Loads data from a JSON file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded data from {filepath}")
        return data
    except Exception as e:
        logger.error(f"Failed to load JSON from {filepath}: {e}")
        return None
