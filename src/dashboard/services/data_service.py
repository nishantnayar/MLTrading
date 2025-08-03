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
    
    def get_available_symbols(self, source: str = 'yahoo') -> List[Dict[str, str]]:
        """Get list of available symbols with market data and company names."""
        try:
            symbols = self.db_manager.get_symbols_with_data(source)
            # Get company names for each symbol
            symbol_data = []
            for symbol in symbols:
                stock_info = self.db_manager.get_stock_info(symbol)
                if stock_info and stock_info.get('company_name'):
                    symbol_data.append({
                        'symbol': symbol,
                        'company_name': stock_info['company_name']
                    })
                else:
                    # Fallback if no company name found
                    symbol_data.append({
                        'symbol': symbol,
                        'company_name': symbol
                    })
            
            logger.info(f"Retrieved {len(symbol_data)} symbols with company names from database")
            return symbol_data
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            # Return fallback symbols if database is not available
            return [
                {'symbol': 'AAPL', 'company_name': 'Apple Inc.'},
                {'symbol': 'GOOGL', 'company_name': 'Alphabet Inc.'},
                {'symbol': 'MSFT', 'company_name': 'Microsoft Corporation'},
                {'symbol': 'TSLA', 'company_name': 'Tesla Inc.'},
                {'symbol': 'AMZN', 'company_name': 'Amazon.com Inc.'}
            ]
    
    def get_symbols_by_sector(self, sector: str, source: str = 'yahoo') -> List[Dict[str, str]]:
        """Get list of symbols with company names for a specific sector."""
        try:
            symbols = self.db_manager.get_stocks_by_sector(sector)
            # Get company names for each symbol
            symbol_data = []
            for symbol in symbols:
                stock_info = self.db_manager.get_stock_info(symbol)
                if stock_info and stock_info.get('company_name'):
                    symbol_data.append({
                        'symbol': symbol,
                        'company_name': stock_info['company_name']
                    })
                else:
                    # Fallback if no company name found
                    symbol_data.append({
                        'symbol': symbol,
                        'company_name': symbol
                    })
            
            logger.info(f"Retrieved {len(symbol_data)} symbols for sector {sector}")
            return symbol_data
        except Exception as e:
            logger.error(f"Failed to get symbols for sector {sector}: {e}")
            return []
    
    def get_symbols_by_industry(self, industry: str, source: str = 'yahoo') -> List[Dict[str, str]]:
        """Get list of symbols with company names for a specific industry."""
        try:
            symbols = self.db_manager.get_stocks_by_industry(industry)
            # Get company names for each symbol
            symbol_data = []
            for symbol in symbols:
                stock_info = self.db_manager.get_stock_info(symbol)
                if stock_info and stock_info.get('company_name'):
                    symbol_data.append({
                        'symbol': symbol,
                        'company_name': stock_info['company_name']
                    })
                else:
                    # Fallback if no company name found
                    symbol_data.append({
                        'symbol': symbol,
                        'company_name': symbol
                    })
            
            logger.info(f"Retrieved {len(symbol_data)} symbols for industry {industry}")
            return symbol_data
        except Exception as e:
            logger.error(f"Failed to get symbols for industry {industry}: {e}")
            return []
    
    def get_market_data(self, symbol: str, days: int = 30, source: str = 'yahoo', hourly: bool = True) -> pd.DataFrame:
        """Get market data for a symbol for the specified number of days."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = self.db_manager.get_market_data(symbol, start_date, end_date, source)
            
            if df.empty:
                logger.warning(f"No data found for {symbol} in the specified date range")
                return pd.DataFrame()
            
            # If hourly data is requested, resample to hourly intervals
            if hourly and not df.empty:
                df = df.set_index('timestamp')
                # Resample to hourly data, taking the last value in each hour
                df_hourly = df.resample('H').agg({
                    'symbol': 'last',
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum',
                    'source': 'last'
                }).dropna()
                df = df_hourly.reset_index()
                logger.info(f"Resampled to {len(df)} hourly records for {symbol}")
            else:
                logger.info(f"Retrieved {len(df)} records for {symbol}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            # Return empty DataFrame with proper columns
            return pd.DataFrame(columns=['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'source'])
    
    def get_all_market_data(self, symbol: str, source: str = 'yahoo', hourly: bool = True) -> pd.DataFrame:
        """Get all available market data for a symbol."""
        try:
            # Get the full date range for this symbol
            start_date, end_date = self.db_manager.get_data_date_range(symbol, source)
            
            if start_date is None or end_date is None:
                logger.warning(f"No data range found for {symbol}")
                return pd.DataFrame()
            
            df = self.db_manager.get_market_data(symbol, start_date, end_date, source)
            
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # If hourly data is requested, resample to hourly intervals
            if hourly and not df.empty:
                df = df.set_index('timestamp')
                # Resample to hourly data, taking the last value in each hour
                df_hourly = df.resample('H').agg({
                    'symbol': 'last',
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum',
                    'source': 'last'
                }).dropna()
                df = df_hourly.reset_index()
                logger.info(f"Resampled to {len(df)} hourly records for {symbol} (all data)")
            else:
                logger.info(f"Retrieved {len(df)} records for {symbol} (all data)")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get all market data for {symbol}: {e}")
            # Return empty DataFrame with proper columns
            return pd.DataFrame(columns=['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'source'])
    
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
            # Get all available data for comprehensive stats
            df = self.get_all_market_data(symbol, source=source, hourly=True)
            
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
    
    def get_chart_data(self, symbol: str, days: int = None, source: str = 'yahoo', hourly: bool = True) -> Dict[str, Any]:
        """Get formatted data for charts."""
        try:
            # If days is None, get all available data
            if days is None:
                df = self.get_all_market_data(symbol, source, hourly=hourly)
            else:
                df = self.get_market_data(symbol, days, source, hourly=hourly)
            
            if df.empty:
                return {
                    'dates': [],
                    'prices': [],
                    'volumes': [],
                    'has_data': False
                }
            
            # Format data for charts with better time formatting for hourly data
            if hourly:
                date_format = '%Y-%m-%d %H:%M'
            else:
                date_format = '%Y-%m-%d'
            
            chart_data = {
                'dates': df['timestamp'].dt.strftime(date_format).tolist(),
                'prices': df['close'].tolist(),
                'volumes': df['volume'].tolist(),
                'has_data': True,
                'symbol': symbol,
                'hourly': hourly
            }
            
            logger.info(f"Prepared chart data for {symbol} ({'hourly' if hourly else 'daily'})")
            return chart_data
            
        except Exception as e:
            logger.error(f"Failed to prepare chart data for {symbol}: {e}")
            return {
                'dates': [],
                'prices': [],
                'volumes': [],
                'has_data': False
            }
    
    def get_recent_signals(self, symbol: str, days: int = None, source: str = 'yahoo') -> List[Dict]:
        """Get recent trading signals based on price movements."""
        try:
            # If days is None, get all available data
            if days is None:
                df = self.get_all_market_data(symbol, source, hourly=True)
            else:
                df = self.get_market_data(symbol, days, source, hourly=True)
            
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
                
                # Format time for hourly data
                time_format = '%Y-%m-%d %H:%M' if len(df) > 24 else '%Y-%m-%d'
                signals.append({
                    'date': current['timestamp'].strftime(time_format),
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
    
    def get_sector_distribution(self) -> Dict[str, Any]:
        """Get sector distribution data for the bar chart."""
        try:
            # Get all sectors from database
            sectors = self.db_manager.get_all_sectors()
            
            if not sectors:
                logger.warning("No sectors found in database, using mock data")
                # Return mock sector data
                return {
                    'sectors': ['Technology', 'Healthcare', 'Finance', 'Consumer', 'Energy'],
                    'counts': [15, 12, 8, 6, 4],
                    'max_sector': 'Technology',
                    'total_stocks': 45,
                    'formatted_date': datetime.now().strftime("%d %b %Y, %I:%M%p")
                }
            
            # Get sector counts
            sector_counts = {}
            for sector in sectors:
                stocks = self.db_manager.get_stocks_by_sector(sector)
                sector_counts[sector] = len(stocks)
            
            # Sort by count descending
            sorted_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)
            sectors_list = [item[0] for item in sorted_sectors]
            counts_list = [item[1] for item in sorted_sectors]
            
            return {
                'sectors': sectors_list,
                'counts': counts_list,
                'max_sector': sectors_list[0] if sectors_list else 'Unknown',
                'total_stocks': sum(counts_list),
                'formatted_date': datetime.now().strftime("%d %b %Y, %I:%M%p")
            }
            
        except Exception as e:
            logger.error(f"Failed to get sector distribution: {e}")
            # Return mock data on error
            return {
                'sectors': ['Technology', 'Healthcare', 'Finance', 'Consumer', 'Energy'],
                'counts': [15, 12, 8, 6, 4],
                'max_sector': 'Technology',
                'total_stocks': 45,
                'formatted_date': datetime.now().strftime("%d %b %Y, %I:%M%p")
            }

    def get_industry_distribution(self, sector: str) -> Dict[str, Any]:
        """Get industry distribution data for a specific sector."""
        try:
            # Get industries for the specified sector
            industries = self.db_manager.get_industries_by_sector(sector)
            
            if not industries:
                logger.warning(f"No industries found for sector {sector}, using mock data")
                # Return mock industry data based on sector
                mock_industries = {
                    'Technology': ['Software', 'Hardware', 'Internet', 'Semiconductors', 'AI/ML'],
                    'Healthcare': ['Pharmaceuticals', 'Biotechnology', 'Medical Devices', 'Healthcare Services'],
                    'Finance': ['Banking', 'Insurance', 'Investment Services', 'Real Estate'],
                    'Consumer': ['Retail', 'Food & Beverage', 'Apparel', 'Entertainment'],
                    'Energy': ['Oil & Gas', 'Renewable Energy', 'Utilities', 'Mining']
                }
                
                industries_list = mock_industries.get(sector, ['Industry 1', 'Industry 2', 'Industry 3'])
                counts_list = [5, 4, 3, 2, 1][:len(industries_list)]
                
                return {
                    'industries': industries_list,
                    'counts': counts_list,
                    'max_industry': industries_list[0] if industries_list else 'Unknown',
                    'total_stocks': sum(counts_list),
                    'sector': sector
                }
            
            # Get industry counts
            industry_counts = {}
            for industry in industries:
                stocks = self.db_manager.get_stocks_by_industry(industry, sector)
                industry_counts[industry] = len(stocks)
            
            # Sort by count descending
            sorted_industries = sorted(industry_counts.items(), key=lambda x: x[1], reverse=True)
            industries_list = [item[0] for item in sorted_industries]
            counts_list = [item[1] for item in sorted_industries]
            
            return {
                'industries': industries_list,
                'counts': counts_list,
                'max_industry': industries_list[0] if industries_list else 'Unknown',
                'total_stocks': sum(counts_list),
                'sector': sector
            }
            
        except Exception as e:
            logger.error(f"Failed to get industry distribution for sector {sector}: {e}")
            # Return mock data on error
            return {
                'industries': ['Industry 1', 'Industry 2', 'Industry 3', 'Industry 4'],
                'counts': [5, 4, 3, 2],
                'max_industry': 'Industry 1',
                'total_stocks': 14,
                'sector': sector
            }

# Global data service instance
data_service = None

def get_data_service() -> MarketDataService:
    """Get the global data service instance."""
    global data_service
    if data_service is None:
        data_service = MarketDataService()
    return data_service 