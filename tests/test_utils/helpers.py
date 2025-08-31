"""
Helper classes and functions for MLTrading tests.

Provides utility classes and methods to simplify test setup and execution.
"""

import time
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager
from unittest.mock import patch, Mock
import logging


class TestHelper:
    """General test helper utilities"""
    
    @staticmethod
    def suppress_logging(logger_names: List[str] = None):
        """Context manager to suppress logging during tests"""
        if logger_names is None:
            logger_names = ['src.dashboard', 'src.trading', 'src.utils']
        
        original_levels = {}
        for name in logger_names:
            logger = logging.getLogger(name)
            original_levels[name] = logger.level
            logger.setLevel(logging.CRITICAL)
        
        try:
            yield
        finally:
            for name, level in original_levels.items():
                logging.getLogger(name).setLevel(level)
    
    @staticmethod
    def wait_for_condition(condition_func, timeout=10, interval=0.1):
        """Wait for a condition to become true with timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        return False
    
    @staticmethod
    def assert_dataframe_equals(df1: pd.DataFrame, df2: pd.DataFrame, 
                              check_dtype=False, rtol=1e-5):
        """Enhanced DataFrame comparison with better error messages"""
        try:
            pd.testing.assert_frame_equal(df1, df2, check_dtype=check_dtype, rtol=rtol)
        except AssertionError as e:
            # Provide more helpful error information
            if df1.shape != df2.shape:
                raise AssertionError(f"DataFrame shapes differ: {df1.shape} != {df2.shape}")
            
            if not df1.columns.equals(df2.columns):
                raise AssertionError(f"Column names differ: {list(df1.columns)} != {list(df2.columns)}")
            
            # Find first differing value
            for col in df1.columns:
                if not df1[col].equals(df2[col]):
                    diff_mask = df1[col] != df2[col]
                    first_diff_idx = diff_mask.idxmax()
                    raise AssertionError(
                        f"First difference in column '{col}' at index {first_diff_idx}: "
                        f"{df1[col][first_diff_idx]} != {df2[col][first_diff_idx]}"
                    )
            
            raise e
    
    @staticmethod
    def generate_test_id(test_name: str, parameters: Dict[str, Any]) -> str:
        """Generate a unique test ID for parametrized tests"""
        param_str = "_".join(f"{k}={v}" for k, v in parameters.items())
        return f"{test_name}_{param_str}"


class DashTestHelper:
    """Helper utilities for Dash application testing"""
    
    def __init__(self, dash_duo):
        self.dash_duo = dash_duo
        self._app = None
    
    def start_app_once(self, app_module="src.dashboard.app"):
        """Start app only once per test session to improve performance"""
        if self._app is None:
            from dash.testing.application_runners import import_app
            self._app = import_app(app_module)
            self.dash_duo.start_server(self._app)
        return self._app
    
    def wait_for_element_with_retry(self, selector: str, timeout=10, retries=3):
        """Wait for element with retry logic for flaky elements"""
        for attempt in range(retries):
            try:
                self.dash_duo.wait_for_element(selector, timeout=timeout)
                return True
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(0.5)
        return False
    
    def safe_click(self, selector: str, retries=3):
        """Safely click element with retry for stale elements"""
        for attempt in range(retries):
            try:
                element = self.dash_duo.find_element(selector)
                element.click()
                return True
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(0.5)
        return False
    
    def get_text_with_retry(self, selector: str, retries=3):
        """Get text content with retry for stale elements"""
        for attempt in range(retries):
            try:
                element = self.dash_duo.find_element(selector)
                return element.text
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(0.5)
        return None
    
    def assert_no_console_errors(self, ignore_warnings=True):
        """Assert no console errors occurred"""
        logs = self.dash_duo.get_logs()
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if not ignore_warnings:
            errors.extend([log for log in logs if log['level'] == 'WARNING'])
        
        if errors:
            error_messages = [f"{log['level']}: {log['message']}" for log in errors]
            pytest.fail(f"Console errors detected:\n" + "\n".join(error_messages))
    
    @contextmanager
    def performance_timer(self, max_duration=None):
        """Context manager to measure performance"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if max_duration and duration > max_duration:
                pytest.fail(f"Operation took {duration:.2f}s, expected < {max_duration}s")


class DatabaseTestHelper:
    """Helper utilities for database testing"""
    
    @staticmethod
    def create_test_market_data(symbols: List[str], days: int = 30) -> pd.DataFrame:
        """Create realistic test market data"""
        data = []
        base_date = datetime(2023, 1, 1)
        
        for symbol in symbols:
            base_price = np.random.uniform(50, 200)
            
            for i in range(days):
                date = base_date + pd.Timedelta(days=i)
                
                # Generate realistic price movements
                price_change = np.random.normal(0, 0.02)  # 2% daily volatility
                base_price *= (1 + price_change)
                
                open_price = base_price * (1 + np.random.normal(0, 0.005))
                close_price = base_price
                high_price = max(open_price, close_price) * (1 + np.random.uniform(0, 0.01))
                low_price = min(open_price, close_price) * (1 - np.random.uniform(0, 0.01))
                volume = np.random.randint(1000000, 10000000)
                
                data.append({
                    'symbol': symbol,
                    'timestamp': date,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume
                })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def mock_database_query(return_data: Any = None, side_effect: Exception = None):
        """Create mock database query function"""
        def mock_query(*args, **kwargs):
            if side_effect:
                raise side_effect
            return return_data or []
        return mock_query
    
    @staticmethod
    def validate_database_schema(df: pd.DataFrame, expected_columns: List[str]):
        """Validate DataFrame matches expected database schema"""
        missing_columns = set(expected_columns) - set(df.columns)
        if missing_columns:
            raise AssertionError(f"Missing columns: {missing_columns}")
        
        # Check for reasonable data types
        if 'timestamp' in df.columns:
            assert pd.api.types.is_datetime64_any_dtype(df['timestamp'])
        
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                assert pd.api.types.is_numeric_dtype(df[col])


class AlertTestHelper:
    """Helper utilities for alert system testing"""
    
    @staticmethod
    def create_test_alert(title="Test Alert", severity="MEDIUM", category="SYSTEM_HEALTH", 
                         metadata=None):
        """Create a test alert object"""
        from src.utils.alerts.models import Alert, AlertSeverity, AlertCategory
        
        return Alert(
            title=title,
            message=f"Test message for {title}",
            severity=AlertSeverity(severity),
            category=AlertCategory(category.upper()),
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
    
    @staticmethod
    def mock_email_service(should_succeed=True):
        """Create mock email service"""
        mock_service = Mock()
        mock_service.is_available.return_value = should_succeed
        mock_service.send_alert.return_value = should_succeed
        mock_service.get_status.return_value = {
            'enabled': True,
            'available': should_succeed,
            'circuit_breaker_state': 'closed'
        }
        return mock_service
    
    @staticmethod
    def assert_alert_sent(alert_manager, expected_count=1):
        """Assert that alerts were sent successfully"""
        stats = alert_manager.get_stats()
        assert stats['sent_alerts'] >= expected_count, \
            f"Expected at least {expected_count} alerts sent, got {stats['sent_alerts']}"
    
    @staticmethod
    def reset_alert_stats(alert_manager):
        """Reset alert manager statistics for clean testing"""
        # Reset statistics if possible
        if hasattr(alert_manager, 'stats'):
            alert_manager.stats = {
                'total_alerts': 0,
                'sent_alerts': 0,
                'failed_alerts': 0,
                'rate_limited_alerts': 0,
                'filtered_alerts': 0,
                'alerts_by_severity': {},
                'alerts_by_category': {}
            }


class PerformanceTestHelper:
    """Helper utilities for performance testing"""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """Measure function execution time"""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
    
    @staticmethod
    def assert_performance_benchmark(func, max_time, *args, **kwargs):
        """Assert function executes within time benchmark"""
        result, execution_time = PerformanceTestHelper.measure_execution_time(func, *args, **kwargs)
        assert execution_time <= max_time, \
            f"Function took {execution_time:.3f}s, expected <= {max_time}s"
        return result
    
    @staticmethod
    def memory_usage_test(func, max_memory_mb=100):
        """Test memory usage of function (requires psutil)"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            result = func()
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            assert memory_used <= max_memory_mb, \
                f"Function used {memory_used:.1f}MB memory, expected <= {max_memory_mb}MB"
            
            return result, memory_used
        except ImportError:
            pytest.skip("psutil not available for memory testing")


# Global test configuration
class TestConfig:
    """Global test configuration settings"""
    
    # Performance thresholds
    DASH_APP_STARTUP_TIME = 10.0  # seconds
    DATABASE_QUERY_TIME = 2.0     # seconds
    CHART_RENDER_TIME = 5.0       # seconds
    
    # Test data sizes
    SMALL_DATASET_SIZE = 100
    MEDIUM_DATASET_SIZE = 1000
    LARGE_DATASET_SIZE = 10000
    
    # Retry settings
    DEFAULT_RETRIES = 3
    ELEMENT_WAIT_TIMEOUT = 10
    
    # Mock settings
    MOCK_RESPONSE_DELAY = 0.1  # seconds