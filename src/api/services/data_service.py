"""
Data service for consuming data extraction APIs.
Provides a clean interface for accessing market data, stock information, and other data.
"""

import requests
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class DataService:
    """Service for consuming data extraction APIs."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize data service.

        Args:
            base_url: Base URL for the API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests

        Returns:
            Response data as dictionary

        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def get_market_data(self, symbol: str, start_date: datetime,
                       end_date: datetime, source: str = "yahoo") -> pd.DataFrame:
        """
        Get market data for a symbol within date range.

        Args:
            symbol: Stock symbol
            start_date: Start date for data range
            end_date: End date for data range
            source: Data source (yahoo, alpaca, iex)

        Returns:
            DataFrame with market data
        """
        endpoint = "/data/market-data"
        payload = {
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "source": source
        }

        data = self._make_request("POST", endpoint, json=payload)

        if not data:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')

        return df

    def get_latest_market_data(self, symbol: str, source: str = "yahoo") -> Optional[Dict[str, Any]]:
        """
        Get latest market data for a symbol.

        Args:
            symbol: Stock symbol
            source: Data source

        Returns:
            Latest market data or None if not found
        """
        endpoint = f"/data/market-data/{symbol}/latest"
        params = {"source": source}

        try:
            data = self._make_request("GET", endpoint, params=params)
            return data
        except requests.RequestException:
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get stock information for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Stock information or None if not found
        """
        endpoint = "/data/stock-info"
        payload = {"symbol": symbol}

        try:
            data = self._make_request("POST", endpoint, json=payload)
            return data
        except requests.RequestException:
            return None

    def get_symbols(self, source: str = "yahoo") -> List[str]:
        """
        Get list of available symbols.

        Args:
            source: Data source

        Returns:
            List of symbols
        """
        endpoint = "/data/symbols"
        payload = {"source": source}

        data = self._make_request("POST", endpoint, json=payload)
        return data.get("symbols", [])

    def get_date_range(self, symbol: str, source: str = "yahoo") -> Dict[str, Any]:
        """
        Get date range of available data for a symbol.

        Args:
            symbol: Stock symbol
            source: Data source

        Returns:
            Dictionary with start_date, end_date, and has_data
        """
        endpoint = "/data/date-range"
        payload = {
            "symbol": symbol,
            "source": source
        }

        data = self._make_request("POST", endpoint, json=payload)

        # Convert string dates back to datetime objects
        if data.get("start_date"):
            data["start_date"] = datetime.fromisoformat(data["start_date"].replace('Z', '+00:00'))
        if data.get("end_date"):
            data["end_date"] = datetime.fromisoformat(data["end_date"].replace('Z', '+00:00'))

        return data

    def get_sectors(self) -> List[str]:
        """
        Get all available sectors.

        Returns:
            List of sectors
        """
        endpoint = "/data/sectors"
        data = self._make_request("POST", endpoint)
        return data.get("sectors", [])

    def get_industries(self) -> List[str]:
        """
        Get all available industries.

        Returns:
            List of industries
        """
        endpoint = "/data/industries"
        data = self._make_request("POST", endpoint)
        return data.get("industries", [])

    def get_stocks_by_sector(self, sector: str) -> List[str]:
        """
        Get all symbols in a specific sector.

        Args:
            sector: Sector name

        Returns:
            List of symbols
        """
        endpoint = f"/data/sectors/{sector}/stocks"
        data = self._make_request("POST", endpoint)
        return data

    def get_stocks_by_industry(self, industry: str) -> List[str]:
        """
        Get all symbols in a specific industry.

        Args:
            industry: Industry name

        Returns:
            List of symbols
        """
        endpoint = f"/data/industries/{industry}/stocks"
        data = self._make_request("POST", endpoint)
        return data

    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of available data in the system.

        Returns:
            Data summary dictionary
        """
        endpoint = "/data/data-summary"
        data = self._make_request("GET", endpoint)
        return data

    def health_check(self) -> bool:
        """
        Check if the API is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            endpoint = "/data/health"
            data = self._make_request("GET", endpoint)
            return data.get("status") == "healthy"
        except requests.RequestException:
            return False

    def close(self):
        """Close the session."""
        self.session.close()


# Global data service instance
_data_service = None


def get_data_service(base_url: str = None) -> DataService:
    """
    Get the global data service instance.

    Args:
        base_url: Base URL for the API server. If None, will try to detect the port.

    Returns:
        DataService instance
    """
    global _data_service

    if base_url is None:
        # Try to detect the running API server
        import socket
        import requests

        def find_api_port():
            """Find the port where the API is running."""
            for port in [8000, 8001, 8002, 8003, 8004]:
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=1)
                    if response.status_code == 200:
                        return port
                except requests.RequestException:
                    continue
            return 8000  # Default fallback

        port = find_api_port()
        base_url = f"http://localhost:{port}"

    if _data_service is None or _data_service.base_url != base_url:
        _data_service = DataService(base_url)

    return _data_service
