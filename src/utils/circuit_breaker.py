"""
Circuit Breaker Pattern Implementation

Provides automatic failure detection and recovery for external API calls,
preventing cascade failures and improving system resilience.
"""

import time
import functools
from typing import Callable, Any, Optional, Dict
from enum import Enum
from dataclasses import dataclass, field
from threading import Lock
import logging

from .logging_config import get_combined_logger

logger = get_combined_logger("mltrading.circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass


class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5           # Failures before opening
    recovery_timeout: float = 60.0      # Seconds before attempting recovery
    expected_exception: type = Exception  # Exception type to monitor
    success_threshold: int = 3           # Successes needed to close from half-open
    timeout: float = 30.0               # Call timeout in seconds


@dataclass


class CircuitBreakerStats:
    """Circuit breaker statistics"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    state_changes: int = 0
    total_calls: int = 0
    blocked_calls: int = 0


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance.

    Automatically opens when failure threshold is reached, preventing further
    calls to failing services. Attempts recovery after timeout period.

    Example:
        >>>  # Decorator usage
        >>> @CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        ... def fetch_external_data():
        ...     # API call that might fail
        ...     pass
        >>>
        >>>  # Manual usage
        >>> cb = CircuitBreaker("yahoo_api", failure_threshold=5)
        >>> with cb:
        ...     result = external_api_call()
    """

    _instances: Dict[str, 'CircuitBreaker'] = {}
    _lock = Lock()


    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = Lock()

        # Register instance for monitoring
        with CircuitBreaker._lock:
            CircuitBreaker._instances[name] = self

    @classmethod


    def get_instance(cls, name: str) -> 'CircuitBreaker':
        """Get existing circuit breaker instance by name"""
        with cls._lock:
            return cls._instances.get(name)

    @classmethod


    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        with cls._lock:
            return {
                name: {
                    'state': cb.state.value,
                    'failure_count': cb.stats.failure_count,
                    'success_count': cb.stats.success_count,
                    'total_calls': cb.stats.total_calls,
                    'blocked_calls': cb.stats.blocked_calls
                }
                for name, cb in cls._instances.items()
            }


    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset from open state"""
        if self.state != CircuitState.OPEN:
            return False

        if self.stats.last_failure_time is None:
            return True

        time_since_failure = time.time() - self.stats.last_failure_time
        return time_since_failure >= self.config.recovery_timeout


    def _record_success(self):
        """Record successful operation"""
        with self._lock:
            self.stats.success_count += 1
            self.stats.total_calls += 1

            if self.state == CircuitState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self.state == CircuitState.OPEN:
                # Shouldn't happen, but handle gracefully
                self._transition_to_half_open()


    def _record_failure(self, exception: Exception):
        """Record failed operation"""
        with self._lock:
            self.stats.failure_count += 1
            self.stats.total_calls += 1
            self.stats.last_failure_time = time.time()

            logger.warning(f"Circuit breaker {self.name} recorded failure: {exception}")

            if self.state == CircuitState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
            elif self.state == CircuitState.HALF_OPEN:
                self._transition_to_open()


    def _transition_to_open(self):
        """Transition circuit breaker to open state"""
        self.state = CircuitState.OPEN
        self.stats.state_changes += 1
        self.stats.success_count = 0  # Reset success counter
        logger.error(f"Circuit breaker {self.name} opened after {self.stats.failure_count} failures")


    def _transition_to_half_open(self):
        """Transition circuit breaker to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.stats.state_changes += 1
        self.stats.success_count = 0  # Reset success counter for testing
        logger.info(f"Circuit breaker {self.name} half-opened for recovery testing")


    def _transition_to_closed(self):
        """Transition circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.stats.state_changes += 1
        self.stats.failure_count = 0  # Reset failure counter
        logger.info(f"Circuit breaker {self.name} closed after {self.stats.success_count} successful calls")


    def __enter__(self):
        """Context manager entry"""
        return self.call


    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type and issubclass(exc_type, self.config.expected_exception):
            self._record_failure(exc_val)
            return False  # Don't suppress exception
        elif exc_type is None:
            self._record_success()
        return False


    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: When circuit is open
            Original exception: When function fails
        """
        with self._lock:
            self.stats.total_calls += 1

            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if not self._should_attempt_reset():
                    self.stats.blocked_calls += 1
                    raise CircuitBreakerError(f"Circuit breaker {self.name} is open")
                else:
                    self._transition_to_half_open()

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.config.expected_exception as e:
            self._record_failure(e)
            raise


    def force_open(self):
        """Manually open the circuit breaker"""
        with self._lock:
            self._transition_to_open()
            logger.warning(f"Circuit breaker {self.name} manually opened")


    def force_close(self):
        """Manually close the circuit breaker"""
        with self._lock:
            self._transition_to_closed()
            logger.info(f"Circuit breaker {self.name} manually closed")


    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.stats.failure_count,
            'success_count': self.stats.success_count,
            'total_calls': self.stats.total_calls,
            'blocked_calls': self.stats.blocked_calls,
            'state_changes': self.stats.state_changes,
            'last_failure_time': self.stats.last_failure_time
        }


def circuit_breaker(name: str = None, failure_threshold: int = 5,
                   recovery_timeout: float = 60.0, expected_exception: type = Exception):
    """
    Decorator for applying circuit breaker pattern to functions.

    Args:
        name: Circuit breaker name (defaults to function name)
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to monitor for failures

    Example:
        >>> @circuit_breaker(name="yahoo_api", failure_threshold=3, recovery_timeout=30)
        ... def fetch_yahoo_data(symbol):
        ...     # This function is now protected by circuit breaker
        ...     return yf.download(symbol)
        >>>
        >>>  # Circuit opens after 3 failures, blocks calls for 30 seconds
        >>> data = fetch_yahoo_data("AAPL")  # May raise CircuitBreakerError
    """


    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )
        breaker = CircuitBreaker(breaker_name, config)

        @functools.wraps(func)


        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        # Attach circuit breaker for monitoring
        wrapper._circuit_breaker = breaker
        return wrapper

    return decorator


def get_circuit_breaker_stats() -> Dict[str, Any]:
    """
    Get statistics for all circuit breakers in the system.

    Returns:
        Dictionary with circuit breaker statistics

    Example:
        >>> stats = get_circuit_breaker_stats()
        >>> for name, stat in stats.items():
        ...     print(f"{name}: {stat['state']} ({stat['total_calls']} calls)")
        yahoo_api: closed (1247 calls)
        database: closed (3891 calls)
    """
    return CircuitBreaker.get_all_stats()

