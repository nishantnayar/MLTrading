import logging
import logging.handlers
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

def setup_logger(name: str, log_file: str = None, level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Log file path (optional)
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
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
    
    # Combined log handler (all components write to this)
    combined_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "mltrading_combined.log",
        maxBytes=50*1024*1024,  # 50MB
        backupCount=3
    )
    combined_handler.setLevel(logging.DEBUG)
    combined_handler.setFormatter(detailed_formatter)
    logger.addHandler(combined_handler)
    
    # Individual file handler (if log_file specified)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_ui_logger(component: str) -> logging.Logger:
    """
    Get a logger for UI components
    
    Args:
        component: Component name (e.g., 'api', 'dashboard')
    
    Returns:
        Configured logger for the component
    """
    return setup_logger(
        name=f"mltrading.ui.{component}",
        log_file=f"ui_{component}.log"
    )

def get_combined_logger(name: str) -> logging.Logger:
    """
    Get a logger that only writes to the combined log file
    
    Args:
        name: Logger name
    
    Returns:
        Configured logger that writes to combined log
    """
    return setup_logger(name=name)

def log_structured_event(component: str, level: str, message: str, 
                        metadata: Dict[str, Any] = None, logger: logging.Logger = None):
    """
    Log structured events with metadata for better parsing and analytics
    
    Args:
        component: Component name (e.g., 'api', 'dashboard', 'trading')
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        message: Log message
        metadata: Additional structured data
        logger: Logger instance (optional)
    """
    if logger is None:
        logger = get_combined_logger(f"mltrading.{component}")
    
    # Create structured log entry
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'component': component,
        'level': level.upper(),
        'message': message,
        'metadata': metadata or {}
    }
    
    # Log the structured entry
    log_message = f"STRUCTURED_LOG: {json.dumps(log_entry)}"
    getattr(logger, level.lower())(log_message)

def log_trading_event(event_type: str, symbol: str, details: str, 
                     metadata: Dict[str, Any] = None, logger: logging.Logger = None):
    """
    Log trading-specific events with structured data
    
    Args:
        event_type: Type of trading event (order, fill, signal, etc.)
        symbol: Trading symbol
        details: Event details
        metadata: Additional trading data
        logger: Logger instance (optional)
    """
    trading_metadata = {
        'event_type': event_type,
        'symbol': symbol,
        'trading_data': metadata or {}
    }
    
    log_structured_event('trading', 'INFO', details, trading_metadata, logger)

def log_system_event(event_type: str, details: str, 
                    metadata: Dict[str, Any] = None, logger: logging.Logger = None):
    """
    Log system-level events with structured data
    
    Args:
        event_type: Type of system event (startup, shutdown, error, etc.)
        details: Event details
        metadata: Additional system data
        logger: Logger instance (optional)
    """
    system_metadata = {
        'event_type': event_type,
        'system_data': metadata or {}
    }
    
    log_structured_event('system', 'INFO', details, system_metadata, logger)

def log_performance_event(operation: str, duration_ms: float, 
                         metadata: Dict[str, Any] = None, logger: logging.Logger = None):
    """
    Log performance metrics with structured data
    
    Args:
        operation: Operation name
        duration_ms: Duration in milliseconds
        metadata: Additional performance data
        logger: Logger instance (optional)
    """
    perf_metadata = {
        'operation': operation,
        'duration_ms': duration_ms,
        'performance_data': metadata or {}
    }
    
    log_structured_event('performance', 'INFO', 
                       f"Operation '{operation}' completed in {duration_ms:.2f}ms", 
                       perf_metadata, logger)

def log_request(request_info: dict, logger: logging.Logger = None):
    """
    Log HTTP request information with structured data
    
    Args:
        request_info: Dictionary containing request details
        logger: Logger instance (optional)
    """
    if logger is None:
        logger = get_ui_logger("api")
    
    # Extract performance data
    duration = request_info.get('duration', 0)
    status_code = request_info.get('status_code', 'UNKNOWN')
    
    # Create structured metadata
    metadata = {
        'method': request_info.get('method', 'UNKNOWN'),
        'path': request_info.get('path', 'UNKNOWN'),
        'status_code': status_code,
        'duration_ms': duration,
        'user_agent': request_info.get('user_agent', ''),
        'ip_address': request_info.get('ip_address', '')
    }
    
    # Log as structured event
    log_structured_event('api', 'INFO', 
                       f"Request: {metadata['method']} {metadata['path']} - "
                       f"Status: {status_code} - Duration: {duration}ms", 
                       metadata, logger)

def log_dashboard_event(event_type: str, details: str, 
                       metadata: Dict[str, Any] = None, logger: logging.Logger = None):
    """
    Log dashboard events with structured data
    
    Args:
        event_type: Type of event (e.g., 'user_action', 'data_update')
        details: Event details
        metadata: Additional dashboard data
        logger: Logger instance (optional)
    """
    dashboard_metadata = {
        'event_type': event_type,
        'dashboard_data': metadata or {}
    }
    
    log_structured_event('dashboard', 'INFO', 
                       f"Dashboard Event - {event_type}: {details}", 
                       dashboard_metadata, logger)

def get_combined_log_path() -> Path:
    """
    Get the path to the combined log file
    
    Returns:
        Path to the combined log file
    """
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    return logs_dir / "mltrading_combined.log"

def get_structured_logs_path() -> Path:
    """
    Get the path to the structured logs file
    
    Returns:
        Path to the structured logs file
    """
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    return logs_dir / "mltrading_structured.log"

def parse_structured_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a structured log line into components
    
    Args:
        line: Log line string
        
    Returns:
        Dictionary with parsed log components or None if invalid
    """
    if not line.startswith('STRUCTURED_LOG: '):
        return None
    
    try:
        # Extract JSON part after "STRUCTURED_LOG: "
        json_str = line[16:]  # Remove "STRUCTURED_LOG: " prefix
        log_entry = json.loads(json_str)
        return log_entry
    except (json.JSONDecodeError, IndexError):
        return None 