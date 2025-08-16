"""
Database Logging Handler
Implements logging to PostgreSQL database with connection pooling and error handling
"""

import logging
import json
import threading
import time
import traceback
import psutil
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from queue import Queue, Empty
from contextlib import contextmanager

from ..data.storage.database import DatabaseManager
from .logging_config import get_correlation_id, sanitize_log_message

class DatabaseLogHandler(logging.Handler):
    """
    Custom logging handler that writes logs to PostgreSQL database
    """
    
    def __init__(self, db_manager: DatabaseManager = None, 
                 table_name: str = "system_logs",
                 max_queue_size: int = 1000,
                 batch_size: int = 50,
                 flush_interval: float = 5.0):
        """
        Initialize database log handler
        
        Args:
            db_manager: Database manager instance
            table_name: Table name for logs
            max_queue_size: Maximum queue size before dropping logs
            batch_size: Number of logs to write in one batch
            flush_interval: Seconds between batch writes
        """
        super().__init__()
        
        self.db_manager = db_manager or DatabaseManager()
        self.table_name = table_name
        self.max_queue_size = max_queue_size
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Thread-safe queue for log records
        self.log_queue = Queue(maxsize=max_queue_size)
        self.shutdown_event = threading.Event()
        
        # Background thread for writing logs
        self.writer_thread = threading.Thread(target=self._log_writer, daemon=True)
        self.writer_thread.start()
        
        # Statistics
        self.stats = {
            'logs_written': 0,
            'logs_dropped': 0,
            'write_errors': 0,
            'last_write': None
        }
    
    def emit(self, record):
        """
        Emit a log record to the database queue
        
        Args:
            record: LogRecord instance
        """
        try:
            # Don't log database-related errors to avoid infinite loops
            if 'database' in record.name.lower() or 'psycopg' in record.name.lower():
                return
            
            # Sanitize the message
            if hasattr(record, 'getMessage'):
                message = sanitize_log_message(record.getMessage())
            else:
                message = sanitize_log_message(str(record.msg))
            
            # Get correlation ID
            correlation_id = getattr(record, 'correlation_id', None)
            if not correlation_id:
                try:
                    correlation_id = get_correlation_id()
                except:
                    correlation_id = None
            
            # Prepare log entry
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc),
                'level': record.levelname,
                'logger_name': record.name,
                'correlation_id': correlation_id,
                'message': message,
                'module': getattr(record, 'module', record.filename if hasattr(record, 'filename') else None),
                'function_name': getattr(record, 'funcName', None),
                'line_number': getattr(record, 'lineno', None),
                'thread_name': getattr(record, 'threadName', None),
                'process_id': getattr(record, 'process', os.getpid()),
                'metadata': self._extract_metadata(record)
            }
            
            # Add to queue (non-blocking)
            try:
                self.log_queue.put_nowait(log_entry)
            except:
                # Queue is full, drop the log entry
                self.stats['logs_dropped'] += 1
                
        except Exception as e:
            # Don't raise exceptions from logging handlers
            self.handleError(record)
    
    def _extract_metadata(self, record) -> Dict[str, Any]:
        """
        Extract metadata from log record
        
        Args:
            record: LogRecord instance
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                try:
                    # Ensure value is JSON serializable
                    json.dumps(value)
                    metadata[key] = value
                except (TypeError, ValueError):
                    metadata[key] = str(value)
        
        # Add system metrics if available
        try:
            process = psutil.Process()
            metadata['memory_usage_mb'] = process.memory_info().rss / 1024 / 1024
            metadata['cpu_percent'] = process.cpu_percent()
        except:
            pass
        
        return metadata
    
    def _log_writer(self):
        """
        Background thread that writes logs to database in batches
        """
        batch = []
        last_flush = time.time()
        
        while not self.shutdown_event.is_set():
            try:
                # Collect logs from queue
                while len(batch) < self.batch_size:
                    try:
                        timeout = max(0.1, self.flush_interval - (time.time() - last_flush))
                        log_entry = self.log_queue.get(timeout=timeout)
                        batch.append(log_entry)
                    except Empty:
                        break
                
                # Write batch if we have logs or enough time has passed
                if batch and (len(batch) >= self.batch_size or 
                             time.time() - last_flush >= self.flush_interval):
                    self._write_batch(batch)
                    batch.clear()
                    last_flush = time.time()
                
            except Exception as e:
                self.stats['write_errors'] += 1
                # Clear batch to avoid infinite error loop
                batch.clear()
                time.sleep(1)  # Brief pause before retrying
    
    def _write_batch(self, batch: List[Dict[str, Any]]):
        """
        Write a batch of log entries to database
        
        Args:
            batch: List of log entries
        """
        if not batch:
            return
        
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Prepare SQL
                    sql = f"""
                    INSERT INTO {self.table_name} 
                    (timestamp, level, logger_name, correlation_id, message, 
                     module, function_name, line_number, thread_name, process_id, metadata)
                    VALUES (%(timestamp)s, %(level)s, %(logger_name)s, %(correlation_id)s, %(message)s,
                            %(module)s, %(function_name)s, %(line_number)s, %(thread_name)s, %(process_id)s, %(metadata)s)
                    """
                    
                    # Execute batch insert
                    cursor.executemany(sql, batch)
                    conn.commit()
                    
                    self.stats['logs_written'] += len(batch)
                    self.stats['last_write'] = datetime.now()
                    
        except Exception as e:
            self.stats['write_errors'] += 1
            # Log to file as fallback (avoid infinite recursion)
            try:
                fallback_logger = logging.getLogger('database_log_fallback')
                fallback_logger.error(f"Failed to write {len(batch)} logs to database: {e}")
            except:
                pass  # Give up if fallback also fails
    
    def flush(self):
        """
        Flush any pending log records
        """
        # Signal the writer thread to flush
        start_time = time.time()
        while not self.log_queue.empty() and time.time() - start_time < 5:
            time.sleep(0.1)
    
    def close(self):
        """
        Close the handler and clean up resources
        """
        self.shutdown_event.set()
        
        # Flush remaining logs
        self.flush()
        
        # Wait for writer thread to finish
        if self.writer_thread.is_alive():
            self.writer_thread.join(timeout=10)
        
        super().close()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get handler statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            **self.stats,
            'queue_size': self.log_queue.qsize(),
            'thread_alive': self.writer_thread.is_alive()
        }

class TradingEventLogger:
    """
    Specialized logger for trading events
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
    
    def log_trading_event(self, event_type: str, symbol: str = None, 
                         side: str = None, quantity: float = None, 
                         price: float = None, order_id: str = None,
                         strategy: str = None, **metadata):
        """
        Log a trading event to database
        
        Args:
            event_type: Type of event ('order_placed', 'order_filled', etc.)
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Order quantity
            price: Order price
            order_id: Order identifier
            strategy: Strategy name
            **metadata: Additional metadata
        """
        try:
            correlation_id = get_correlation_id()
            
            event_data = {
                'timestamp': datetime.now(tz=timezone.utc),
                'event_type': event_type,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_id': order_id,
                'strategy': strategy,
                'correlation_id': correlation_id,
                'metadata': json.dumps(metadata) if metadata else None
            }
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                    INSERT INTO trading_events 
                    (timestamp, event_type, symbol, side, quantity, price, 
                     order_id, strategy, correlation_id, metadata)
                    VALUES (%(timestamp)s, %(event_type)s, %(symbol)s, %(side)s, %(quantity)s, 
                            %(price)s, %(order_id)s, %(strategy)s, %(correlation_id)s, %(metadata)s)
                    """
                    cursor.execute(sql, event_data)
                    conn.commit()
                    
        except Exception as e:
            # Fallback to file logging
            fallback_logger = logging.getLogger('trading_events_fallback')
            fallback_logger.error(f"Failed to log trading event: {e}")

class PerformanceLogger:
    """
    Specialized logger for performance metrics
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
    
    def log_performance(self, operation_name: str, duration_ms: float,
                       status: str = 'success', component: str = None, **metadata):
        """
        Log performance metrics to database
        
        Args:
            operation_name: Name of the operation
            duration_ms: Duration in milliseconds
            status: 'success', 'error', or 'timeout'
            component: Component name
            **metadata: Additional metadata
        """
        try:
            correlation_id = get_correlation_id()
            
            # Get system metrics
            try:
                process = psutil.Process()
                memory_usage_mb = process.memory_info().rss / 1024 / 1024
                cpu_usage_percent = process.cpu_percent()
            except:
                memory_usage_mb = None
                cpu_usage_percent = None
            
            perf_data = {
                'timestamp': datetime.now(tz=timezone.utc),
                'operation_name': operation_name,
                'duration_ms': duration_ms,
                'status': status,
                'component': component,
                'correlation_id': correlation_id,
                'memory_usage_mb': memory_usage_mb,
                'cpu_usage_percent': cpu_usage_percent,
                'metadata': json.dumps(metadata) if metadata else None
            }
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                    INSERT INTO performance_logs 
                    (timestamp, operation_name, duration_ms, status, component,
                     correlation_id, memory_usage_mb, cpu_usage_percent, metadata)
                    VALUES (%(timestamp)s, %(operation_name)s, %(duration_ms)s, %(status)s, %(component)s,
                            %(correlation_id)s, %(memory_usage_mb)s, %(cpu_usage_percent)s, %(metadata)s)
                    """
                    cursor.execute(sql, perf_data)
                    conn.commit()
                    
        except Exception as e:
            # Fallback to file logging
            fallback_logger = logging.getLogger('performance_fallback')
            fallback_logger.error(f"Failed to log performance data: {e}")

@contextmanager
def log_performance_to_db(operation_name: str, component: str = None, **metadata):
    """
    Context manager for logging performance to database
    
    Args:
        operation_name: Name of the operation
        component: Component name
        **metadata: Additional metadata
    """
    perf_logger = PerformanceLogger()
    start_time = time.time()
    
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        perf_logger.log_performance(operation_name, duration_ms, 'success', component, **metadata)
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        perf_logger.log_performance(operation_name, duration_ms, 'error', component, 
                                   error=str(e), **metadata)
        raise

# Global instances
_trading_logger = None
_performance_logger = None

def get_trading_logger() -> TradingEventLogger:
    """Get global trading event logger"""
    global _trading_logger
    if _trading_logger is None:
        _trading_logger = TradingEventLogger()
    return _trading_logger

def get_performance_logger() -> PerformanceLogger:
    """Get global performance logger"""
    global _performance_logger
    if _performance_logger is None:
        _performance_logger = PerformanceLogger()
    return _performance_logger