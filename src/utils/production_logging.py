"""
Production logging configuration that avoids file rotation issues.
Simple, robust logging for production deployments.
"""

import logging
import os
from pathlib import Path
from datetime import datetime


def setup_production_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Set up a production logger that avoids rotation conflicts.
    Uses timestamped log files to prevent concurrent access issues.
    """
    # Create logs directory in project root
    project_root = Path(__file__).parent.parent.parent
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # Production file handler - use timestamped filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    process_id = os.getpid()
    log_filename = f"mltrading_production_{timestamp}_{process_id}.log"

    file_handler = logging.FileHandler(logs_dir / log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    return logger


def get_deployment_logger(deployment_name: str) -> logging.Logger:
    """
    Get a logger specifically for deployment processes.
    """
    logger_name = f"mltrading.deployment.{deployment_name}"
    return setup_production_logger(logger_name, "INFO")


# Quick patch function to fix existing loggers


def patch_for_production():
    """
    Patch existing loggers to avoid rotation issues in production.
    Call this at the start of deployment scripts.
    """
    import logging.handlers

    # Find all loggers with RotatingFileHandler
    all_loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    all_loggers.append(logging.root)

    for logger in all_loggers:
        handlers_to_replace = []
        for handler in logger.handlers[:]:  # Create a copy of the list
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handlers_to_replace.append(handler)

        # Replace rotating handlers with simple file handlers
        for old_handler in handlers_to_replace:
            # Create new simple file handler
            new_handler = logging.FileHandler(old_handler.baseFilename)
            new_handler.setLevel(old_handler.level)
            new_handler.setFormatter(old_handler.formatter)

            # Replace handler
            logger.removeHandler(old_handler)
            logger.addHandler(new_handler)

            # Close old handler
            try:
                old_handler.close()
            except Exception:
                pass

