"""
Integration tests for ML Trading API endpoints.
Tests the actual API functionality when the server is running.
"""

import pytest
import requests
import json
from datetime import datetime, timedelta
from typing import Optional


class TestAPIIntegration:
    """Test suite for API integration tests."""
    
    @pytest.fixture(scope="class")
    def api_port(self) -> Optional[int]:
        """Find the port where the API is running."""
        for port in [8000, 8001, 8002, 8003, 8004]:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    return port
            except requests.RequestException:
                continue
        return None
    
    @pytest.fixture(scope="class")
    def base_url(self, api_port: Optional[int]) -> str:
        """Get the base URL for API requests."""
        if api_port is None:
            pytest.skip("API server is not running")
        return f"http://localhost:{api_port}"
    
    def test_api_health(self, base_url: str):
        """Test API health endpoints."""
        # Test main health endpoint
        response = requests.get(f"{base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ml-trading-api"
        
        # Test data API health endpoint
        response = requests.get(f"{base_url}/data/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "data-api"
    
    def test_data_symbols_endpoint(self, base_url: str):
        """Test symbols endpoint."""
        payload = {"source": "yahoo"}
        response = requests.post(f"{base_url}/data/symbols", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "symbols" in data
        assert "count" in data
        assert "source" in data
        assert data["source"] == "yahoo"
        assert isinstance(data["symbols"], list)
        assert data["count"] == len(data["symbols"])
        assert data["count"] > 0  # Should have some symbols
    
    def test_data_sectors_endpoint(self, base_url: str):
        """Test sectors endpoint."""
        response = requests.post(f"{base_url}/data/sectors")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sectors" in data
        assert "count" in data
        assert isinstance(data["sectors"], list)
        assert data["count"] == len(data["sectors"])
        assert data["count"] > 0  # Should have some sectors
    
    def test_data_industries_endpoint(self, base_url: str):
        """Test industries endpoint."""
        response = requests.post(f"{base_url}/data/industries")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "industries" in data
        assert "count" in data
        assert isinstance(data["industries"], list)
        assert data["count"] == len(data["industries"])
    
    def test_data_summary_endpoint(self, base_url: str):
        """Test data summary endpoint."""
        response = requests.get(f"{base_url}/data/data-summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_symbols" in data
        assert "total_sectors" in data
        assert "total_industries" in data
        assert isinstance(data["total_symbols"], int)
        assert isinstance(data["total_sectors"], int)
        assert isinstance(data["total_industries"], int)
        assert data["total_symbols"] > 0
        assert data["total_sectors"] > 0
    
    def test_market_data_endpoint(self, base_url: str):
        """Test market data endpoint."""
        # First get available symbols
        symbols_response = requests.post(f"{base_url}/data/symbols", json={"source": "yahoo"})
        assert symbols_response.status_code == 200
        symbols_data = symbols_response.json()
        
        if not symbols_data["symbols"]:
            pytest.skip("No symbols available for testing")
        
        # Test with first available symbol
        symbol = symbols_data["symbols"][0]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        payload = {
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "source": "yahoo"
        }
        
        response = requests.post(f"{base_url}/data/market-data", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Response should be a list of market data records
        assert isinstance(data, list)
        
        # If data exists, check structure
        if data:
            record = data[0]
            required_fields = ["symbol", "timestamp", "open", "high", "low", "close", "volume", "source"]
            for field in required_fields:
                assert field in record
    
    def test_latest_market_data_endpoint(self, base_url: str):
        """Test latest market data endpoint."""
        # First get available symbols
        symbols_response = requests.post(f"{base_url}/data/symbols", json={"source": "yahoo"})
        assert symbols_response.status_code == 200
        symbols_data = symbols_response.json()
        
        if not symbols_data["symbols"]:
            pytest.skip("No symbols available for testing")
        
        # Test with first available symbol
        symbol = symbols_data["symbols"][0]
        
        response = requests.get(f"{base_url}/data/market-data/{symbol}/latest?source=yahoo")
        
        # This might return 404 if no data exists, which is acceptable
        if response.status_code == 200:
            data = response.json()
            required_fields = ["symbol", "timestamp", "open", "high", "low", "close", "volume", "source"]
            for field in required_fields:
                assert field in data
            assert data["symbol"] == symbol
        elif response.status_code == 404:
            # No data available for this symbol
            pass
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_stock_info_endpoint(self, base_url: str):
        """Test stock info endpoint."""
        # First get available symbols
        symbols_response = requests.post(f"{base_url}/data/symbols", json={"source": "yahoo"})
        assert symbols_response.status_code == 200
        symbols_data = symbols_response.json()
        
        if not symbols_data["symbols"]:
            pytest.skip("No symbols available for testing")
        
        # Test with first available symbol
        symbol = symbols_data["symbols"][0]
        
        payload = {"symbol": symbol}
        response = requests.post(f"{base_url}/data/stock-info", json=payload)
        
        # This might return 404 if no stock info exists, which is acceptable
        if response.status_code == 200:
            data = response.json()
            assert "symbol" in data
            assert data["symbol"] == symbol
        elif response.status_code == 404:
            # No stock info available for this symbol
            pass
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_sector_stocks_endpoint(self, base_url: str):
        """Test sector stocks endpoint."""
        # First get available sectors
        sectors_response = requests.post(f"{base_url}/data/sectors")
        assert sectors_response.status_code == 200
        sectors_data = sectors_response.json()
        
        if not sectors_data["sectors"]:
            pytest.skip("No sectors available for testing")
        
        # Find first non-empty sector
        sectors = [s for s in sectors_data["sectors"] if s.strip()]
        if not sectors:
            pytest.skip("No valid sectors available for testing")
        
        # Test with first available non-empty sector
        sector = sectors[0]
        
        response = requests.post(f"{base_url}/data/sectors/{sector}/stocks")
        
        assert response.status_code == 200
        data = response.json()
        
        # Response should be a list of symbols
        assert isinstance(data, list)
    
    def test_industry_stocks_endpoint(self, base_url: str):
        """Test industry stocks endpoint."""
        # First get available industries
        industries_response = requests.post(f"{base_url}/data/industries")
        assert industries_response.status_code == 200
        industries_data = industries_response.json()
        
        if not industries_data["industries"]:
            pytest.skip("No industries available for testing")
        
        # Find first non-empty industry
        industries = [i for i in industries_data["industries"] if i.strip()]
        if not industries:
            pytest.skip("No valid industries available for testing")
        
        # Test with first available non-empty industry
        industry = industries[0]
        
        response = requests.post(f"{base_url}/data/industries/{industry}/stocks")
        
        assert response.status_code == 200
        data = response.json()
        
        # Response should be a list of symbols
        assert isinstance(data, list)
    
    def test_date_range_endpoint(self, base_url: str):
        """Test date range endpoint."""
        # First get available symbols
        symbols_response = requests.post(f"{base_url}/data/symbols", json={"source": "yahoo"})
        assert symbols_response.status_code == 200
        symbols_data = symbols_response.json()
        
        if not symbols_data["symbols"]:
            pytest.skip("No symbols available for testing")
        
        # Test with first available symbol
        symbol = symbols_data["symbols"][0]
        
        payload = {
            "symbol": symbol,
            "source": "yahoo"
        }
        
        response = requests.post(f"{base_url}/data/date-range", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "symbol" in data
        assert "source" in data
        assert "has_data" in data
        assert data["symbol"] == symbol
        assert data["source"] == "yahoo"
        assert isinstance(data["has_data"], bool)


class TestAPIErrorHandling:
    """Test suite for API error handling."""
    
    @pytest.fixture(scope="class")
    def api_port(self) -> Optional[int]:
        """Find the port where the API is running."""
        for port in [8000, 8001, 8002, 8003, 8004]:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    return port
            except requests.RequestException:
                continue
        return None
    
    @pytest.fixture(scope="class")
    def base_url(self, api_port: Optional[int]) -> str:
        """Get the base URL for API requests."""
        if api_port is None:
            pytest.skip("API server is not running")
        return f"http://localhost:{api_port}"
    
    def test_invalid_symbol(self, base_url: str):
        """Test API behavior with invalid symbol."""
        payload = {
            "symbol": "INVALID_SYMBOL_12345",
            "start_date": datetime.now().isoformat(),
            "end_date": datetime.now().isoformat(),
            "source": "yahoo"
        }
        
        response = requests.post(f"{base_url}/data/market-data", json=payload)
        
        # Should return 200 with empty data, not an error
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Empty list is acceptable for invalid symbol
    
    def test_invalid_date_format(self, base_url: str):
        """Test API behavior with invalid date format."""
        payload = {
            "symbol": "AAPL",
            "start_date": "invalid-date",
            "end_date": "invalid-date",
            "source": "yahoo"
        }
        
        response = requests.post(f"{base_url}/data/market-data", json=payload)
        
        # Should return 422 (validation error) for invalid date format
        assert response.status_code == 422
    
    def test_missing_required_fields(self, base_url: str):
        """Test API behavior with missing required fields."""
        payload = {
            "source": "yahoo"
            # Missing symbol field
        }
        
        response = requests.post(f"{base_url}/data/market-data", json=payload)
        
        # Should return 422 (validation error) for missing required fields
        assert response.status_code == 422


def run_api_tests():
    """Run API tests and print results."""
    print("🚀 ML Trading API Integration Tests")
    print("=" * 50)
    
    # Check if API is running
    api_port = None
    for port in [8000, 8001, 8002, 8003, 8004]:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                api_port = port
                break
        except requests.RequestException:
            continue
    
    if api_port is None:
        print("❌ API server is not running")
        print("Please start the API server first:")
        print("   python run_ui.py")
        return False
    
    print(f"✅ API is running on port {api_port}")
    
    # Run basic tests
    base_url = f"http://localhost:{api_port}"
    tests_passed = 0
    tests_failed = 0
    
    # Test health endpoints
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint test passed")
            tests_passed += 1
        else:
            print(f"❌ Health endpoint test failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Health endpoint test error: {e}")
        tests_failed += 1
    
    # Test symbols endpoint
    try:
        payload = {"source": "yahoo"}
        response = requests.post(f"{base_url}/data/symbols", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Symbols endpoint test passed: {data.get('count', 0)} symbols")
            tests_passed += 1
        else:
            print(f"❌ Symbols endpoint test failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Symbols endpoint test error: {e}")
        tests_failed += 1
    
    # Test sectors endpoint
    try:
        response = requests.post(f"{base_url}/data/sectors")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sectors endpoint test passed: {data.get('count', 0)} sectors")
            tests_passed += 1
        else:
            print(f"❌ Sectors endpoint test failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Sectors endpoint test error: {e}")
        tests_failed += 1
    
    # Test data summary
    try:
        response = requests.get(f"{base_url}/data/data-summary")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Data summary test passed: {data.get('total_symbols', 0)} symbols, {data.get('total_sectors', 0)} sectors")
            tests_passed += 1
        else:
            print(f"❌ Data summary test failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Data summary test error: {e}")
        tests_failed += 1
    
    print(f"\n📊 Test Results: {tests_passed} passed, {tests_failed} failed")
    
    if tests_failed == 0:
        print("🎉 All tests passed!")
        print(f"\n📖 API Documentation available at:")
        print(f"   Swagger UI: http://localhost:{api_port}/docs")
        print(f"   ReDoc: http://localhost:{api_port}/redoc")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    run_api_tests() 