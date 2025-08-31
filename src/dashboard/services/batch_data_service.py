"""
Batch data service for optimized multi-symbol data retrieval.
Eliminates N+1 query patterns with bulk operations.
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import pandas as pd
from .base_service import BaseDashboardService
from .cache_service import cached


class BatchDataService(BaseDashboardService):
    """Service for efficient batch data operations."""

    @cached(ttl=180, key_func=lambda self, symbols, days=30, source='yahoo': f"batch_market_{len(symbols)}_{days}_{source}")
    def get_batch_market_data(self, symbols: List[str], days: int = 30, source: str = 'yahoo') -> Dict[str, pd.DataFrame]:
        """
        Get market data for multiple symbols in a single query.

        Args:
            symbols: List of stock symbols
            days: Number of days of data to retrieve
            source: Data source

        Returns:
            Dict mapping symbol to DataFrame of market data
        """
        try:
            if not symbols:
                return {}

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Create parameterized query for batch retrieval
            symbol_placeholders = ','.join(['%s'] * len(symbols))
            query = f"""
                SELECT symbol, timestamp, open, high, low, close, volume, source
                FROM market_data
                WHERE symbol IN ({symbol_placeholders})
                AND timestamp BETWEEN %s AND %s
                AND source = %s
                ORDER BY symbol, timestamp
            """

            params = tuple(symbols) + (start_date, end_date, source)
            results = self.execute_query(query, params)

            if not results:
                self.logger.warning(f"No batch market data found for {len(symbols)} symbols")
                return {}

            # Group results by symbol
            symbol_data = {}
            for row in results:
                symbol = row[0]
                if symbol not in symbol_data:
                    symbol_data[symbol] = []

                symbol_data[symbol].append({
                    'symbol': row[0],
                    'timestamp': row[1],
                    'open': row[2],
                    'high': row[3],
                    'low': row[4],
                    'close': row[5],
                    'volume': row[6],
                    'source': row[7]
                })

            # Convert to DataFrames
            result = {}
            for symbol, data in symbol_data.items():
                if data:
                    df = pd.DataFrame(data)
                    # Ensure proper data types
                    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                    original_count = len(df)
                    for col in numeric_columns:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    df['timestamp'] = pd.to_datetime(df['timestamp'])

                    # Only drop rows with missing essential OHLC data
                    essential_columns = ['timestamp', 'open', 'high', 'low', 'close']
                    df = df.sort_values('timestamp').dropna(subset=essential_columns)

                    cleaned_count = len(df)
                    if original_count != cleaned_count:
                        self.logger.warning(f"Symbol {symbol}: Removed {original_count - cleaned_count} rows with missing essential data")

                    result[symbol] = df

            self.logger.info(f"Retrieved batch market data for {len(result)} symbols with {sum(len(df) for df in result.values())} total records")
            return result

        except Exception as e:
            self.logger.error(f"Error getting batch market data: {e}")
            return {}

    @cached(ttl=300, key_func=lambda self, symbols, source='yahoo': f"batch_info_{len(symbols)}_{source}")
    def get_batch_stock_info(self, symbols: List[str], source: str = 'yahoo') -> Dict[str, Dict[str, Any]]:
        """
        Get stock info for multiple symbols in a single query.

        Args:
            symbols: List of stock symbols
            source: Data source

        Returns:
            Dict mapping symbol to stock info
        """
        try:
            if not symbols:
                return {}

            # Create parameterized query for batch retrieval
            symbol_placeholders = ','.join(['%s'] * len(symbols))
            query = f"""
                SELECT symbol, company_name, sector, industry, market_cap,
                       country, currency, exchange, source, created_at, updated_at
                FROM stock_info
                WHERE symbol IN ({symbol_placeholders})
            """

            results = self.execute_query(query, tuple(symbols))

            if not results:
                self.logger.warning(f"No batch stock info found for {len(symbols)} symbols")
                return {}

            # Convert results to dict
            stock_info = {}
            for row in results:
                stock_info[row[0]] = {
                    'symbol': row[0],
                    'company_name': row[1],
                    'sector': row[2],
                    'industry': row[3],
                    'market_cap': row[4],
                    'country': row[5],
                    'currency': row[6],
                    'exchange': row[7],
                    'source': row[8],
                    'created_at': row[9],
                    'updated_at': row[10]
                }

            self.logger.info(f"Retrieved batch stock info for {len(stock_info)} symbols")
            return stock_info

        except Exception as e:
            self.logger.error(f"Error getting batch stock info: {e}")
            return {}

    def get_batch_latest_prices(self, symbols: List[str], source: str = 'yahoo') -> Dict[str, Dict[str, Any]]:
        """
        Get latest prices for multiple symbols in a single query.

        Args:
            symbols: List of stock symbols
            source: Data source

        Returns:
            Dict mapping symbol to latest price data
        """
        try:
            if not symbols:
                return {}

            # Use window function to get latest price for each symbol efficiently
            symbol_placeholders = ','.join(['%s'] * len(symbols))
            query = f"""
                WITH latest_data AS (
                    SELECT symbol, timestamp, open, high, low, close, volume,
                           ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) as rn
                    FROM market_data
                    WHERE symbol IN ({symbol_placeholders}) AND source = %s
                )
                SELECT symbol, timestamp, open, high, low, close, volume
                FROM latest_data
                WHERE rn = 1
                ORDER BY symbol
            """

            params = tuple(symbols) + (source,)
            results = self.execute_query(query, params)

            if not results:
                self.logger.warning(f"No latest prices found for {len(symbols)} symbols")
                return {}

            # Convert results to dict
            latest_prices = {}
            for row in results:
                latest_prices[row[0]] = {
                    'symbol': row[0],
                    'timestamp': row[1],
                    'open': float(row[2]) if row[2] is not None else None,
                    'high': float(row[3]) if row[3] is not None else None,
                    'low': float(row[4]) if row[4] is not None else None,
                    'close': float(row[5]) if row[5] is not None else None,
                    'volume': int(row[6]) if row[6] is not None else None
                }

            self.logger.info(f"Retrieved latest prices for {len(latest_prices)} symbols")
            return latest_prices

        except Exception as e:
            self.logger.error(f"Error getting batch latest prices: {e}")
            return {}

    def preload_dashboard_data(self, source: str = 'yahoo') -> Dict[str, Any]:
        """
        Preload all commonly used dashboard data in optimized batch queries.

        Returns:
            Dict containing all preloaded data
        """
        try:
            self.logger.info("Starting dashboard data preload...")

            # Get all symbols in single query
            symbols_query = "SELECT DISTINCT symbol FROM market_data WHERE source = %s ORDER BY symbol"
            symbol_results = self.execute_query(symbols_query, (source,))
            symbols = [row[0] for row in symbol_results]

            if not symbols:
                self.logger.warning("No symbols found for preload")
                return {}

            # Batch load data
            preloaded_data = {
                'symbols': symbols,
                'market_data': self.get_batch_market_data(symbols[:50], days=30, source=source),  # Limit to top 50 for performance
                'stock_info': self.get_batch_stock_info(symbols, source=source),
                'latest_prices': self.get_batch_latest_prices(symbols, source=source)
            }

            # Add aggregated statistics
            stats_query = """
                SELECT
                    COUNT(DISTINCT symbol) as total_symbols,
                    COUNT(*) as total_records,
                    MIN(timestamp) as earliest_date,
                    MAX(timestamp) as latest_date
                FROM market_data
                WHERE source = %s
            """
            stats_results = self.execute_query(stats_query, (source,))

            if stats_results:
                preloaded_data['statistics'] = {
                    'total_symbols': stats_results[0][0],
                    'total_records': stats_results[0][1],
                    'earliest_date': stats_results[0][2],
                    'latest_date': stats_results[0][3]
                }

            self.logger.info(f"Preloaded dashboard data for {len(symbols)} symbols")
            return preloaded_data

        except Exception as e:
            self.logger.error(f"Error preloading dashboard data: {e}")
            return {}
