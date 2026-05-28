import os
import json
from app.utils.logger import get_logger

logger = get_logger(__name__)

RULES_FILE = "data/rules.json"

DEFAULT_RULES = [
    {
        "name": "Confidentiality",
        "description": "Detect sensitive projects like Project Titan, Q4 Projections, or Trade Secrets.",
        "enabled": True
    },
    {
        "name": "Salary Check",
        "description": "Flag any mention of employee salaries or compensation packages.",
        "enabled": True
    }
]

def load_rules() -> list:
    if not os.path.exists(RULES_FILE):
        save_rules(DEFAULT_RULES)
        return DEFAULT_RULES
        
    try:
        with open(RULES_FILE, "r") as f:
            rules = json.load(f)
            if not isinstance(rules, list):
                logger.warning("rules.json is not a list. Resetting to defaults.")
                return DEFAULT_RULES
            return rules
    except Exception as e:
        logger.error(f"Failed to load rules.json: {e}")
        return DEFAULT_RULES

def save_rules(rules: list):
    os.makedirs(os.path.dirname(RULES_FILE), exist_ok=True)
    try:
        with open(RULES_FILE, "w") as f:
            json.dump(rules, f, indent=4)
        logger.info("Rules saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save rules.json: {e}")
