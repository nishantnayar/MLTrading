"""
Data service for dashboard to connect with market_data table.
Provides methods to fetch and format data for the UI.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.storage.database import get_db_manager
from src.utils.logging_config import get_ui_logger

# Initialize logger
logger = get_ui_logger("dashboard")

class MarketDataService:
    """Service to handle market data operations for the dashboard."""
    
    def __init__(self):
        """Initialize the data service."""
        self.db_manager = get_db_manager()
        logger.info("MarketDataService initialized")
    
    def get_available_symbols(self, source: str = 'yahoo') -> List[str]:
        """Get list of available symbols with market data."""
        try:
            symbols = self.db_manager.get_symbols_with_data(source)
            logger.info(f"Retrieved {len(symbols)} symbols from database")
            return symbols
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            return []
    
    def get_market_data(self, symbol: str, days: int = 30, source: str = 'yahoo') -> pd.DataFrame:
        """Get market data for a symbol for the specified number of days."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = self.db_manager.get_market_data(symbol, start_date, end_date, source)
            
            if df.empty:
                logger.warning(f"No data found for {symbol} in the specified date range")
                return pd.DataFrame()
            
            logger.info(f"Retrieved {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_latest_data(self, symbol: str, source: str = 'yahoo') -> Optional[Dict]:
        """Get the latest market data for a symbol."""
        try:
            latest = self.db_manager.get_latest_market_data(symbol, source)
            if latest:
                logger.info(f"Retrieved latest data for {symbol}")
            return latest
        except Exception as e:
            logger.error(f"Failed to get latest data for {symbol}: {e}")
            return None
    
    def get_dashboard_stats(self, symbol: str = 'AAPL', source: str = 'yahoo') -> Dict[str, Any]:
        """Get dashboard statistics for a symbol."""
        try:
            # Get recent data
            df = self.get_market_data(symbol, days=30, source=source)
            
            if df.empty:
                return {
                    'current_price': 0,
                    'daily_change': 0,
                    'daily_change_percent': 0,
                    'total_volume': 0,
                    'last_signal': 'N/A',
                    'has_data': False
                }
            
            # Calculate statistics
            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest
            
            current_price = latest['close']
            daily_change = current_price - previous['close']
            daily_change_percent = (daily_change / previous['close']) * 100 if previous['close'] > 0 else 0
            total_volume = df['volume'].sum()
            
            # Determine signal based on price movement
            if daily_change > 0:
                last_signal = 'BUY'
            elif daily_change < 0:
                last_signal = 'SELL'
            else:
                last_signal = 'HOLD'
            
            stats = {
                'current_price': round(current_price, 2),
                'daily_change': round(daily_change, 2),
                'daily_change_percent': round(daily_change_percent, 2),
                'total_volume': int(total_volume),
                'last_signal': last_signal,
                'has_data': True,
                'symbol': symbol
            }
            
            logger.info(f"Calculated dashboard stats for {symbol}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to calculate dashboard stats for {symbol}: {e}")
            return {
                'current_price': 0,
                'daily_change': 0,
                'daily_change_percent': 0,
                'total_volume': 0,
                'last_signal': 'N/A',
                'has_data': False
            }
    
    def get_chart_data(self, symbol: str, days: int = 30, source: str = 'yahoo') -> Dict[str, Any]:
        """Get formatted data for charts."""
        try:
            df = self.get_market_data(symbol, days, source)
            
            if df.empty:
                return {
                    'dates': [],
                    'prices': [],
                    'volumes': [],
                    'has_data': False
                }
            
            # Format data for charts
            chart_data = {
                'dates': df['timestamp'].dt.strftime('%Y-%m-%d').tolist(),
                'prices': df['close'].tolist(),
                'volumes': df['volume'].tolist(),
                'has_data': True,
                'symbol': symbol
            }
            
            logger.info(f"Prepared chart data for {symbol}")
            return chart_data
            
        except Exception as e:
            logger.error(f"Failed to prepare chart data for {symbol}: {e}")
            return {
                'dates': [],
                'prices': [],
                'volumes': [],
                'has_data': False
            }
    
    def get_recent_signals(self, symbol: str, days: int = 7, source: str = 'yahoo') -> List[Dict]:
        """Get recent trading signals based on price movements."""
        try:
            df = self.get_market_data(symbol, days, source)
            
            if df.empty:
                return []
            
            signals = []
            for i in range(1, len(df)):
                current = df.iloc[i]
                previous = df.iloc[i-1]
                
                price_change = current['close'] - previous['close']
                
                if price_change > 0:
                    signal = 'BUY'
                elif price_change < 0:
                    signal = 'SELL'
                else:
                    signal = 'HOLD'
                
                signals.append({
                    'date': current['timestamp'].strftime('%Y-%m-%d'),
                    'signal': signal,
                    'price': round(current['close'], 2),
                    'change': round(price_change, 2)
                })
            
            # Return last 5 signals
            recent_signals = signals[-5:] if len(signals) > 5 else signals
            logger.info(f"Generated {len(recent_signals)} recent signals for {symbol}")
            return recent_signals
            
        except Exception as e:
            logger.error(f"Failed to generate signals for {symbol}: {e}")
            return []

# Global data service instance
data_service = None

def get_data_service() -> MarketDataService:
    """Get the global data service instance."""
    global data_service
    if data_service is None:
        data_service = MarketDataService()
    return data_service 