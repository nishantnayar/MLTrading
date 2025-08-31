"""
Test performance monitoring and benchmarking suite.

This module provides tools to monitor test performance and detect regressions
in test execution time and resource usage.
"""

import pytest
import json
import time
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from test_utils.helpers import PerformanceTestHelper, TestConfig


@dataclass
class TestMetrics:
    """Test execution metrics"""
    test_name: str
    execution_time: float
    memory_usage_mb: Optional[float]
    status: str
    timestamp: str
    metadata: Dict[str, Any]


class PerformanceMonitor:
    """Monitor and track test performance over time"""
    
    def __init__(self, results_file: str = "tests/performance_results.json"):
        self.results_file = Path(results_file)
        self.results_file.parent.mkdir(exist_ok=True)
        self.current_session_results = []
        
    def record_test_result(self, test_name: str, execution_time: float, 
                          memory_usage: Optional[float] = None, 
                          status: str = "passed", **metadata):
        """Record test execution metrics"""
        metrics = TestMetrics(
            test_name=test_name,
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata
        )
        
        self.current_session_results.append(metrics)
    
    def save_session_results(self):
        """Save current session results to file"""
        # Load existing results
        existing_results = []
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r') as f:
                    existing_results = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_results = []
        
        # Add current session results
        new_results = [asdict(metric) for metric in self.current_session_results]
        existing_results.extend(new_results)
        
        # Keep only last 1000 results to avoid file bloat
        if len(existing_results) > 1000:
            existing_results = existing_results[-1000:]
        
        # Save updated results
        with open(self.results_file, 'w') as f:
            json.dump(existing_results, f, indent=2)
    
    def get_performance_history(self, test_name: str, limit: int = 10) -> List[Dict]:
        """Get performance history for a specific test"""
        if not self.results_file.exists():
            return []
        
        try:
            with open(self.results_file, 'r') as f:
                all_results = json.load(f)
            
            # Filter by test name and sort by timestamp
            test_results = [
                result for result in all_results 
                if result['test_name'] == test_name
            ]
            
            # Sort by timestamp (newest first)
            test_results.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return test_results[:limit]
            
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def detect_performance_regression(self, test_name: str, current_time: float, 
                                    threshold_factor: float = 1.5) -> bool:
        """Detect if current execution time indicates a performance regression"""
        history = self.get_performance_history(test_name, limit=5)
        
        if len(history) < 3:
            return False  # Need sufficient history
        
        # Calculate average of recent executions (excluding current)
        recent_times = [result['execution_time'] for result in history]
        avg_time = sum(recent_times) / len(recent_times)
        
        # Check if current time is significantly higher
        return current_time > (avg_time * threshold_factor)
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.results_file.exists():
            return {"error": "No performance data available"}
        
        try:
            with open(self.results_file, 'r') as f:
                all_results = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"error": "Could not load performance data"}
        
        # Analyze results
        test_stats = {}
        for result in all_results:
            test_name = result['test_name']
            if test_name not in test_stats:
                test_stats[test_name] = {
                    'execution_times': [],
                    'memory_usage': [],
                    'run_count': 0,
                    'failure_count': 0
                }
            
            test_stats[test_name]['execution_times'].append(result['execution_time'])
            if result.get('memory_usage_mb'):
                test_stats[test_name]['memory_usage'].append(result['memory_usage_mb'])
            
            test_stats[test_name]['run_count'] += 1
            if result['status'] != 'passed':
                test_stats[test_name]['failure_count'] += 1
        
        # Calculate statistics
        report = {
            'total_tests': len(test_stats),
            'total_runs': sum(stats['run_count'] for stats in test_stats.values()),
            'test_performance': {}
        }
        
        for test_name, stats in test_stats.items():
            times = stats['execution_times']
            report['test_performance'][test_name] = {
                'run_count': stats['run_count'],
                'failure_rate': stats['failure_count'] / stats['run_count'],
                'avg_execution_time': sum(times) / len(times),
                'min_execution_time': min(times),
                'max_execution_time': max(times),
                'avg_memory_usage': sum(stats['memory_usage']) / len(stats['memory_usage']) 
                                  if stats['memory_usage'] else None
            }
        
        return report


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


@pytest.fixture(autouse=True)
def monitor_test_performance(request):
    """Automatically monitor test performance"""
    test_name = f"{request.module.__name__}::{request.function.__name__}"
    
    start_time = time.time()
    memory_before = None
    
    # Get memory usage if psutil is available
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
    except ImportError:
        pass
    
    yield
    
    # Calculate metrics
    execution_time = time.time() - start_time
    memory_usage = None
    
    if memory_before is not None:
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = memory_after - memory_before
        except ImportError:
            pass
    
    # Record results
    performance_monitor.record_test_result(
        test_name=test_name,
        execution_time=execution_time,
        memory_usage=memory_usage,
        status="passed" if request.node.rep_outcome.outcome == "passed" else "failed",
        test_file=request.module.__file__,
        node_id=request.node.nodeid
    )
    
    # Check for performance regression
    if execution_time > 1.0:  # Only check for tests that take > 1 second
        is_regression = performance_monitor.detect_performance_regression(
            test_name, execution_time
        )
        
        if is_regression:
            pytest.warn(
                f"Performance regression detected for {test_name}: "
                f"{execution_time:.2f}s (above historical average)"
            )


@pytest.fixture(scope="session", autouse=True)
def save_performance_results(request):
    """Save performance results at end of test session"""
    yield
    performance_monitor.save_session_results()


# Performance test benchmarks
@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Benchmark tests for performance monitoring"""
    
    def test_dashboard_load_benchmark(self, app, dash_duo):
        """Benchmark dashboard loading time"""
        def load_dashboard():
            dash_duo.start_server(app)
            dash_duo.wait_for_element("#page-content", timeout=30)
            return True
        
        result = PerformanceTestHelper.assert_performance_benchmark(
            load_dashboard,
            max_time=TestConfig.DASH_APP_STARTUP_TIME
        )
        assert result
    
    def test_data_processing_benchmark(self, large_market_dataset):
        """Benchmark data processing performance"""
        def process_data():
            # Simulate typical data processing operations
            result = large_market_dataset.groupby('symbol').agg({
                'volume': ['mean', 'sum'],
                'close': ['min', 'max', 'std']
            })
            return len(result)
        
        result = PerformanceTestHelper.assert_performance_benchmark(
            process_data,
            max_time=2.0  # Should complete in 2 seconds
        )
        assert result > 0
    
    def test_database_query_benchmark(self, mock_database_connection):
        """Benchmark database query performance"""
        def execute_queries():
            # Simulate multiple database queries
            for i in range(100):
                with mock_database_connection as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT * FROM market_data LIMIT 1000")
                        cursor.fetchall()
            return True
        
        result = PerformanceTestHelper.assert_performance_benchmark(
            execute_queries,
            max_time=TestConfig.DATABASE_QUERY_TIME
        )
        assert result
    
    @pytest.mark.slow
    def test_memory_usage_benchmark(self, performance_config):
        """Benchmark memory usage during intensive operations"""
        def memory_intensive_operation():
            # Create large datasets to test memory handling
            import pandas as pd
            import numpy as np
            
            # Generate multiple large DataFrames
            dataframes = []
            for i in range(10):
                df = pd.DataFrame({
                    'data': np.random.rand(10000),
                    'category': np.random.choice(['A', 'B', 'C'], 10000)
                })
                dataframes.append(df)
            
            # Perform operations that could use significant memory
            combined = pd.concat(dataframes)
            result = combined.groupby('category').agg(['mean', 'std', 'count'])
            
            return len(result)
        
        try:
            result, memory_used = PerformanceTestHelper.memory_usage_test(
                memory_intensive_operation,
                max_memory_mb=200  # Allow up to 200MB
            )
            assert result > 0
            assert memory_used < 200
        except ImportError:
            pytest.skip("Memory testing requires psutil")


def test_performance_monitor_functionality():
    """Test the performance monitoring system itself"""
    monitor = PerformanceMonitor("tests/test_monitor.json")
    
    # Record some test results
    monitor.record_test_result("test_example", 1.5, memory_usage=50.0, status="passed")
    monitor.record_test_result("test_example", 1.7, memory_usage=55.0, status="passed")
    monitor.record_test_result("test_example", 3.0, memory_usage=80.0, status="passed")
    
    # Test regression detection
    is_regression = monitor.detect_performance_regression("test_example", 4.0)
    assert is_regression  # 4.0s should be flagged as regression
    
    is_normal = monitor.detect_performance_regression("test_example", 1.6)
    assert not is_normal  # 1.6s should be normal
    
    # Test performance history
    history = monitor.get_performance_history("test_example")
    assert len(history) == 0  # No saved results yet
    
    # Save and load
    monitor.save_session_results()
    history = monitor.get_performance_history("test_example", limit=2)
    assert len(history) == 2
    
    # Clean up test file
    test_file = Path("tests/test_monitor.json")
    if test_file.exists():
        test_file.unlink()


# Hook to capture test outcomes for performance monitoring
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test outcomes"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
    
    # Store outcome for performance monitoring
    if rep.when == "call":
        setattr(item, "rep_outcome", rep)