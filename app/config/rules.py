from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_RULES = [
    {
        "name": "Salary Check",
        "description": "Flag any mention of employee salaries or compensation packages.",
        "severity": "Auto (LLM Decides)",
        "enabled": True
    }
]

CORE_RULES = {
    "PII": {
        "name": "PII Detection",
        "description": "Extract ANY Personally Identifiable Information (SSNs, Emails, Phone Numbers, Credit Cards). Severity MUST be 'High' or 'Critical'.",
        "enabled": True
    },
    "Confidentiality": {
        "name": "Confidentiality Check",
        "description": "Flag mentions of 'Internal Use Only', 'Proprietary', 'Trade Secret', or unreleased financials. Severity MUST be 'Critical'.",
        "enabled": True
    },
    "Toxicity": {
        "name": "Toxicity Filter",
        "description": "Detect abusive, hateful, discriminatory, or unlawful language. Severity depends on context.",
        "enabled": True
    },
    "Encoding": {
        "name": "Encoding/Obfuscation",
        "description": "Detect suspicious obfuscation like Base64 blocks or garbled Unicode strings. Severity can be 'Low', 'Medium', or 'High'.",
        "enabled": True
    }
}
