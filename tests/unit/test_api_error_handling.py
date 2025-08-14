"""
Unit tests for API error handling.
Tests API behavior with invalid inputs without requiring a real server.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.main import app
from src.api.schemas.data import MarketDataRequest, DataSource


class TestAPIErrorHandlingUnit:
    """Unit tests for API error handling using mocked dependencies."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database manager."""
        mock_db = Mock()
        mock_db.get_market_data.return_value = None
        return mock_db
    
    def test_invalid_symbol_fast(self, client, mock_db):
        """Test API behavior with invalid symbol using mocked database."""
        with patch('src.api.routes.data.get_db', return_value=mock_db):
            start_date = datetime.now() - timedelta(days=30)
            end_date = start_date + timedelta(days=1)  # Ensure end_date is after start_date
            
            payload = {
                "symbol": "INVALID_SYMBOL_12345",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "source": "yahoo"
            }
            
            response = client.post("/data/market-data", json=payload)
            
            # Should return 200 with empty data, not an error
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0  # Empty list for invalid symbol
    
    def test_invalid_date_format_fast(self, client):
        """Test API behavior with invalid date format."""
        payload = {
            "symbol": "AAPL",
            "start_date": "invalid-date",
            "end_date": "invalid-date",
            "source": "yahoo"
        }
        
        response = client.post("/data/market-data", json=payload)
        
        # Should return 422 (validation error) for invalid date format
        assert response.status_code == 422
    
    def test_missing_required_fields_fast(self, client):
        """Test API behavior with missing required fields."""
        payload = {
            "source": "yahoo"
            # Missing symbol field
        }
        
        response = client.post("/data/market-data", json=payload)
        
        # Should return 422 (validation error) for missing required fields
        assert response.status_code == 422
    
    def test_invalid_source_fast(self, client):
        """Test API behavior with invalid data source."""
        payload = {
            "symbol": "AAPL",
            "start_date": datetime.now().isoformat(),
            "end_date": datetime.now().isoformat(),
            "source": "invalid_source"
        }
        
        response = client.post("/data/market-data", json=payload)
        
        # Should return 422 (validation error) for invalid source
        assert response.status_code == 422
    
    def test_empty_symbol_fast(self, client):
        """Test API behavior with empty symbol."""
        start_date = datetime.now() - timedelta(days=30)
        end_date = start_date + timedelta(days=1)  # Ensure end_date is after start_date
        
        payload = {
            "symbol": "",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "source": "yahoo"
        }
        
        response = client.post("/data/market-data", json=payload)
        
        # Should return 200 with empty data for invalid symbol (graceful handling)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # Empty list for invalid symbol
    
    def test_symbol_too_long_fast(self, client):
        """Test API behavior with symbol that's too long."""
        start_date = datetime.now() - timedelta(days=30)
        end_date = start_date + timedelta(days=1)  # Ensure end_date is after start_date
        
        payload = {
            "symbol": "A" * 20,  # Symbol too long
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "source": "yahoo"
        }
        
        response = client.post("/data/market-data", json=payload)
        
        # Should return 200 with empty data for invalid symbol (graceful handling)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # Empty list for invalid symbol


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
