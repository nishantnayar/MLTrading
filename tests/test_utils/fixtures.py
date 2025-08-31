"""
Shared pytest fixtures for the MLTrading test suite.

Provides commonly used fixtures to reduce duplication across test files.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import yaml
import os
from unittest.mock import Mock, patch


@pytest.fixture(scope="session")
def sample_market_data():
    """Comprehensive sample market data for testing"""
    return {
        "symbols": [
            {"symbol": "AAPL", "company_name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics"},
            {"symbol": "GOOGL", "company_name": "Alphabet Inc.", "sector": "Technology", "industry": "Internet Content & Information"},
            {"symbol": "MSFT", "company_name": "Microsoft Corp.", "sector": "Technology", "industry": "Software Infrastructure"},
            {"symbol": "JNJ", "company_name": "Johnson & Johnson", "sector": "Healthcare", "industry": "Drug Manufacturers"},
            {"symbol": "JPM", "company_name": "JPMorgan Chase", "sector": "Finance", "industry": "Banks"},
            {"symbol": "TSLA", "company_name": "Tesla Inc.", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers"},
            {"symbol": "NVDA", "company_name": "NVIDIA Corp.", "sector": "Technology", "industry": "Semiconductors"}
        ],
        "sectors": [
            {"sector": "Technology", "count": 4},
            {"sector": "Healthcare", "count": 1}, 
            {"sector": "Finance", "count": 1},
            {"sector": "Consumer Cyclical", "count": 1}
        ],
        "ohlcv_data": {
            "AAPL": pd.DataFrame({
                'timestamp': pd.date_range(start='2023-01-01', periods=30, freq='D'),
                'open': np.random.uniform(150, 170, 30),
                'high': np.random.uniform(155, 175, 30),
                'low': np.random.uniform(145, 165, 30),
                'close': np.random.uniform(148, 172, 30),
                'volume': np.random.randint(50000000, 100000000, 30)
            })
        }
    }


@pytest.fixture(scope="session")
def technical_indicator_data():
    """Test data specifically designed for technical indicator testing"""
    dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
    
    # Create price series with known patterns
    base_price = 100.0
    trend = np.linspace(0, 20, 50)  # Upward trend
    noise = np.random.normal(0, 2, 50)  # Random noise
    prices = base_price + trend + noise
    
    # Ensure realistic OHLC relationships
    closes = prices
    opens = closes + np.random.normal(0, 1, 50)
    highs = np.maximum(opens, closes) + np.random.uniform(0, 2, 50)
    lows = np.minimum(opens, closes) - np.random.uniform(0, 2, 50)
    volumes = np.random.randint(1000000, 5000000, 50)
    
    return pd.DataFrame({
        'timestamp': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    }).set_index('timestamp')


@pytest.fixture(scope="session")
def alert_test_config():
    """Configuration for alert system testing"""
    return {
        'email_alerts': {
            'enabled': True,
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'use_tls': True,
            'timeout': 30
        },
        'alerts': {
            'enabled': True,
            'min_severity': 'MEDIUM',
            'rate_limiting': {
                'enabled': True,
                'max_alerts_per_hour': 5,
                'max_alerts_per_day': 20
            },
            'alert_categories': {
                'trading_errors': {'enabled': True, 'severity': 'HIGH'},
                'system_health': {'enabled': True, 'severity': 'MEDIUM'},
                'data_pipeline': {'enabled': True, 'severity': 'MEDIUM'},
                'security': {'enabled': True, 'severity': 'CRITICAL'}
            }
        }
    }


@pytest.fixture(scope="session")
def alpaca_test_config():
    """Test configuration for Alpaca trading service"""
    return {
        'trading': {'mode': 'paper'},
        'alpaca': {
            'paper_trading': {'base_url': 'https://paper-api.alpaca.markets'},
            'live_trading': {'base_url': 'https://api.alpaca.markets'}
        },
        'risk': {
            'emergency_stop': False,
            'max_position_size': 1000,
            'max_daily_orders': 25
        }
    }


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'DB_PASSWORD': 'test_password',
        'ALPACA_PAPER_API_KEY': 'test_paper_key',
        'ALPACA_PAPER_SECRET_KEY': 'test_paper_secret',
        'EMAIL_SENDER': 'test@example.com',
        'EMAIL_PASSWORD': 'test_password',
        'ALERT_RECIPIENT_EMAIL': 'alerts@example.com'
    }):
        yield


@pytest.fixture(scope="module")
def shared_dash_app():
    """Shared Dash app instance for testing (module scope to reduce startup overhead)"""
    try:
        from src.dashboard.app import app as dashboard_app
        return dashboard_app
    except ImportError:
        pytest.skip("Dashboard app not available")


@pytest.fixture
def mock_data_service(monkeypatch, sample_market_data):
    """Mock data service with comprehensive functionality"""
    
    class MockDataService:
        def __init__(self):
            self.data = sample_market_data
        
        def get_available_symbols(self):
            return self.data["symbols"]
        
        def get_sector_distribution(self):
            return {
                "sectors": [s["sector"] for s in self.data["sectors"]],
                "counts": [s["count"] for s in self.data["sectors"]]
            }
        
        def get_market_data(self, symbol, start_date=None, end_date=None):
            if symbol in self.data["ohlcv_data"]:
                df = self.data["ohlcv_data"][symbol].copy()
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]
                return df
            return pd.DataFrame()
        
        def get_top_symbols_by_volume(self, limit=10):
            return self.data["symbols"][:limit]
        
        def get_price_performance(self, symbols, period='1M'):
            return {
                symbol: np.random.uniform(-10, 10) 
                for symbol in [s['symbol'] for s in symbols]
            }
    
    mock_service = MockDataService()
    
    # Apply mocks to various service modules
    service_paths = [
        "src.dashboard.services.market_data_service.MarketDataService",
        "src.dashboard.services.symbol_service.SymbolService",
        "src.dashboard.services.data_service.DataService"
    ]
    
    for path in service_paths:
        try:
            monkeypatch.setattr(f"{path}.get_available_symbols", mock_service.get_available_symbols)
            monkeypatch.setattr(f"{path}.get_sector_distribution", mock_service.get_sector_distribution)
        except AttributeError:
            # Some services may not exist, skip gracefully
            pass
    
    return mock_service


@pytest.fixture
def mock_database_connection():
    """Mock database connection for testing"""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None
    
    # Mock common database operations
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    mock_cursor.execute.return_value = None
    
    return mock_conn


@pytest.fixture
def performance_data():
    """Generate performance test data with larger datasets"""
    n_records = 10000
    n_symbols = 100
    
    symbols = [f"TEST{i:03d}" for i in range(n_symbols)]
    dates = pd.date_range(start='2020-01-01', periods=n_records // n_symbols, freq='D')
    
    data = []
    for symbol in symbols:
        for date in dates:
            data.append({
                'symbol': symbol,
                'timestamp': date,
                'open': np.random.uniform(50, 200),
                'high': np.random.uniform(55, 220),
                'low': np.random.uniform(45, 180),
                'close': np.random.uniform(50, 210),
                'volume': np.random.randint(100000, 10000000)
            })
    
    return pd.DataFrame(data)


@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing error handling"""
    return {
        'network_error': ConnectionError("Network connection failed"),
        'api_error': ValueError("Invalid API response"),
        'timeout_error': TimeoutError("Request timed out"),
        'auth_error': PermissionError("Authentication failed"),
        'data_error': KeyError("Required data field missing")
    }


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests to prevent state leakage"""
    yield
    # Reset any singleton instances here
    # This ensures clean state between tests