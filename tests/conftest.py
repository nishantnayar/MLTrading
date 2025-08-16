"""
Pytest configuration and fixtures for dashboard testing
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def app():
    """Create app instance for testing"""
    from src.dashboard.app import app as dashboard_app
    return dashboard_app


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        "symbols": [
            {"symbol": "AAPL", "company_name": "Apple Inc.", "sector": "Technology"},
            {"symbol": "GOOGL", "company_name": "Alphabet Inc.", "sector": "Technology"},
            {"symbol": "MSFT", "company_name": "Microsoft Corp.", "sector": "Technology"},
            {"symbol": "JNJ", "company_name": "Johnson & Johnson", "sector": "Healthcare"},
            {"symbol": "JPM", "company_name": "JPMorgan Chase", "sector": "Finance"}
        ],
        "sectors": [
            {"sector": "Technology", "count": 3},
            {"sector": "Healthcare", "count": 1}, 
            {"sector": "Finance", "count": 1}
        ]
    }


@pytest.fixture
def mock_data_service(monkeypatch, sample_market_data):
    """Mock data service for testing"""
    def mock_get_available_symbols():
        return sample_market_data["symbols"]
    
    def mock_get_sector_distribution():
        return {
            "sectors": [s["sector"] for s in sample_market_data["sectors"]],
            "counts": [s["count"] for s in sample_market_data["sectors"]]
        }
    
    # Apply mocks
    monkeypatch.setattr("src.dashboard.services.market_data_service.MarketDataService.get_available_symbols", mock_get_available_symbols)
    monkeypatch.setattr("src.dashboard.services.symbol_service.SymbolService.get_sector_distribution", mock_get_sector_distribution)