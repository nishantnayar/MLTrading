"""
Resilient Database Logging System
Implements connection pool-aware logging with circuit breaker and graceful degradation
"""

import logging
import json
import threading
import time
import traceback
from typing import Dict, Any, Optional, List
from queue import Queue, Empty
from contextlib import contextmanager
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from ..data.storage.database import DatabaseManager
from .logging_config import get_correlation_id, sanitize_log_message


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, blocking database writes
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerStats:
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state: CircuitState = CircuitState.CLOSED


class DatabaseCircuitBreaker:
    """Circuit breaker for database operations to prevent pool exhaustion"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.stats = CircuitBreakerStats()
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        """Check if database operation can proceed"""
        with self._lock:
            if self.stats.state == CircuitState.CLOSED:
                return True
            elif self.stats.state == CircuitState.OPEN:
                # Check if we should try to recover
                if (time.time() - self.stats.last_failure_time) > self.recovery_timeout:
                    self.stats.state = CircuitState.HALF_OPEN
                    return True
                return False
            else:  # HALF_OPEN
                return True

    def record_success(self):
        """Record successful database operation"""
        with self._lock:
            self.stats.success_count += 1
            self.stats.last_success_time = time.time()

            if self.stats.state == CircuitState.HALF_OPEN:
                # Recovery successful, close circuit
                self.stats.state = CircuitState.CLOSED
                self.stats.failure_count = 0

    def record_failure(self):
        """Record failed database operation"""
        with self._lock:
            self.stats.failure_count += 1
            self.stats.last_failure_time = time.time()

            if self.stats.failure_count >= self.failure_threshold:
                self.stats.state = CircuitState.OPEN

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self._lock:
            return {
                'state': self.stats.state.value,
                'failure_count': self.stats.failure_count,
                'success_count': self.stats.success_count,
                'last_failure': self.stats.last_failure_time,
                'last_success': self.stats.last_success_time
            }


class ResilientDatabaseLogger:
    """
    Database logger with connection pool protection and graceful degradation
    """

    def __init__(self, table_name: str, batch_size: int = 100,
                 flush_interval: float = 10.0, max_queue_size: int = 5000):
        self.table_name = table_name
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_queue_size = max_queue_size

        # Queue for pending log entries
        self.log_queue = Queue(maxsize=max_queue_size)

        # Circuit breaker for database operations
        self.circuit_breaker = DatabaseCircuitBreaker()

        # Statistics
        self.stats = {
            'logs_queued': 0,
            'logs_written_to_db': 0,
            'logs_dropped': 0,
            'database_errors': 0,
            'last_flush': None
        }

        # Background thread for database writes
        self.shutdown_event = threading.Event()
        self.writer_thread = threading.Thread(target=self._database_writer, daemon=True)
        self.writer_thread.start()

        # Dedicated database connection for logging
        self._db_connection = None
        self._connection_lock = threading.Lock()

    def _get_dedicated_connection(self):
        """Get or create dedicated database connection for logging"""
        with self._connection_lock:
            if self._db_connection is None or self._db_connection.closed:
                try:
                    # Create a single dedicated connection for logging
                    self._db_connection = DatabaseManager().get_connection()
                    # Set autocommit for logging operations
                    self._db_connection.autocommit = True
                except Exception as e:
                    self.circuit_breaker.record_failure()
                    raise e
            return self._db_connection

    def log_async(self, data: Dict[str, Any]):
        """Add log entry to queue for asynchronous processing"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now(tz=timezone.utc)

            # Try to add to queue (non-blocking)
            self.log_queue.put_nowait(data)
            self.stats['logs_queued'] += 1

        except Exception:
            # Queue is full, drop the log
            self.stats['logs_dropped'] += 1

    def _database_writer(self):
        """Background thread that writes logs to database in batches"""
        batch = []
        last_flush = time.time()

        while not self.shutdown_event.is_set():
            try:
                # Collect logs into batch
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

                    if self.circuit_breaker.can_execute():
                        self._write_batch_to_database(batch)
                    else:
                        # Circuit is open, drop the batch and log to fallback
                        self._write_batch_to_fallback(batch)

                    batch.clear()
                    last_flush = time.time()
                    self.stats['last_flush'] = datetime.now()

            except Exception as e:
                # Clear batch to avoid infinite error loop
                batch.clear()
                self.stats['database_errors'] += 1
                time.sleep(1)  # Brief pause before retrying

    def _write_batch_to_database(self, batch: List[Dict[str, Any]]):
        """Write batch to database with circuit breaker protection"""
        if not batch:
            return

        try:
            conn = self._get_dedicated_connection()
            with conn.cursor() as cursor:
                # Prepare SQL based on table type
                sql = self._get_insert_sql()

                # Execute batch insert
                cursor.executemany(sql, batch)

                # Record success
                self.circuit_breaker.record_success()
                self.stats['logs_written_to_db'] += len(batch)

        except Exception as e:
            # Record failure and write to fallback
            self.circuit_breaker.record_failure()
            self.stats['database_errors'] += 1
            self._write_batch_to_fallback(batch)

            # Close bad connection
            if self._db_connection:
                try:
                    self._db_connection.close()
                except Exception:
                    pass
                self._db_connection = None

    def _write_batch_to_fallback(self, batch: List[Dict[str, Any]]):
        """Write batch to fallback file when database is unavailable"""
        try:
            fallback_logger = logging.getLogger(f'database_fallback_{self.table_name}')
            if not fallback_logger.handlers:
                # Set up file handler for fallback
                handler = logging.FileHandler(f'logs/database_fallback_{self.table_name}.log')
                handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
                fallback_logger.addHandler(handler)
                fallback_logger.setLevel(logging.INFO)

            for entry in batch:
                fallback_logger.info(f"FALLBACK_LOG: {json.dumps(entry, default=str)}")

        except Exception as e:
            # Last resort: drop the logs silently
            self.stats['logs_dropped'] += len(batch)

    def _get_insert_sql(self) -> str:
        """Get SQL insert statement based on table name"""
        if self.table_name == 'data_collection_logs':
            return """
                INSERT INTO data_collection_logs
                (timestamp, operation_type, data_source, symbol, records_processed,
                 duration_ms, status, correlation_id, metadata)
                VALUES (%(timestamp)s, %(operation_type)s, %(data_source)s, %(symbol)s,
                        %(records_processed)s, %(duration_ms)s, %(status)s, %(correlation_id)s, %(metadata)s)
            """
        elif self.table_name == 'error_logs':
            return """
                INSERT INTO error_logs
                (timestamp, error_type, error_message, component, severity, stack_trace,
                 source_file, source_line, source_function, user_impact, correlation_id,
                 first_occurrence, occurrence_count, resolution_status, metadata)
                VALUES (%(timestamp)s, %(error_type)s, %(error_message)s, %(component)s,
                        %(severity)s, %(stack_trace)s, %(source_file)s, %(source_line)s,
                        %(source_function)s, %(user_impact)s, %(correlation_id)s,
                        %(first_occurrence)s, %(occurrence_count)s, %(resolution_status)s, %(metadata)s)
            """
        elif self.table_name == 'performance_logs':
            return """
                INSERT INTO performance_logs
                (timestamp, operation_name, duration_ms, status, component,
                 correlation_id, memory_usage_mb, cpu_usage_percent, metadata)
                VALUES (%(timestamp)s, %(operation_name)s, %(duration_ms)s, %(status)s, %(component)s,
                        %(correlation_id)s, %(memory_usage_mb)s, %(cpu_usage_percent)s, %(metadata)s)
            """
        else:
            return """
                INSERT INTO system_logs
                (timestamp, level, logger_name, correlation_id, message,
                 module, function_name, line_number, thread_name, process_id, metadata)
                VALUES (%(timestamp)s, %(level)s, %(logger_name)s, %(correlation_id)s, %(message)s,
                        %(module)s, %(function_name)s, %(line_number)s, %(thread_name)s, %(process_id)s, %(metadata)s)
            """


    def flush(self):
        """Force flush pending logs"""
        start_time = time.time()
        while not self.log_queue.empty() and time.time() - start_time < 5:
            time.sleep(0.1)


    def close(self):
        """Shutdown the logger"""
        self.shutdown_event.set()
        self.flush()

        if self.writer_thread.is_alive():
            self.writer_thread.join(timeout=10)

        if self._db_connection:
            try:
                self._db_connection.close()
            except Exception:
                pass


    def get_stats(self) -> Dict[str, Any]:
        """Get logger statistics"""
        return {
            **self.stats,
            'queue_size': self.log_queue.qsize(),
            'circuit_breaker': self.circuit_breaker.get_stats(),
            'thread_alive': self.writer_thread.is_alive()
        }


class ResilientDataCollectionLogger:
    """Resilient data collection logger with circuit breaker protection"""


    def __init__(self):
        self.logger = ResilientDatabaseLogger('data_collection_logs', batch_size=50, flush_interval=5.0)


    def log_data_collection(self, operation_type: str, data_source: str,
                           symbol: str = None, records_processed: int = None,
                           duration_ms: float = None, status: str = 'success',
                           **metadata):
        """Log data collection event asynchronously"""
        try:
            correlation_id = get_correlation_id()

            data = {
                'timestamp': datetime.now(tz=timezone.utc),
                'operation_type': operation_type,
                'data_source': data_source,
                'symbol': symbol,
                'records_processed': records_processed or 0,
                'duration_ms': duration_ms,
                'status': status,
                'correlation_id': correlation_id,
                'metadata': json.dumps(metadata) if metadata else None
            }

            # Queue for async processing
            self.logger.log_async(data)

        except Exception:
            # Fail silently to avoid disrupting main operations
            pass


class ResilientErrorLogger:
    """Resilient error logger with circuit breaker protection"""


    def __init__(self):
        self.logger = ResilientDatabaseLogger('error_logs', batch_size=25, flush_interval=3.0)


    def log_error(self, error_type: str, error_message: str, component: str = None,
                  severity: str = 'MEDIUM', stack_trace: str = None,
                  source_file: str = None, source_line: int = None,
                  source_function: str = None, user_impact: bool = False, **metadata):
        """Log error event asynchronously"""
        try:
            correlation_id = get_correlation_id()

            data = {
                'timestamp': datetime.now(tz=timezone.utc),
                'error_type': error_type,
                'error_message': error_message,
                'component': component,
                'severity': severity,
                'stack_trace': stack_trace,
                'source_file': source_file,
                'source_line': source_line,
                'source_function': source_function,
                'user_impact': user_impact,
                'correlation_id': correlation_id,
                'first_occurrence': datetime.now(tz=timezone.utc),
                'occurrence_count': 1,
                'resolution_status': 'open',
                'metadata': json.dumps(metadata) if metadata else None
            }

            # Queue for async processing
            self.logger.log_async(data)

        except Exception:
            # Fail silently to avoid disrupting main operations
            pass


class ResilientPerformanceLogger:
    """Resilient performance logger with circuit breaker protection"""


    def __init__(self):
        self.logger = ResilientDatabaseLogger('performance_logs', batch_size=75, flush_interval=8.0)


    def log_performance(self, operation_name: str, duration_ms: float,
                       status: str = 'success', component: str = None, **metadata):
        """Log performance metrics asynchronously"""
        try:
            correlation_id = get_correlation_id()

            data = {
                'timestamp': datetime.now(tz=timezone.utc),
                'operation_name': operation_name,
                'duration_ms': duration_ms,
                'status': status,
                'component': component or 'unknown',
                'correlation_id': correlation_id,
                'memory_usage_mb': None,  # Could add psutil metrics if needed
                'cpu_usage_percent': None,
                'metadata': json.dumps(metadata) if metadata else None
            }

            # Queue for async processing
            self.logger.log_async(data)

        except Exception:
            # Fail silently to avoid disrupting main operations
            pass


# Global resilient logger instances
_resilient_data_logger = None
_resilient_error_logger = None
_resilient_performance_logger = None


def get_resilient_data_collection_logger() -> ResilientDataCollectionLogger:
    """Get global resilient data collection logger"""
    global _resilient_data_logger
    if _resilient_data_logger is None:
        _resilient_data_logger = ResilientDataCollectionLogger()
    return _resilient_data_logger


def get_resilient_error_logger() -> ResilientErrorLogger:
    """Get global resilient error logger"""
    global _resilient_error_logger
    if _resilient_error_logger is None:
        _resilient_error_logger = ResilientErrorLogger()
    return _resilient_error_logger


def get_resilient_performance_logger() -> ResilientPerformanceLogger:
    """Get global resilient performance logger"""
    global _resilient_performance_logger
    if _resilient_performance_logger is None:
        _resilient_performance_logger = ResilientPerformanceLogger()
    return _resilient_performance_logger


def get_all_logger_stats() -> Dict[str, Any]:
    """Get statistics from all resilient loggers"""
    stats = {}

    if _resilient_data_logger:
        stats['data_collection'] = _resilient_data_logger.logger.get_stats()

    if _resilient_error_logger:
        stats['error'] = _resilient_error_logger.logger.get_stats()

    if _resilient_performance_logger:
        stats['performance'] = _resilient_performance_logger.logger.get_stats()

    return stats


def cleanup_resilient_loggers():
    """Cleanup all resilient loggers"""
    global _resilient_data_logger, _resilient_error_logger, _resilient_performance_logger

    if _resilient_data_logger:
        _resilient_data_logger.logger.close()
        _resilient_data_logger = None

    if _resilient_error_logger:
        _resilient_error_logger.logger.close()
        _resilient_error_logger = None

    if _resilient_performance_logger:
        _resilient_performance_logger.logger.close()
        _resilient_performance_logger = None


@contextmanager


def resilient_log_performance(operation_name: str, component: str = None, **metadata):
    """Context manager for resilient performance logging"""
    perf_logger = get_resilient_performance_logger()
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
