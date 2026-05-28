import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger with the standard format.
    """
    logger = logging.getLogger(name)
    
    # Only configure if it doesn't already have handlers to prevent duplicate logs
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
    return logger
