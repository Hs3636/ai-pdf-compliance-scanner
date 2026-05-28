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
