# MLTrading Test Suite

This document provides a comprehensive guide to the optimized MLTrading test suite, including performance monitoring, shared utilities, and best practices.

## Test Structure

```
tests/
├── README.md                    # This file
├── conftest.py                  # Global pytest configuration
├── pytest.ini                  # Pytest settings (in project root)
├── alerts/                      # Alert system tests
│   ├── __init__.py
│   ├── test_alert_system.py
│   ├── test_email_alert.py
│   └── test_prefect_alerts.py
├── integration/                 # Integration tests
│   ├── __init__.py
│   └── test_api_integration.py
├── performance/                 # Performance tests and monitoring
│   ├── __init__.py
│   └── test_performance_monitor.py
├── regression/                  # Regression tests
│   ├── __init__.py
│   ├── test_callback_regression.py
│   └── test_dashboard_regression.py
├── unit/                        # Unit tests
│   ├── __init__.py
│   ├── dashboard/
│   ├── indicators/
│   ├── test_alpaca_service.py
│   ├── test_api_error_handling.py
│   ├── test_dashboard_app.py
│   ├── test_dashboard_callbacks.py
│   ├── test_dashboard_layouts.py
│   ├── test_dashboard_services.py
│   ├── test_market_hours_integration.py
│   └── test_trading_callbacks.py
├── test_utils/                  # Shared testing utilities
│   ├── __init__.py
│   ├── fixtures.py             # Common fixtures
│   ├── helpers.py              # Test helper classes
│   ├── data_generators.py      # Mock data generation
│   └── mocks.py                # Mock services
├── optimized_examples/          # Best practice examples
│   └── test_optimized_dashboard.py
├── fixtures/                    # Legacy fixtures (deprecated)
└── performance_results.json    # Test performance history
```

## Quick Start

### Running Tests

```bash
# Run all tests
pytest

# Run only fast tests (skip slow integration tests)
pytest --fast

# Run performance tests with benchmarking
pytest --performance

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Exclude slow tests

# Run tests from specific subfolders
pytest tests/unit/           # All unit tests
pytest tests/integration/   # All integration tests
pytest tests/alerts/         # All alert system tests
pytest tests/regression/     # All regression tests
pytest tests/performance/    # All performance tests

# Run specific test files
pytest tests/alerts/test_email_alert.py
pytest tests/unit/test_dashboard_app.py
```

### Performance Monitoring

The test suite automatically monitors test performance and detects regressions:

- **Execution time tracking**: All tests are automatically timed
- **Memory usage monitoring**: Tracks memory consumption (requires `psutil`)
- **Performance regression detection**: Alerts when tests become significantly slower
- **Historical tracking**: Maintains performance history in `performance_results.json`

## Using Test Utilities

### Shared Fixtures

Import optimized fixtures from `test_utils.fixtures`:

```python
from test_utils.fixtures import (
    sample_market_data,
    mock_data_service,
    large_market_dataset,
    technical_indicator_data
)

def test_example(sample_market_data, mock_data_service):
    # Use shared, optimized fixtures
    data = mock_data_service.get_market_data("AAPL")
    assert not data.empty
```

### Test Helpers

Use helper classes for reliable test operations:

```python
from test_utils.helpers import DashTestHelper, PerformanceTestHelper

def test_dashboard_interaction(started_app):
    helper = DashTestHelper(started_app)
    
    # Reliable element interaction
    helper.wait_for_element_with_retry("#nav-trading")
    helper.safe_click("#nav-trading")
    helper.assert_no_console_errors()

def test_performance_benchmark():
    def expensive_operation():
        # Your code here
        return result
    
    # Performance testing
    result = PerformanceTestHelper.assert_performance_benchmark(
        expensive_operation,
        max_time=2.0
    )
```

### Data Generators

Generate consistent test data:

```python
from test_utils.data_generators import MarketDataGenerator

def test_with_generated_data():
    generator = MarketDataGenerator(seed=42)  # Reproducible
    data = generator.generate_ohlcv_data("AAPL", periods=100)
    
    # Test with generated data
    assert len(data) == 100
    assert "close" in data.columns
```

### Mock Services

Use comprehensive mocks for external dependencies:

```python
from test_utils.mocks import MockedServices

def test_with_mocked_services():
    with MockedServices(mock_database=True, mock_alpaca=True):
        # All external services are mocked
        # Your test code here
        pass
```

## Performance Optimization Best Practices

### 1. Use Appropriate Fixture Scopes

```python
# Session scope - expensive setup once per test session
@pytest.fixture(scope="session")
def expensive_resource():
    return create_expensive_resource()

# Class scope - shared within test class
@pytest.fixture(scope="class")
def class_resource():
    return create_class_resource()

# Function scope (default) - fresh for each test
@pytest.fixture
def fresh_resource():
    return create_fresh_resource()
```

### 2. Optimize Dash Application Testing

```python
# BAD: Multiple app startups
def test_navigation_bad(app, dash_duo):
    dash_duo.start_server(app)  # Expensive startup
    # test code

def test_charts_bad(app, dash_duo):
    dash_duo.start_server(app)  # Another expensive startup
    # test code

# GOOD: Shared app startup
@pytest.fixture(scope="class")
def started_app(app, dash_duo):
    dash_duo.start_server(app)  # Start once
    dash_duo.wait_for_element("#page-content")
    yield dash_duo

class TestDashboard:
    def test_navigation(self, started_app):
        # Use already started app
        
    def test_charts(self, started_app):
        # Reuse same app instance
```

### 3. Use Performance Helpers

```python
# Measure execution time
result, time_taken = PerformanceTestHelper.measure_execution_time(my_function)

# Performance benchmarking
PerformanceTestHelper.assert_performance_benchmark(
    my_function,
    max_time=1.0
)

# Memory usage testing
result, memory_used = PerformanceTestHelper.memory_usage_test(
    memory_intensive_function,
    max_memory_mb=100
)
```

### 4. Suppress Unnecessary Logging

```python
def test_with_suppressed_logging(suppressed_logging):
    # Logging is automatically suppressed
    # Test runs faster and cleaner
    pass
```

## Performance Monitoring

### Automatic Monitoring

All tests are automatically monitored for:
- Execution time
- Memory usage (if `psutil` installed)
- Performance regressions

### Performance Reports

Generate performance reports:

```python
from test_performance_monitor import performance_monitor

# Get performance history for a specific test
history = performance_monitor.get_performance_history("test_example")

# Generate comprehensive report
report = performance_monitor.generate_performance_report()
```

### Regression Detection

Tests that take longer than 1 second are automatically checked for performance regressions. If a test becomes 50% slower than its recent average, a warning is issued.

## Test Categories and Markers

### Markers

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, external deps)
- `@pytest.mark.performance` - Performance benchmarks
- `@pytest.mark.slow` - Slow tests (can be skipped with `--fast`)
- `@pytest.mark.regression` - Regression tests

### Example Usage

```python
@pytest.mark.unit
def test_calculation():
    # Fast unit test
    pass

@pytest.mark.integration
def test_database_connection():
    # Integration test with external dependency
    pass

@pytest.mark.performance
def test_large_dataset_processing():
    # Performance benchmark test
    pass

@pytest.mark.slow
def test_comprehensive_workflow():
    # Slow test that can be skipped
    pass
```

## Configuration

### Pytest Configuration (pytest.ini)

Key settings:
- Test discovery patterns
- Output formatting
- Markers definition
- Warning filters
- Timeouts and logging

### Environment Variables

For testing, set these environment variables:
```bash
# Database
DB_PASSWORD=test_password

# Alpaca API
ALPACA_PAPER_API_KEY=test_key
ALPACA_PAPER_SECRET_KEY=test_secret

# Email alerts
EMAIL_SENDER=test@example.com
EMAIL_PASSWORD=test_password
ALERT_RECIPIENT_EMAIL=alerts@example.com
```

## Migration from Legacy Tests

### Before (Legacy Pattern)

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_something():
    # Duplicate setup code
    data = create_test_data()  # Expensive operation
    # Test logic
```

### After (Optimized Pattern)

```python
from test_utils.fixtures import sample_market_data
from test_utils.helpers import TestHelper

def test_something(sample_market_data):
    # Use shared fixture (created once)
    # Test logic with optimized utilities
```

## Troubleshooting

### Performance Issues

1. **Slow test execution**: Check if tests are marked appropriately (`@pytest.mark.slow`)
2. **Memory usage**: Use `PerformanceTestHelper.memory_usage_test()` to identify memory leaks
3. **Dash app startup**: Ensure you're using class-scoped `started_app` fixture

### Common Issues

1. **Import errors**: Ensure `test_utils` package is properly installed
2. **Missing fixtures**: Check that fixtures are imported from `test_utils.fixtures`
3. **Mock failures**: Verify mock services are configured correctly in test setup

### Performance Monitoring Not Working

- Ensure `psutil` is installed for memory monitoring: `pip install psutil`
- Check that `performance_results.json` is writable
- Verify test names are consistent across runs

## Best Practices Summary

1. **Use shared fixtures** with appropriate scopes
2. **Leverage test utilities** instead of duplicate code
3. **Mark tests appropriately** for better organization
4. **Monitor performance** with built-in tools
5. **Use mocks comprehensively** for external dependencies
6. **Suppress unnecessary output** for cleaner test runs
7. **Generate consistent test data** with data generators
8. **Follow naming conventions** for automatic test discovery

## Performance Benchmarks

Current performance targets:
- Dashboard load time: < 10 seconds
- Database query time: < 2 seconds
- Chart render time: < 3 seconds
- Unit tests: < 0.1 seconds each
- Integration tests: < 5 seconds each

## Contributing

When adding new tests:

1. Use existing utilities from `test_utils/`
2. Add appropriate markers (`@pytest.mark.unit`, etc.)
3. Consider performance implications
4. Use shared fixtures when possible
5. Follow the patterns in `optimized_examples/`

For new test utilities:
1. Add to appropriate module in `test_utils/`
2. Update fixtures if needed
3. Add examples to `optimized_examples/`
4. Update this documentation