"""
Retry Decorators for Enhanced Error Handling

Provides configurable retry logic with exponential backoff, jitter,
and integration with circuit breakers for robust external API calls.
"""

import time
import random
import functools
from typing import Callable, Type, Tuple, Optional, Union, Any
import logging

from .logging_config import get_combined_logger
from .circuit_breaker import CircuitBreakerError

logger = get_combined_logger("mltrading.retry")


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0,
                        jitter: bool = True) -> float:
    """
    Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter

    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (2 ** attempt), max_delay)

    if jitter:
        # Add ±25% jitter to prevent thundering herd
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)

    return max(delay, 0)


def retry(max_attempts: int = 3,
          delay: float = 1.0,
          max_delay: float = 60.0,
          backoff_multiplier: float = 2.0,
          jitter: bool = True,
          exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
          on_retry: Optional[Callable[[Exception, int], None]] = None):
    """
    Retry decorator with exponential backoff and configurable exception handling.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_multiplier: Multiplier for exponential backoff
        jitter: Whether to add random jitter to delays
        exceptions: Exception type(s) to retry on
        on_retry: Optional callback function called on each retry

    Example:
        >>> @retry(max_attempts=3, delay=1.0, exceptions=ConnectionError)
        ... def fetch_data_from_api():
        ...     # This function will retry up to 3 times on ConnectionError
        ...     return requests.get("https://api.example.com/data")
        >>>
        >>> @retry(max_attempts=5, delay=0.5, backoff_multiplier=1.5)
        ... def database_operation():
        ...     # Retries with 0.5s, 0.75s, 1.125s, 1.69s delays
        ...     return db.execute_query("SELECT * FROM table")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except CircuitBreakerError:
                    # Don't retry circuit breaker errors
                    raise

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise

                    # Calculate delay for next attempt
                    if backoff_multiplier == 1.0:
                        # Linear backoff
                        sleep_time = delay
                    else:
                        # Exponential backoff
                        sleep_time = min(delay * (backoff_multiplier ** attempt), max_delay)

                    if jitter:
                        # Add ±25% jitter
                        jitter_range = sleep_time * 0.25
                        sleep_time += random.uniform(-jitter_range, jitter_range)

                    sleep_time = max(sleep_time, 0)

                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                                   f"Retrying in {sleep_time:.2f}s...")

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, attempt + 1)
                        except Exception as callback_error:
                            logger.warning(f"Retry callback failed: {callback_error}")

                    time.sleep(sleep_time)

            # Should never reach here, but just in case
            raise last_exception

        return wrapper

    return decorator


def retry_with_circuit_breaker(circuit_breaker_name: str,
                               max_attempts: int = 3,
                               delay: float = 1.0,
                               exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception):
    """
    Combined retry and circuit breaker decorator.

    Args:
        circuit_breaker_name: Name of circuit breaker to use
        max_attempts: Maximum retry attempts
        delay: Initial delay between retries
        exceptions: Exception types to retry on

    Example:
        >>> @retry_with_circuit_breaker("yahoo_api", max_attempts=3, delay=2.0)
        ... def fetch_yahoo_data(symbol):
        ...     # Protected by both retry logic and circuit breaker
        ...     return yf.download(symbol)
    """

    def decorator(func: Callable) -> Callable:
        # Import here to avoid circular imports
        from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig

        # Create or get circuit breaker
        cb_config = CircuitBreakerConfig(expected_exception=exceptions)
        circuit_breaker = CircuitBreaker(circuit_breaker_name, cb_config)

        @retry(max_attempts=max_attempts, delay=delay, exceptions=exceptions)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return circuit_breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


class RetryableOperation:
    """
    Context manager for retryable operations with fine-grained control.

    Example:
        >>> op = RetryableOperation(max_attempts=3, delay=1.0)
        >>> for attempt in op:
        ...     try:
        ...         result = risky_operation()
        ...         op.success(result)
        ...         break
        ...     except Exception as e:
        ...         if not op.should_retry(e):
        ...             raise
        ...         print(f"Attempt {attempt} failed, retrying...")
    """

    def __init__(self, max_attempts: int = 3, delay: float = 1.0,
                 max_delay: float = 60.0, jitter: bool = True):
        self.max_attempts = max_attempts
        self.delay = delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.current_attempt = 0
        self.last_exception = None
        self.result = None
        self.succeeded = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.current_attempt >= self.max_attempts or self.succeeded:
            raise StopIteration

        attempt = self.current_attempt
        self.current_attempt += 1

        # Add delay before retry (except first attempt)
        if attempt > 0:
            sleep_time = exponential_backoff(attempt - 1, self.delay, self.max_delay, self.jitter)
            logger.info(f"Retrying operation in {sleep_time:.2f}s (attempt {attempt + 1}/{self.max_attempts})")
            time.sleep(sleep_time)

        return attempt

    def success(self, result: Any = None):
        """Mark operation as successful"""
        self.succeeded = True
        self.result = result
        logger.info(f"Operation succeeded on attempt {self.current_attempt}")

    def should_retry(self, exception: Exception) -> bool:
        """Check if operation should be retried"""
        self.last_exception = exception

        # Don't retry circuit breaker errors
        if isinstance(exception, CircuitBreakerError):
            return False

        # Continue retrying if we have attempts left
        return self.current_attempt < self.max_attempts


# Convenience retry decorators for common scenarios


def retry_on_connection_error(max_attempts: int = 3, delay: float = 2.0):
    """Retry decorator specifically for connection errors"""
    return retry(
        max_attempts=max_attempts,
        delay=delay,
        exceptions=(ConnectionError, OSError, TimeoutError)
    )


def retry_on_api_error(max_attempts: int = 5, delay: float = 1.0):
    """Retry decorator for API-related errors"""
    import requests
    return retry(
        max_attempts=max_attempts,
        delay=delay,
        exceptions=(requests.RequestException, ConnectionError, TimeoutError)
    )


def retry_on_database_error(max_attempts: int = 3, delay: float = 0.5):
    """Retry decorator for database-related errors"""
    import psycopg2
    return retry(
        max_attempts=max_attempts,
        delay=delay,
        exceptions=(psycopg2.OperationalError, psycopg2.InterfaceError)
    )
