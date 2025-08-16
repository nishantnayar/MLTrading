import logging
import logging.handlers
import os
import json
import gzip
import shutil
import threading
import time
import uuid
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor

# Import database logging components
try:
    from .database_logging import DatabaseLogHandler
    DATABASE_LOGGING_AVAILABLE = True
except ImportError:
    DATABASE_LOGGING_AVAILABLE = False
    DatabaseLogHandler = None

class SanitizingFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive information"""
    
    def format(self, record):
        # Sanitize the message
        if hasattr(record, 'msg') and record.msg:
            record.msg = sanitize_log_message(str(record.msg))
        
        # Add correlation ID if available
        try:
            correlation_id = get_correlation_id()
            if not hasattr(record, 'correlation_id'):
                record.correlation_id = correlation_id
        except:
            record.correlation_id = 'N/A'
        
        return super().format(record)

def setup_logger(name: str, log_file: str = None, level: str = "INFO", 
                 enable_database_logging: bool = True, 
                 file_log_level: str = "DEBUG",
                 db_log_level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with file, console, and optional database handlers
    
    Args:
        name: Logger name
        log_file: Log file path (optional)
        level: Overall logging level
        enable_database_logging: Whether to enable database logging
        file_log_level: Log level for file handlers
        db_log_level: Log level for database handler
    
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
    
    # Create formatters with sanitization
    detailed_formatter = SanitizingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
    )
    simple_formatter = SanitizingFormatter(
        '%(asctime)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
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
        file_handler.setLevel(getattr(logging, file_log_level.upper()))
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Database handler (if enabled and available)
    if enable_database_logging and DATABASE_LOGGING_AVAILABLE and DatabaseLogHandler:
        try:
            from ..data.storage.database import DatabaseManager
            db_manager = DatabaseManager()
            
            db_handler = DatabaseLogHandler(
                db_manager=db_manager,
                table_name="system_logs",
                max_queue_size=1000,
                batch_size=50,
                flush_interval=5.0
            )
            db_handler.setLevel(getattr(logging, db_log_level.upper()))
            logger.addHandler(db_handler)
            
        except Exception as e:
            # If database logging fails, log to file as fallback
            fallback_logger = logging.getLogger('database_setup_fallback')
            if not fallback_logger.handlers:
                # Set up minimal file handler for fallback
                fallback_handler = logging.FileHandler(logs_dir / "database_fallback.log")
                fallback_handler.setFormatter(detailed_formatter)
                fallback_logger.addHandler(fallback_handler)
            fallback_logger.error(f"Failed to set up database logging for {name}: {e}")
    
    return logger

def get_ui_logger(component: str, enable_database_logging: bool = True) -> logging.Logger:
    """
    Get a logger for UI components
    
    Args:
        component: Component name (e.g., 'api', 'dashboard')
        enable_database_logging: Whether to enable database logging
    
    Returns:
        Configured logger for the component
    """
    return setup_logger(
        name=f"mltrading.ui.{component}",
        log_file=f"ui_{component}.log",
        enable_database_logging=enable_database_logging,
        file_log_level="DEBUG",
        db_log_level="INFO"
    )

def get_combined_logger(name: str, enable_database_logging: bool = True) -> logging.Logger:
    """
    Get a logger that writes to combined log file and optionally to database
    
    Args:
        name: Logger name
        enable_database_logging: Whether to enable database logging
    
    Returns:
        Configured logger that writes to combined log and database
    """
    return setup_logger(name=name, enable_database_logging=enable_database_logging)

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

# Global variables for log management
_log_cleanup_thread = None
_cleanup_running = False
_correlation_context = threading.local()

# Sensitive data patterns for sanitization
SENSITIVE_PATTERNS = {
    'password': re.compile(r'(?i)(password["\s]*[=:]["\s]*)([^\s"]+)', re.IGNORECASE),
    'api_key': re.compile(r'(?i)(api[_-]?key["\s]*[=:]["\s]*)([^\s"]+)', re.IGNORECASE),
    'secret': re.compile(r'(?i)(secret["\s]*[=:]["\s]*)([^\s"]+)', re.IGNORECASE),
    'token': re.compile(r'(?i)(token["\s]*[=:]["\s]*)([^\s"]+)', re.IGNORECASE),
    'bearer': re.compile(r'(?i)(bearer[\s]+)([^\s]+)', re.IGNORECASE)
}

def sanitize_log_message(message: str) -> str:
    """
    Sanitize log messages by masking sensitive information
    
    Args:
        message: Raw log message
        
    Returns:
        Sanitized log message with sensitive data masked
    """
    sanitized = message
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        sanitized = pattern.sub(r'\1***MASKED***', sanitized)
    return sanitized

def get_correlation_id() -> str:
    """
    Get or create a correlation ID for the current thread
    
    Returns:
        Correlation ID string
    """
    if not hasattr(_correlation_context, 'correlation_id'):
        _correlation_context.correlation_id = str(uuid.uuid4())[:8]
    return _correlation_context.correlation_id

def set_correlation_id(correlation_id: str):
    """
    Set the correlation ID for the current thread
    
    Args:
        correlation_id: Correlation ID to set
    """
    _correlation_context.correlation_id = correlation_id

@contextmanager
def log_operation(operation_name: str, logger: logging.Logger = None, 
                 log_args: bool = False, **metadata):
    """
    Context manager for logging operations with automatic timing and error handling
    
    Args:
        operation_name: Name of the operation being performed
        logger: Logger instance to use
        log_args: Whether to log operation arguments
        **metadata: Additional metadata to include in logs
    """
    if logger is None:
        logger = get_combined_logger("mltrading.operation")
    
    correlation_id = get_correlation_id()
    start_time = time.time()
    
    # Sanitize metadata
    clean_metadata = {k: sanitize_log_message(str(v)) for k, v in metadata.items()}
    
    try:
        logger.info(f"[{correlation_id}] Starting operation: {operation_name}", 
                   extra={'correlation_id': correlation_id, 'operation': operation_name, 
                         'metadata': clean_metadata if log_args else {}})
        yield
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"[{correlation_id}] Completed operation: {operation_name} in {duration_ms:.2f}ms",
                   extra={'correlation_id': correlation_id, 'operation': operation_name,
                         'duration_ms': duration_ms, 'status': 'success'})
        
        # Log performance event
        log_performance_event(operation_name, duration_ms, 
                            {**clean_metadata, 'correlation_id': correlation_id}, logger)
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = sanitize_log_message(str(e))
        logger.error(f"[{correlation_id}] Failed operation: {operation_name} after {duration_ms:.2f}ms - {error_msg}",
                    extra={'correlation_id': correlation_id, 'operation': operation_name,
                          'duration_ms': duration_ms, 'status': 'error', 'error': error_msg},
                    exc_info=True)
        raise

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

def compress_log_file(file_path: Path) -> bool:
    """
    Compress a log file using gzip
    
    Args:
        file_path: Path to the log file to compress
        
    Returns:
        True if compression successful, False otherwise
    """
    try:
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file after successful compression
        file_path.unlink()
        return True
    except Exception as e:
        print(f"Error compressing log file {file_path}: {e}")
        return False

def consolidate_logs(logs_dir: Path = None, max_age_days: int = 7) -> Dict[str, Any]:
    """
    Consolidate old log files by compressing them
    
    Args:
        logs_dir: Directory containing log files
        max_age_days: Maximum age in days before compression
        
    Returns:
        Dictionary with consolidation results
    """
    if logs_dir is None:
        logs_dir = Path("logs")
    
    if not logs_dir.exists():
        return {'status': 'error', 'message': 'Logs directory does not exist'}
    
    results = {
        'compressed_files': [],
        'failed_files': [],
        'total_space_saved': 0,
        'errors': []
    }
    
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    
    try:
        # Find log files older than cutoff date
        for log_file in logs_dir.glob('*.log'):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                original_size = log_file.stat().st_size
                
                if compress_log_file(log_file):
                    compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
                    compressed_size = compressed_file.stat().st_size if compressed_file.exists() else 0
                    space_saved = original_size - compressed_size
                    
                    results['compressed_files'].append(str(log_file))
                    results['total_space_saved'] += space_saved
                else:
                    results['failed_files'].append(str(log_file))
        
        results['status'] = 'success'
        results['message'] = f"Compressed {len(results['compressed_files'])} files, saved {results['total_space_saved']} bytes"
        
    except Exception as e:
        results['status'] = 'error'
        results['message'] = f"Error during consolidation: {e}"
        results['errors'].append(str(e))
    
    return results

def cleanup_old_logs(logs_dir: Path = None, max_age_days: int = 30, 
                    max_compressed_age_days: int = 90) -> Dict[str, Any]:
    """
    Clean up old log files and compressed archives
    
    Args:
        logs_dir: Directory containing log files
        max_age_days: Maximum age for regular log files before deletion
        max_compressed_age_days: Maximum age for compressed files before deletion
        
    Returns:
        Dictionary with cleanup results
    """
    if logs_dir is None:
        logs_dir = Path("logs")
    
    if not logs_dir.exists():
        return {'status': 'error', 'message': 'Logs directory does not exist'}
    
    results = {
        'deleted_files': [],
        'deleted_compressed': [],
        'total_space_freed': 0,
        'errors': []
    }
    
    try:
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        compressed_cutoff_date = datetime.now() - timedelta(days=max_compressed_age_days)
        
        # Delete old regular log files
        for log_file in logs_dir.glob('*.log'):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    size = log_file.stat().st_size
                    log_file.unlink()
                    results['deleted_files'].append(str(log_file))
                    results['total_space_freed'] += size
                except Exception as e:
                    results['errors'].append(f"Failed to delete {log_file}: {e}")
        
        # Delete old compressed log files
        for compressed_file in logs_dir.glob('*.log.gz'):
            if compressed_file.stat().st_mtime < compressed_cutoff_date.timestamp():
                try:
                    size = compressed_file.stat().st_size
                    compressed_file.unlink()
                    results['deleted_compressed'].append(str(compressed_file))
                    results['total_space_freed'] += size
                except Exception as e:
                    results['errors'].append(f"Failed to delete {compressed_file}: {e}")
        
        results['status'] = 'success'
        results['message'] = f"Deleted {len(results['deleted_files'])} log files and {len(results['deleted_compressed'])} compressed files, freed {results['total_space_freed']} bytes"
        
    except Exception as e:
        results['status'] = 'error'
        results['message'] = f"Error during cleanup: {e}"
        results['errors'].append(str(e))
    
    return results

def start_log_cleanup_scheduler(cleanup_interval_hours: int = 24, 
                              consolidate_after_days: int = 7,
                              delete_after_days: int = 30,
                              delete_compressed_after_days: int = 90):
    """
    Start a background thread for periodic log cleanup
    
    Args:
        cleanup_interval_hours: Hours between cleanup runs
        consolidate_after_days: Days before consolidating logs
        delete_after_days: Days before deleting regular logs
        delete_compressed_after_days: Days before deleting compressed logs
    """
    global _log_cleanup_thread
    
    if _cleanup_running:
        return
    
    def cleanup_worker():
        global _cleanup_running
        _cleanup_running = True
        logger = get_combined_logger("mltrading.log_cleanup")
        
        while _cleanup_running:
            try:
                # Consolidate old logs
                consolidate_results = consolidate_logs(max_age_days=consolidate_after_days)
                if consolidate_results['status'] == 'success':
                    logger.info(f"Log consolidation completed: {consolidate_results['message']}")
                else:
                    logger.error(f"Log consolidation failed: {consolidate_results['message']}")
                
                # Clean up old logs
                cleanup_results = cleanup_old_logs(
                    max_age_days=delete_after_days,
                    max_compressed_age_days=delete_compressed_after_days
                )
                if cleanup_results['status'] == 'success':
                    logger.info(f"Log cleanup completed: {cleanup_results['message']}")
                else:
                    logger.error(f"Log cleanup failed: {cleanup_results['message']}")
                
                # Wait for next cleanup cycle
                time.sleep(cleanup_interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Error in log cleanup worker: {e}")
                time.sleep(3600)  # Wait 1 hour before retrying
    
    _log_cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    _log_cleanup_thread.start()

def stop_log_cleanup_scheduler():
    """
    Stop the log cleanup scheduler
    """
    global _cleanup_running
    _cleanup_running = False

def get_log_statistics(logs_dir: Path = None) -> Dict[str, Any]:
    """
    Get statistics about log files
    
    Args:
        logs_dir: Directory containing log files
        
    Returns:
        Dictionary with log statistics
    """
    if logs_dir is None:
        logs_dir = Path("logs")
    
    if not logs_dir.exists():
        return {'status': 'error', 'message': 'Logs directory does not exist'}
    
    stats = {
        'total_log_files': 0,
        'total_compressed_files': 0,
        'total_size': 0,
        'oldest_file': None,
        'newest_file': None,
        'files_by_age': {'1d': 0, '7d': 0, '30d': 0, 'older': 0}
    }
    
    now = datetime.now()
    
    try:
        all_files = list(logs_dir.glob('*.log*'))
        
        for log_file in all_files:
            file_stat = log_file.stat()
            file_age = now - datetime.fromtimestamp(file_stat.st_mtime)
            
            stats['total_size'] += file_stat.st_size
            
            if log_file.suffix == '.log':
                stats['total_log_files'] += 1
            elif log_file.suffix == '.gz':
                stats['total_compressed_files'] += 1
            
            # Track oldest and newest files
            if stats['oldest_file'] is None or file_stat.st_mtime < stats['oldest_file']['mtime']:
                stats['oldest_file'] = {'name': str(log_file), 'mtime': file_stat.st_mtime}
            
            if stats['newest_file'] is None or file_stat.st_mtime > stats['newest_file']['mtime']:
                stats['newest_file'] = {'name': str(log_file), 'mtime': file_stat.st_mtime}
            
            # Categorize by age
            if file_age.days <= 1:
                stats['files_by_age']['1d'] += 1
            elif file_age.days <= 7:
                stats['files_by_age']['7d'] += 1
            elif file_age.days <= 30:
                stats['files_by_age']['30d'] += 1
            else:
                stats['files_by_age']['older'] += 1
        
        stats['status'] = 'success'
        
    except Exception as e:
        stats['status'] = 'error'
        stats['message'] = f"Error getting log statistics: {e}"
    
    return stats 