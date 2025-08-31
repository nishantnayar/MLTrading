"""
Market data service for handling OHLCV data operations.
Manages historical market data, price queries, and data validation.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
from .base_service import BaseDashboardService


class MarketDataService(BaseDashboardService):
    """Service to handle market data operations."""


    def get_market_data(self, symbol: str, days: int = 30, source: str = 'yahoo', hourly: bool = False) -> pd.DataFrame:
        """Get historical market data for a symbol."""
        try:
            if not self.validate_symbol(symbol):
                self.logger.warning(f"Invalid symbol format: {symbol}")
                return pd.DataFrame()

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Get data from database - this returns a DataFrame directly
            df = self.db_manager.get_market_data(symbol.upper(), start_date, end_date, source)

            # If no data found in recent range, try to get any available data
            if df is None or df.empty:
                self.logger.info(f"No recent data for {symbol}, checking for any available data...")
                df = self.get_any_available_data(symbol, source)

            # Ensure df is a DataFrame and handle None case
            if df is None:
                self.logger.warning(f"Database returned None for {symbol}")
                return pd.DataFrame()

            if df.empty:
                self.logger.warning(f"No market data found for {symbol} in last {days} days")
                return pd.DataFrame()

            # Ensure proper column names and types
            if not df.empty:
                expected_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                missing_columns = [col for col in expected_columns if col not in df.columns]

                if missing_columns:
                    self.logger.error(f"Missing columns in market data: {missing_columns}")
                    return pd.DataFrame()

                # Convert numeric columns
                numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # Convert timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                # Sort by timestamp
                df = df.sort_values('timestamp')

                # Log data before cleaning
                original_count = len(df)

                # Only remove rows where essential OHLC data is missing
                # Keep rows with missing volume or other non-essential data
                essential_columns = ['timestamp', 'open', 'high', 'low', 'close']
                df = df.dropna(subset=essential_columns)

                cleaned_count = len(df)
                if original_count != cleaned_count:
                    self.logger.warning(f"Removed {original_count - cleaned_count} rows with missing essential data (kept {cleaned_count}/{original_count})")

                self.logger.info(f"Retrieved {len(df)} market data points for {symbol}")

            return df

        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return pd.DataFrame()


    def get_all_available_data(self, symbol: str, source: str = 'yahoo') -> pd.DataFrame:
        """Get ALL available data for a symbol (no limits)."""
        try:
            # Get ALL records for the symbol
            query = """
                SELECT symbol, timestamp, open, high, low, close, volume, source
                FROM market_data
                WHERE symbol = %s AND source = %s
                ORDER BY timestamp ASC
            """

            conn = self.db_manager.get_connection()
            try:
                df = pd.read_sql_query(query, conn, params=[symbol.upper(), source])
            finally:
                self.db_manager.return_connection(conn)

            if not df.empty:
                # Log data before cleaning
                original_count = len(df)

                # Convert timestamp column
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                # Convert numeric columns and log conversion issues
                numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_columns:
                    if col in df.columns:
                        original_nulls = df[col].isna().sum()
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        new_nulls = df[col].isna().sum()
                        if new_nulls > original_nulls:
                            self.logger.warning(f"Column {col}: {new_nulls - original_nulls} values became null after numeric conversion")

                # Only remove rows where essential OHLC data is missing
                essential_columns = ['timestamp', 'open', 'high', 'low', 'close']
                df = df.dropna(subset=essential_columns)

                cleaned_count = len(df)
                if original_count != cleaned_count:
                    self.logger.warning(f"Removed {original_count - cleaned_count} rows with missing essential data")

                self.logger.info(f"Found ALL {len(df)} records for {symbol} from {df['timestamp'].min()} to {df['timestamp'].max()}")

            return df

        except Exception as e:
            self.logger.error(f"Error getting all available data for {symbol}: {e}")
            return pd.DataFrame()


    def get_any_available_data(self, symbol: str, source: str = 'yahoo') -> pd.DataFrame:
        """Get any available data for a symbol (fallback when no recent data exists)."""
        try:
            # Get the last 200 records regardless of date
            query = """
                SELECT symbol, timestamp, open, high, low, close, volume, source
                FROM market_data
                WHERE symbol = %s AND source = %s
                ORDER BY timestamp DESC
                LIMIT 200
            """

            conn = self.db_manager.get_connection()
            try:
                df = pd.read_sql_query(query, conn, params=[symbol.upper(), source])
            finally:
                self.db_manager.return_connection(conn)

            if not df.empty:
                # Reverse to get chronological order
                df = df.sort_values('timestamp').reset_index(drop=True)

                # Convert timestamp column
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                # Log data before cleaning
                original_count = len(df)

                # Convert numeric columns and log any conversion issues
                numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_columns:
                    if col in df.columns:
                        original_nulls = df[col].isna().sum()
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        new_nulls = df[col].isna().sum()
                        if new_nulls > original_nulls:
                            self.logger.warning(f"Column {col}: {new_nulls - original_nulls} values became null after numeric conversion")

                self.logger.info(f"Found {len(df)} historical records for {symbol} from {df['timestamp'].min()} to {df['timestamp'].max()}")

            return df

        except Exception as e:
            self.logger.error(f"Error getting any available data for {symbol}: {e}")
            return pd.DataFrame()


    def get_latest_price(self, symbol: str, source: str = 'yahoo') -> Optional[Dict[str, Any]]:
        """Get the latest price data for a symbol."""
        try:
            if not self.validate_symbol(symbol):
                self.logger.warning(f"Invalid symbol format: {symbol}")
                return None

            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM market_data
                WHERE symbol = %s AND source = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """

            result = self.execute_query(query, (symbol.upper(), source))

            if not result:
                self.logger.warning(f"No latest price data found for {symbol}")
                return None

            row = result[0]
            price_data = {
                'symbol': symbol.upper(),
                'timestamp': row[0],
                'open': float(row[1]) if row[1] is not None else None,
                'high': float(row[2]) if row[2] is not None else None,
                'low': float(row[3]) if row[3] is not None else None,
                'close': float(row[4]) if row[4] is not None else None,
                'volume': int(row[5]) if row[5] is not None else None
            }

            self.logger.info(f"Retrieved latest price for {symbol}: ${price_data['close']}")
            return price_data

        except Exception as e:
            self.logger.error(f"Error getting latest price for {symbol}: {e}")
            return None


    def get_price_change(self, symbol: str, days: int = 1, source: str = 'yahoo') -> Optional[Dict[str, Any]]:
        """Get price change over specified number of days."""
        try:
            if not self.validate_symbol(symbol):
                return None

            # Get current and previous prices
            current_data = self.get_latest_price(symbol, source)
            if not current_data:
                return None

            # Get price from 'days' ago
            past_date = datetime.now() - timedelta(days=days)

            query = """
                SELECT close
                FROM market_data
                WHERE symbol = %s AND source = %s AND timestamp <= %s
                ORDER BY timestamp DESC
                LIMIT 1
            """

            result = self.execute_query(query, (symbol.upper(), source, past_date))

            if not result:
                self.logger.warning(f"No historical price data found for {symbol}")
                return current_data

            past_close = float(result[0][0])
            current_close = current_data['close']

            if past_close and current_close:
                change = current_close - past_close
                change_percent = (change / past_close) * 100

                price_change_data = {
                    **current_data,
                    'previous_close': past_close,
                    'change': change,
                    'change_percent': change_percent,
                    'period_days': days
                }

                self.logger.info(f"Calculated price change for {symbol}: {change_percent:.2f}%")
                return price_change_data

            return current_data

        except Exception as e:
            self.logger.error(f"Error calculating price change for {symbol}: {e}")
            return None


    def get_data_date_range(self, source: str = 'yahoo') -> str:
        """Get the date range of available data."""
        try:
            query = """
                SELECT MIN(timestamp) as start_date, MAX(timestamp) as end_date
                FROM market_data
                WHERE source = %s
            """

            result = self.execute_query(query, (source,))

            if not result or not result[0][0]:
                return "No data available"

            start_date = result[0][0]
            end_date = result[0][1]

            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            self.logger.info(f"Data date range: {date_range}")

            return date_range

        except Exception as e:
            self.logger.error(f"Error getting data date range: {e}")
            return "Error retrieving date range"


    def get_data_quality_metrics(self, symbol: str, source: str = 'yahoo') -> Dict[str, Any]:
        """Get data quality metrics for a symbol."""
        try:
            if not self.validate_symbol(symbol):
                return {}

            query = """
                SELECT
                    COUNT(*) as total_records,
                    MIN(timestamp) as first_date,
                    MAX(timestamp) as last_date,
                    COUNT(CASE WHEN close IS NULL THEN 1 END) as missing_close,
                    COUNT(CASE WHEN volume IS NULL OR volume = 0 THEN 1 END) as missing_volume,
                    AVG(close) as avg_close,
                    MIN(close) as min_close,
                    MAX(close) as max_close
                FROM market_data
                WHERE symbol = %s AND source = %s
            """

            result = self.execute_query(query, (symbol.upper(), source))

            if not result:
                return {}

            row = result[0]

            quality_metrics = {
                'symbol': symbol.upper(),
                'total_records': row[0] or 0,
                'first_date': row[1],
                'last_date': row[2],
                'missing_close': row[3] or 0,
                'missing_volume': row[4] or 0,
                'avg_close': float(row[5]) if row[5] else 0,
                'min_close': float(row[6]) if row[6] else 0,
                'max_close': float(row[7]) if row[7] else 0,
                'data_completeness': ((row[0] - (row[3] or 0)) / row[0] * 100) if row[0] > 0 else 0
            }

            self.logger.info(f"Retrieved data quality metrics for {symbol}")
            return quality_metrics

        except Exception as e:
            self.logger.error(f"Error getting data quality metrics for {symbol}: {e}")
            return {}


    def get_available_symbols(self, source: str = 'yahoo') -> List[Dict[str, str]]:
        """Get list of available symbols with market data and company names."""
        try:
            query = """
                SELECT DISTINCT s.symbol, COALESCE(si.company_name, s.symbol) as company_name
                FROM (
                    SELECT DISTINCT symbol FROM market_data WHERE source = %s
                ) s
                LEFT JOIN stock_info si ON s.symbol = si.symbol
                ORDER BY s.symbol
            """

            results = self.execute_query(query, (source,))

            if not results:
                self.logger.warning("No symbols found with market data")
                return []

            symbol_data = [
                {
                    'symbol': row[0],
                    'company_name': row[1]
                }
                for row in results
            ]

            self.logger.info(f"Retrieved {len(symbol_data)} symbols with company names")
            return symbol_data

        except Exception as e:
            self.logger.error(f"Error getting available symbols: {e}")
            return []


    def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search symbols by symbol or company name."""
        try:
            if not query or len(query) < 2:
                return []

            search_query = """
                SELECT DISTINCT s.symbol, s.company_name
                FROM stock_info s
                INNER JOIN market_data md ON s.symbol = md.symbol
                WHERE (
                    s.symbol ILIKE %s OR
                    s.company_name ILIKE %s
                )
                ORDER BY
                    CASE WHEN s.symbol ILIKE %s THEN 1 ELSE 2 END,
                    s.symbol
                LIMIT %s
            """

            search_pattern = f"%{query}%"
            exact_pattern = f"{query}%"

            results = self.execute_query(
                search_query,
                (search_pattern, search_pattern, exact_pattern, limit)
            )

            if not results:
                return []

            symbol_data = [
                {
                    'symbol': row[0],
                    'company_name': row[1] or row[0]
                }
                for row in results
            ]

            self.logger.info(f"Found {len(symbol_data)} symbols for search: '{query}'")
            return symbol_data

        except Exception as e:
            self.logger.error(f"Error searching symbols with query '{query}': {e}")
            return []


    def validate_market_data(self, data: List[Dict]) -> bool:
        """Validate market data format and completeness."""
        try:
            if not data:
                return False

            required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

            for record in data[:5]:  # Check first 5 records
                # Check required fields exist
                if not all(field in record for field in required_fields):
                    self.logger.error("Missing required fields in market data")
                    return False

                # Validate OHLC relationships
                o, h, l, c = record['open'], record['high'], record['low'], record['close']
                if o and h and l and c:
                    if not (l <= o <= h and l <= c <= h):
                        self.logger.error("Invalid OHLC relationship in market data")
                        return False

                # Validate volume is non-negative
                if record['volume'] and record['volume'] < 0:
                    self.logger.error("Negative volume in market data")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating market data: {e}")
            return False

