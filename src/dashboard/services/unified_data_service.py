"""
Unified data service that combines all dashboard services.
Provides a single interface for dashboard data operations with backwards compatibility.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta

from .symbol_service import SymbolService
from .market_data_service import MarketDataService as CoreMarketDataService
from .analytics_service import AnalyticsService
from ...utils.logging_config import get_ui_logger


class MarketDataService:
    """
    Unified data service that provides backwards compatibility 
    while using the new modular service architecture.
    """
    
    def __init__(self):
        """Initialize unified service with all sub-services."""
        self.symbol_service = SymbolService()
        self.market_service = CoreMarketDataService()
        self.analytics_service = AnalyticsService()
        self.logger = get_ui_logger("unified_dashboard_service")
        self.logger.info("Unified MarketDataService initialized with modular architecture")
    
    # Symbol Service Methods (delegated)
    def get_available_symbols(self, source: str = 'yahoo') -> List[Dict[str, str]]:
        """Get list of available symbols with market data and company names."""
        return self.symbol_service.get_available_symbols(source)
    
    def get_symbols_by_sector(self, sector: str, source: str = 'yahoo') -> List[Dict[str, str]]:
        """Get symbols filtered by sector."""
        return self.symbol_service.get_symbols_by_sector(sector, source)
    
    def get_symbols_by_industry(self, industry: str, source: str = 'yahoo') -> List[Dict[str, str]]:
        """Get symbols filtered by industry."""
        return self.symbol_service.get_symbols_by_industry(industry, source)
    
    def get_sector_distribution(self, source: str = 'yahoo') -> Dict[str, Any]:
        """Get distribution of symbols by sector."""
        return self.symbol_service.get_sector_distribution(source)
    
    def get_industry_distribution(self, sector: str, source: str = 'yahoo') -> Dict[str, Any]:
        """Get distribution of symbols by industry within a sector."""
        return self.symbol_service.get_industry_distribution(sector, source)
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search symbols by symbol or company name."""
        return self.symbol_service.search_symbols(query, limit)
    
    # Market Data Service Methods (delegated)
    def get_market_data(self, symbol: str, days: int = 30, source: str = 'yahoo', hourly: bool = False) -> pd.DataFrame:
        """Get historical market data for a symbol."""
        return self.market_service.get_market_data(symbol, days, source, hourly)
    
    def get_latest_price(self, symbol: str, source: str = 'yahoo') -> Optional[Dict[str, Any]]:
        """Get the latest price data for a symbol."""
        return self.market_service.get_latest_price(symbol, source)
    
    def get_price_change(self, symbol: str, days: int = 1, source: str = 'yahoo') -> Optional[Dict[str, Any]]:
        """Get price change over specified number of days."""
        return self.market_service.get_price_change(symbol, days, source)
    
    def get_data_date_range(self, source: str = 'yahoo') -> str:
        """Get the date range of available data."""
        return self.market_service.get_data_date_range(source)
    
    def get_data_quality_metrics(self, symbol: str, source: str = 'yahoo') -> Dict[str, Any]:
        """Get data quality metrics for a symbol."""
        return self.market_service.get_data_quality_metrics(symbol, source)
    
    # Analytics Service Methods (delegated)
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for the dashboard."""
        return self.analytics_service.get_summary_statistics()
    
    def get_market_overview(self, days: int = 30) -> Dict[str, Any]:
        """Get market overview data for the specified period."""
        return self.analytics_service.get_market_overview(days)
    
    def get_top_performers(self, days: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing stocks over the specified period."""
        return self.analytics_service.get_top_performers(days, limit)
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trading activity."""
        return self.analytics_service.get_recent_activity(limit)
    
    def get_portfolio_performance(self, days: int = 30) -> Dict[str, Any]:
        """Get portfolio performance metrics."""
        return self.analytics_service.get_portfolio_performance(days)
    
    def get_symbol_correlation(self, symbols: List[str], days: int = 90) -> Dict[str, Any]:
        """Calculate correlation matrix for given symbols."""
        return self.analytics_service.get_symbol_correlation(symbols, days)
    
    def get_volatility_metrics(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Calculate volatility metrics for a symbol."""
        return self.analytics_service.get_volatility_metrics(symbol, days)
    
    # Additional convenience methods
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific symbol."""
        return self.symbol_service.get_symbol_info(symbol)
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format."""
        return self.symbol_service.validate_symbol(symbol)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all sub-services."""
        try:
            status = {
                'unified_service': 'active',
                'symbol_service': 'active' if hasattr(self.symbol_service, 'db_manager') else 'error',
                'market_service': 'active' if hasattr(self.market_service, 'db_manager') else 'error', 
                'analytics_service': 'active' if hasattr(self.analytics_service, 'db_manager') else 'error',
                'database_connection': 'connected' if self.symbol_service.db_manager else 'disconnected',
                'services_count': 3,
                'initialization_time': datetime.now().isoformat()
            }
            
            self.logger.info("Retrieved service status")
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting service status: {e}")
            return {
                'unified_service': 'error',
                'error_message': str(e)
            }