# ML Trading System Tests

This document describes the testing structure and procedures for the ML Trading System.

## Test Structure

```
tests/
├── __init__.py
├── unit/                    # Unit tests
│   └── __init__.py
└── integration/             # Integration tests
    ├── __init__.py
    └── test_api_integration.py
```

## Test Types

### Unit Tests (`tests/unit/`)
- Test individual functions and classes in isolation
- Fast execution
- No external dependencies
- Mock external services

### Integration Tests (`tests/integration/`)
- Test how components work together
- May require external services (database, API)
- Slower execution
- Test real data flows

## Running Tests

### Quick API Health Check
```bash
python run_tests.py --type quick
```

### Run All Tests
```bash
python run_tests.py --type all
```

### Run Specific Test Types
```bash
# Unit tests only
python run_tests.py --type unit

# Integration tests only
python run_tests.py --type integration

# API tests only
python run_tests.py --type api
```

### Using pytest directly
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/integration/test_api_integration.py -v

# Run tests matching pattern
pytest tests/ -k "api" -v
```

## API Integration Tests

The API integration tests (`test_api_integration.py`) require the API server to be running. They will:

1. **Auto-detect** the running API server (ports 8000-8004)
2. **Test all endpoints** for proper functionality
3. **Validate responses** for correct structure and data
4. **Test error handling** for invalid inputs

### Prerequisites for API Tests
- API server must be running (start with `python run_ui.py`)
- Database must be accessible
- Test data should be available

### What API Tests Cover
- ✅ Health endpoints
- ✅ Data endpoints (symbols, sectors, industries)
- ✅ Market data retrieval
- ✅ Stock information
- ✅ Error handling
- ✅ Response validation

## Test Configuration

### pytest.ini
- Configures test discovery patterns
- Sets up markers for test categorization
- Configures output format

### Coverage
Tests can generate coverage reports:
```bash
pytest tests/ --cov=src --cov-report=html
```

This creates an HTML coverage report in `htmlcov/`.

## Writing Tests

### Unit Test Example
```python
import pytest
from src.some_module import some_function

def test_some_function():
    """Test some_function behavior."""
    result = some_function("input")
    assert result == "expected_output"
```

### Integration Test Example
```python
import pytest
import requests

class TestAPIIntegration:
    def test_api_health(self, base_url):
        """Test API health endpoint."""
        response = requests.get(f"{base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
```

### Test Markers
Use markers to categorize tests:
```python
@pytest.mark.integration
def test_api_endpoint():
    pass

@pytest.mark.slow
def test_expensive_operation():
    pass
```

## Continuous Integration

Tests can be run in CI/CD pipelines:
```yaml
- name: Run tests
  run: |
    python run_tests.py --type all
```

## Troubleshooting

### API Tests Failing
1. Ensure API server is running: `python run_ui.py`
2. Check database connection
3. Verify test data exists
4. Check API logs for errors

### Import Errors
1. Ensure you're in the project root directory
2. Check that `src/` is in Python path
3. Verify all dependencies are installed

### Test Discovery Issues
1. Ensure test files follow naming convention: `test_*.py`
2. Check that test functions start with `test_`
3. Verify test classes start with `Test`

## Test Commands Reference

### Quick Commands
```bash
# Quick API health check
python run_tests.py --type quick

# Run all tests with coverage
python run_tests.py --type all

# Run only API tests
python run_tests.py --type api
```

### Pytest Commands
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/integration/test_api_integration.py -v

# Run tests matching pattern
pytest tests/ -k "api" -v

# Run tests with specific markers
pytest tests/ -m "integration" -v
```

### Coverage Commands
```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Generate terminal coverage report
pytest tests/ --cov=src --cov-report=term

# Generate both HTML and terminal reports
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

## Test Best Practices

### Writing Good Tests
1. **Test one thing at a time** - Each test should verify one specific behavior
2. **Use descriptive names** - Test names should clearly describe what they test
3. **Arrange-Act-Assert** - Structure tests with setup, action, and verification
4. **Keep tests independent** - Tests should not depend on each other
5. **Use appropriate assertions** - Choose the right assertion for the scenario

### Test Organization
1. **Group related tests** - Use test classes to group related functionality
2. **Use fixtures** - Share setup code between tests
3. **Mark tests appropriately** - Use markers to categorize tests
4. **Keep tests fast** - Unit tests should run quickly

### Integration Test Guidelines
1. **Test real scenarios** - Test actual use cases, not just happy paths
2. **Handle external dependencies** - Mock or stub external services when appropriate
3. **Test error conditions** - Verify proper error handling
4. **Clean up after tests** - Ensure tests don't leave data behind

## Performance Testing

### Load Testing API
```bash
# Install locust for load testing
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000
```

### Benchmark Tests
```bash
# Run performance benchmarks
pytest tests/ -m "benchmark" -v
```

## Security Testing

### API Security Tests
- Authentication and authorization
- Input validation
- SQL injection prevention
- XSS protection
- Rate limiting

### Data Security Tests
- Sensitive data handling
- Encryption/decryption
- Secure communication
- Access control

## Monitoring and Reporting

### Test Metrics
- Test execution time
- Coverage percentage
- Pass/fail rates
- Flaky test detection

### Continuous Monitoring
- Automated test runs
- Coverage tracking
- Performance regression detection
- Security vulnerability scanning 