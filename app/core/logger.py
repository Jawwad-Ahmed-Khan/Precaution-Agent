import logging
import sys
from app.core.config import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a configured logger with the specified name.
    Ensures stdout output and specific formatting.
    """
    logger = logging.getLogger(name)
    
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Prevent duplicate handlers if called multiple times for the same logger
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        
        # Format: YYYY-MM-DD HH:MM:SS | LEVEL | module | message
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
