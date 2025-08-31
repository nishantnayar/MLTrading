"""
Optimized Feature Data Service with performance improvements for feature_engineered_data queries.
Addresses slow queries, reduces memory usage, and improves caching strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from .base_service import BaseDashboardService
from .cache_service import cached


class OptimizedFeatureDataService(BaseDashboardService):
    """
    High-performance feature data service with optimized queries and caching.

    Key Optimizations:
    1. Selective column retrieval (avoid SELECT *)
    2. Optimized WHERE clauses matching new indexes
    3. Intelligent query batching
    4. Enhanced caching with feature-specific TTLs
    5. Lazy loading for expensive features
    """

    def __init__(self):
        super().__init__()
        self.logger.info("OptimizedFeatureDataService initialized with performance enhancements")

        # Define column sets for selective querying
        self.CORE_COLUMNS = [
            'symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'returns', 'feature_version'
        ]

        self.TECHNICAL_COLUMNS = [
            'rsi_1d', 'price_ma_short', 'price_ma_med', 'price_ma_long',
            'bb_upper', 'bb_lower', 'bb_position', 'macd', 'macd_signal',
            'atr', 'williams_r'
        ]

        self.ADVANCED_COLUMNS = [
            'realized_vol_short', 'volume_ratio', 'mfi', 'vpt_normalized',
            'returns_lag_1', 'returns_lag_24', 'price_momentum_24h'
        ]

    @cached(ttl=300, key_func=lambda self, symbol, days: f"core_features_{symbol}_{days}")
    def get_core_features(self, symbol: str, days: int = 30, feature_version: str = '3.0') -> pd.DataFrame:
        """
        Get core OHLCV + basic features with optimized query.
        Uses covering index to avoid table lookups.
        """
        try:
            columns = ', '.join(self.CORE_COLUMNS)
            query = f"""
                SELECT {columns}
                FROM feature_engineered_data
                WHERE symbol = %s
                AND feature_version = %s
                AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """

            result = self.execute_query(query, (symbol, feature_version, days))

            if not result:
                return pd.DataFrame()

            df = pd.DataFrame(result, columns=self.CORE_COLUMNS)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            self.logger.debug(f"Retrieved {len(df)} core feature records for {symbol}")
            return df

        except Exception as e:
            self.logger.error(f"Error retrieving core features for {symbol}: {e}")
            return pd.DataFrame()

    @cached(ttl=600, key_func=lambda self, symbol, days: f"technical_features_{symbol}_{days}")
    def get_technical_features(self, symbol: str, days: int = 30, feature_version: str = '3.0') -> pd.DataFrame:
        """
        Get technical indicators with optimized query.
        Separate from core features for better cache management.
        """
        try:
            columns = ['symbol', 'timestamp'] + self.TECHNICAL_COLUMNS
            columns_str = ', '.join(columns)

            query = f"""
                SELECT {columns_str}
                FROM feature_engineered_data
                WHERE symbol = %s
                AND feature_version = %s
                AND timestamp >= NOW() - INTERVAL '%s days'
                AND rsi_1d IS NOT NULL  -- Use index condition
                ORDER BY timestamp ASC
            """

            result = self.execute_query(query, (symbol, feature_version, days))

            if not result:
                return pd.DataFrame()

            df = pd.DataFrame(result, columns=columns)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            self.logger.debug(f"Retrieved {len(df)} technical feature records for {symbol}")
            return df

        except Exception as e:
            self.logger.error(f"Error retrieving technical features for {symbol}: {e}")
            return pd.DataFrame()

    @cached(ttl=900, key_func=lambda self, symbol, days: f"advanced_features_{symbol}_{days}")
    def get_advanced_features(self, symbol: str, days: int = 30, feature_version: str = '3.0') -> pd.DataFrame:
        """
        Get advanced ML features (lagged, rolling stats) with longer cache TTL.
        These change less frequently than technical indicators.
        """
        try:
            # Build advanced columns dynamically
            lagged_cols = [f'{feat}_lag_{lag}' for feat in ['returns', 'vol', 'volume_ratio']
                          for lag in [1, 2, 4, 8, 24]]
            rolling_cols = [f'returns_{stat}_{window}h' for stat in ['mean', 'std', 'skew', 'kurt']
                           for window in [6, 12, 24]]

            columns = ['symbol', 'timestamp'] + self.ADVANCED_COLUMNS + lagged_cols + rolling_cols
            columns_str = ', '.join(columns)

            query = f"""
                SELECT {columns_str}
                FROM feature_engineered_data
                WHERE symbol = %s
                AND feature_version = %s
                AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """

            result = self.execute_query(query, (symbol, feature_version, days))

            if not result:
                return pd.DataFrame()

            df = pd.DataFrame(result, columns=columns)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            self.logger.debug(f"Retrieved {len(df)} advanced feature records for {symbol}")
            return df

        except Exception as e:
            self.logger.error(f"Error retrieving advanced features for {symbol}: {e}")
            return pd.DataFrame()

    def get_feature_data_optimized(self, symbol: str, days: int = 30,
                                 include_advanced: bool = False) -> pd.DataFrame:
        """
        Get comprehensive feature data with intelligent loading.
        Combines core + technical features by default, loads advanced on demand.
        """
        try:
            # Get core data (always needed)
            core_df = self.get_core_features(symbol, days)
            if core_df.empty:
                return pd.DataFrame()

            # Get technical indicators
            technical_df = self.get_technical_features(symbol, days)

            # Merge core and technical
            if not technical_df.empty:
                df = pd.merge(core_df, technical_df, on=['symbol', 'timestamp'], how='left')
            else:
                df = core_df

            # Optionally include advanced features (for ML training)
            if include_advanced:
                advanced_df = self.get_advanced_features(symbol, days)
                if not advanced_df.empty:
                    df = pd.merge(df, advanced_df, on=['symbol', 'timestamp'], how='left')

            self.logger.info(f"Retrieved optimized feature data for {symbol}: {len(df)} records")
            return df

        except Exception as e:
            self.logger.error(f"Error retrieving optimized feature data for {symbol}: {e}")
            return pd.DataFrame()

    @cached(ttl=1800, key_func=lambda self, symbols: f"batch_latest_{hash(tuple(sorted(symbols)))}")
    def get_latest_features_batch(self, symbols: List[str], feature_version: str = '3.0') -> pd.DataFrame:
        """
        Efficiently get latest features for multiple symbols.
        Uses batch query with optimized indexes.
        """
        try:
            if not symbols:
                return pd.DataFrame()

            # Create parameterized query for batch processing
            symbol_placeholders = ','.join(['%s'] * len(symbols))

            core_columns = ', '.join(self.CORE_COLUMNS + self.TECHNICAL_COLUMNS)

            query = f"""
                WITH latest_features AS (
                    SELECT {core_columns},
                           ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) as rn
                    FROM feature_engineered_data
                    WHERE symbol IN ({symbol_placeholders})
                    AND feature_version = %s
                    AND timestamp >= NOW() - INTERVAL '7 days'
                    AND rsi_1d IS NOT NULL
                )
                SELECT {core_columns}
                FROM latest_features
                WHERE rn = 1
                ORDER BY symbol
            """

            params = symbols + [feature_version]
            result = self.execute_query(query, params)

            if not result:
                return pd.DataFrame()

            columns = self.CORE_COLUMNS + self.TECHNICAL_COLUMNS
            df = pd.DataFrame(result, columns=columns)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            self.logger.info(f"Retrieved latest features for {len(df)} symbols")
            return df

        except Exception as e:
            self.logger.error(f"Error retrieving batch latest features: {e}")
            return pd.DataFrame()

    @cached(ttl=3600, key_func=lambda self: "feature_summary")
    def get_feature_summary_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive feature table statistics using materialized view.
        Updated hourly for dashboard health monitoring.
        """
        try:
            # Use materialized view if available, fallback to direct query
            query = """
                SELECT
                    symbol,
                    total_records,
                    latest_timestamp,
                    latest_version,
                    rsi_coverage,
                    ma_coverage
                FROM mv_features_dashboard_summary
                ORDER BY latest_timestamp DESC
                LIMIT 100
            """

            result = self.execute_query(query, ())

            if not result:
                # Fallback to direct query if materialized view doesn't exist
                return self._get_feature_summary_fallback()

            summary_data = []
            for row in result:
                summary_data.append({
                    'symbol': row[0],
                    'total_records': row[1],
                    'latest_timestamp': row[2],
                    'latest_version': row[3],
                    'rsi_coverage': float(row[4]) if row[4] else 0.0,
                    'ma_coverage': float(row[5]) if row[5] else 0.0
                })

            return {
                'total_symbols': len(summary_data),
                'symbols': summary_data,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting feature summary stats: {e}")
            return self._get_feature_summary_fallback()

    def _get_feature_summary_fallback(self) -> Dict[str, Any]:
        """Fallback summary stats when materialized view unavailable"""
        try:
            query = """
                SELECT
                    COUNT(DISTINCT symbol) as total_symbols,
                    COUNT(*) as total_records,
                    MAX(timestamp) as latest_timestamp,
                    MIN(timestamp) as earliest_timestamp
                FROM feature_engineered_data
                WHERE timestamp >= NOW() - INTERVAL '7 days'
            """

            result = self.execute_query(query, ())
            if result:
                row = result[0]
                return {
                    'total_symbols': row[0],
                    'total_records': row[1],
                    'latest_timestamp': row[2].isoformat() if row[2] else None,
                    'earliest_timestamp': row[3].isoformat() if row[3] else None,
                    'last_updated': datetime.now().isoformat()
                }
            return {}

        except Exception as e:
            self.logger.error(f"Error in fallback summary stats: {e}")
            return {}

    # Optimized versions of existing methods
    def get_moving_averages_optimized(self, symbol: str, days: int = 30) -> Dict[str, pd.Series]:
        """Optimized moving averages using selective column query"""
        df = self.get_technical_features(symbol, days)
        if df.empty:
            return {}

        return {
            'sma_short': df['price_ma_short'],
            'sma_med': df['price_ma_med'],
            'sma_long': df['price_ma_long']
        }

    def get_rsi_data_optimized(self, symbol: str, days: int = 30) -> Dict[str, pd.Series]:
        """Optimized RSI data using technical features cache"""
        df = self.get_technical_features(symbol, days)
        if df.empty:
            return {}

        return {
            'rsi_14': df['rsi_1d'],
            'timestamp': df['timestamp']
        }

    def invalidate_symbol_cache(self, symbol: str):
        """Invalidate all cached data for a symbol (useful after data updates)"""
        cache_keys = [
            f"core_features_{symbol}_30",
            f"technical_features_{symbol}_30",
            f"advanced_features_{symbol}_30"
        ]

        # Note: Actual cache invalidation would depend on cache implementation
        self.logger.info(f"Cache invalidation requested for {symbol}")
