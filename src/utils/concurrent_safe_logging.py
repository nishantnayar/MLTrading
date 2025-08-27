"""
Concurrent-safe logging configuration for MLTrading system.
Handles file rotation issues in multi-process environments.
"""

import logging
import logging.handlers
import os
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional


class ConcurrentSafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Rotating file handler that safely handles concurrent access.
    Prevents PermissionError during log rotation in multi-process environments.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rotation_lock = threading.Lock()
    
    def doRollover(self):
        """
        Perform log rotation with proper locking to handle concurrent access.
        If rotation fails due to concurrent access, continue logging to current file.
        """
        with self._rotation_lock:
            try:
                super().doRollover()
            except (PermissionError, OSError) as e:
                # If rotation fails, log the error and continue with current file
                # This prevents the entire logging system from failing
                try:
                    self.stream.write(f"\n{datetime.now()} - LOG ROTATION WARNING: {e}\n")
                    self.stream.write(f"Continuing with current log file: {self.baseFilename}\n")
                    self.stream.flush()
                except:
                    # If we can't write to the log, there's nothing more we can do
                    pass


class ProcessSafeFileHandler(logging.FileHandler):
    """
    File handler that creates process-specific log files to avoid conflicts.
    """
    
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        # Add process ID to filename to avoid conflicts
        base_path = Path(filename)
        process_filename = base_path.parent / f"{base_path.stem}_{os.getpid()}{base_path.suffix}"
        super().__init__(str(process_filename), mode, encoding, delay)


def setup_concurrent_safe_logger(name: str, 
                                log_file: Optional[str] = None,
                                level: str = "INFO",
                                use_rotation: bool = True,
                                use_process_specific: bool = False) -> logging.Logger:
    """
    Set up a logger that safely handles concurrent access.
    
    Args:
        name: Logger name
        log_file: Optional specific log file name
        level: Logging level
        use_rotation: Whether to use rotating file handlers
        use_process_specific: Whether to create process-specific log files
    
    Returns:
        Configured logger
    """
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
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
    
    # File handler selection based on configuration
    if use_process_specific:
        # Use process-specific files to avoid conflicts entirely
        combined_handler = ProcessSafeFileHandler(
            logs_dir / "mltrading_combined.log"
        )
    elif use_rotation:
        # Use concurrent-safe rotation
        combined_handler = ConcurrentSafeRotatingFileHandler(
            logs_dir / "mltrading_combined.log",
            maxBytes=50*1024*1024,  # 50MB
            backupCount=3
        )
    else:
        # Use simple file handler (no rotation)
        combined_handler = logging.FileHandler(
            logs_dir / "mltrading_combined.log"
        )
    
    combined_handler.setLevel(logging.DEBUG)
    combined_handler.setFormatter(detailed_formatter)
    logger.addHandler(combined_handler)
    
    # Individual file handler if specified
    if log_file:
        if use_process_specific:
            file_handler = ProcessSafeFileHandler(logs_dir / log_file)
        elif use_rotation:
            file_handler = ConcurrentSafeRotatingFileHandler(
                logs_dir / log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        else:
            file_handler = logging.FileHandler(logs_dir / log_file)
        
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_production_logger(name: str) -> logging.Logger:
    """
    Get a production-ready logger that handles concurrent access safely.
    Uses process-specific logging to avoid rotation conflicts.
    """
    return setup_concurrent_safe_logger(
        name=name,
        level="INFO",
        use_rotation=False,  # Disable rotation in production to avoid conflicts
        use_process_specific=True  # Use process-specific files
    )


def cleanup_old_process_logs(max_age_hours: int = 24):
    """
    Clean up old process-specific log files.
    Should be called periodically in a maintenance task.
    """
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return
    
    cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
    
    for log_file in logs_dir.glob("*_*.log"):
        try:
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
        except (OSError, PermissionError):
            # If we can't delete, skip it
            pass


# Patch the existing logging configuration for production safety
def patch_existing_logging():
    """
    Patch existing loggers to use safer handlers.
    Call this at application startup to prevent rotation issues.
    """
    # Get all existing loggers
    existing_loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    
    for logger in existing_loggers:
        if not logger.handlers:
            continue
            
        # Replace RotatingFileHandler with safer alternatives
        handlers_to_replace = []
        for handler in logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handlers_to_replace.append(handler)
        
        for old_handler in handlers_to_replace:
            # Create new safe handler
            new_handler = ConcurrentSafeRotatingFileHandler(
                old_handler.baseFilename,
                maxBytes=old_handler.maxBytes,
                backupCount=old_handler.backupCount
            )
            new_handler.setLevel(old_handler.level)
            new_handler.setFormatter(old_handler.formatter)
            
            # Replace handler
            logger.removeHandler(old_handler)
            logger.addHandler(new_handler)
            
            # Close old handler
            old_handler.close()