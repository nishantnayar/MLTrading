"""
Optimized pytest configuration and fixtures for MLTrading test suite.

Provides centralized test configuration with performance optimizations
and reduced duplication across the test suite.
"""

import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import patch
import os

# Add project root to path once
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add tests directory to path for test_utils import
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

# Import test utilities (after path setup)
from test_utils.fixtures import *
from test_utils.helpers import TestHelper, DashTestHelper, TestConfig
from test_utils.mocks import MockedServices, MockedEnvironment

# Configure test logging
logging.getLogger('src.dashboard').setLevel(logging.WARNING)
logging.getLogger('src.trading').setLevel(logging.WARNING)
logging.getLogger('src.utils').setLevel(logging.WARNING)


def pytest_configure(config):
    """Configure pytest with optimizations"""
    # Add custom markers
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    
    # Set test timeouts
    config.option.timeout = TestConfig.ELEMENT_WAIT_TIMEOUT


def pytest_collection_modifyitems(config, items):
    """Modify collected test items for optimization"""
    # Auto-mark slow tests based on patterns
    slow_patterns = ['test_dashboard_regression', 'test_integration', 'performance']
    
    for item in items:
        # Mark slow tests
        if any(pattern in item.nodeid.lower() for pattern in slow_patterns):
            item.add_marker(pytest.mark.slow)
        
        # Mark integration tests
        if 'integration' in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        elif 'unit' in item.nodeid.lower():
            item.add_marker(pytest.mark.unit)


@pytest.fixture(scope="session")
def app():
    """Create app instance for testing (session scope for performance)"""
    try:
        from src.dashboard.app import app as dashboard_app
        return dashboard_app
    except ImportError:
        pytest.skip("Dashboard app not available")


@pytest.fixture(scope="module")
def dash_helper(dash_duo):
    """Enhanced Dash testing helper with optimizations"""
    return DashTestHelper(dash_duo)


@pytest.fixture(autouse=True, scope="function")
def cleanup_test_state():
    """Automatically cleanup test state between tests"""
    yield
    # Reset any global state here
    # Clear caches, reset singletons, etc.


@pytest.fixture(scope="session")
def test_environment():
    """Set up test environment with mocked services and optimized database settings"""
    with MockedEnvironment(
        DB_PASSWORD='test_password',
        ALPACA_PAPER_API_KEY='test_key',
        ALPACA_PAPER_SECRET_KEY='test_secret',
        EMAIL_SENDER='test@example.com',
        EMAIL_PASSWORD='test_password',
        ALERT_RECIPIENT_EMAIL='alerts@example.com',
        # Database optimization for tests
        DATABASE_MAX_CONNECTIONS=5,
        DATABASE_MIN_CONNECTIONS=1,
        DATABASE_CONNECTION_TIMEOUT=30,
        DATABASE_QUERY_TIMEOUT=10
    ):
        yield


@pytest.fixture
def suppressed_logging():
    """Suppress verbose logging during tests"""
    with TestHelper.suppress_logging():
        yield


@pytest.fixture
def mocked_services():
    """Context manager for mocking all external services"""
    with MockedServices(mock_database=True, mock_alpaca=True, mock_email=True):
        yield


# Performance optimization fixtures
@pytest.fixture(scope="session")
def performance_config():
    """Configuration for performance testing"""
    return {
        'max_dashboard_load_time': TestConfig.DASH_APP_STARTUP_TIME,
        'max_query_time': TestConfig.DATABASE_QUERY_TIME,
        'max_chart_render_time': TestConfig.CHART_RENDER_TIME
    }


# Data fixtures (using new generators)
@pytest.fixture(scope="session")
def large_market_dataset():
    """Large dataset for performance testing"""
    from test_utils.data_generators import MarketDataGenerator
    generator = MarketDataGenerator(seed=42)  # Reproducible
    return generator.generate_multiple_symbols(
        symbols=['TEST001', 'TEST002', 'TEST003', 'TEST004', 'TEST005'],
        periods=1000
    )


@pytest.fixture
def trading_config():
    """Trading configuration for tests"""
    from test_utils.data_generators import ConfigGenerator
    return ConfigGenerator.generate_trading_config()


# Backward compatibility - keep existing fixtures but optimize them
@pytest.fixture
def legacy_sample_market_data(sample_market_data):
    """Legacy fixture for backward compatibility"""
    return sample_market_data


@pytest.fixture  
def legacy_mock_data_service(mock_data_service):
    """Legacy mock data service for backward compatibility"""
    return mock_data_service


# Pytest hooks for optimization
def pytest_runtest_setup(item):
    """Setup optimizations before each test"""
    # Skip slow tests in fast mode
    if item.get_closest_marker("slow") and item.config.getoption("--fast", default=False):
        pytest.skip("Skipping slow test in fast mode")


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--fast", action="store_true", default=False,
        help="Run only fast tests, skip slow integration tests"
    )
    parser.addoption(
        "--performance", action="store_true", default=False,
        help="Run performance tests with benchmarking"
    )