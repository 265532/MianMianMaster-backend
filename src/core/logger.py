import logging
import re
from typing import Any

class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in logs."""
    
    # Patterns for sensitive data
    SENSITIVE_PATTERNS = [
        (re.compile(r"('|\")password('|\")\s*:\s*('|\").*?('|\")", re.IGNORECASE), r"\1password\2: \3***\4"),
        (re.compile(r"('|\")token('|\")\s*:\s*('|\").*?('|\")", re.IGNORECASE), r"\1token\2: \3***\4"),
        (re.compile(r"('|\")access_token('|\")\s*:\s*('|\").*?('|\")", re.IGNORECASE), r"\1access_token\2: \3***\4"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True

def setup_logging() -> None:
    """Setup global logging configuration."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add sensitive data filter
        sensitive_filter = SensitiveDataFilter()
        console_handler.addFilter(sensitive_filter)
        
        logger.addHandler(console_handler)
