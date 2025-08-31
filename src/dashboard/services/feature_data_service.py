"""
Feature Data Service for retrieving pre-calculated technical indicators from database.
Replaces real-time calculations with efficient database queries for comprehensive features.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from .base_service import BaseDashboardService
from .cache_service import cached


class FeatureDataService(BaseDashboardService):
    """
    Service for retrieving pre-calculated feature engineering data from database.

    This service leverages the comprehensive feature engineering pipeline that
    calculates 90+ technical indicators and stores them in the feature_engineered_data table.

    Benefits over real-time calculation:
    - Much faster performance (database query vs calculation)
    - Consistent across entire system
    - Validated and cleaned data
    - Access to advanced features not available in UI calculations
    """


    def __init__(self):
        super().__init__()
        self.logger.info("FeatureDataService initialized - using pre-calculated features from database")

    @cached(ttl=120, key_func=lambda self, symbol, days: f"features_{symbol}_{days}")


    def get_feature_data(self, symbol: str, days: int = 30, feature_version: str = '3.0') -> pd.DataFrame:
        """
        Get comprehensive feature data for a symbol from the database.

        Args:
            symbol: Stock symbol
            days: Number of days of data to retrieve
            feature_version: Feature version ('3.0' for comprehensive features)

        Returns:
            DataFrame with all pre-calculated features
        """
        try:
            query = """
                SELECT *
                FROM feature_engineered_data
                WHERE symbol = %s
                AND feature_version = %s
                AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """

            result = self.execute_query(query, (symbol, feature_version, days))

            if not result:
                self.logger.warning(f"No feature data found for {symbol} (version {feature_version})")
                return pd.DataFrame()

            # Convert to DataFrame
            # Get column names from query result
            columns = ['id', 'symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume',
                      'returns', 'log_returns', 'high_low_pct', 'open_close_pct', 'price_acceleration', 'returns_sign',
                      'returns_squared', 'realized_vol_short', 'realized_vol_med', 'realized_vol_long', 'gk_volatility', 'vol_of_vol',
                      'price_ma_short', 'price_ma_med', 'price_ma_long', 'price_to_ma_short', 'price_to_ma_med', 'price_to_ma_long',
                      'ma_short_to_med', 'ma_med_to_long', 'volume_ma', 'volume_ratio', 'log_volume', 'vpt', 'vpt_ma', 'vpt_normalized', 'mfi',
                      'rsi_1d', 'rsi_3d', 'rsi_1w', 'rsi_2w', 'rsi_ema', 'hour', 'day_of_week', 'date', 'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
                      'is_market_open', 'is_morning', 'is_afternoon', 'hours_since_open', 'hours_to_close', 'returns_from_daily_open',
                      'intraday_high', 'intraday_low', 'intraday_range_pct', 'position_in_range', 'overnight_gap', 'dist_from_intraday_high', 'dist_from_intraday_low',
                      'returns_lag_1', 'vol_lag_1', 'volume_ratio_lag_1', 'returns_lag_2', 'vol_lag_2', 'volume_ratio_lag_2',
                      'returns_lag_4', 'vol_lag_4', 'volume_ratio_lag_4', 'returns_lag_8', 'vol_lag_8', 'volume_ratio_lag_8',
                      'returns_lag_24', 'vol_lag_24', 'volume_ratio_lag_24', 'returns_mean_6h', 'returns_std_6h', 'returns_skew_6h', 'returns_kurt_6h', 'price_momentum_6h',
                      'returns_mean_12h', 'returns_std_12h', 'returns_skew_12h', 'returns_kurt_12h', 'price_momentum_12h',
                      'returns_mean_24h', 'returns_std_24h', 'returns_skew_24h', 'returns_kurt_24h', 'price_momentum_24h',
                      'bb_upper', 'bb_lower', 'bb_position', 'bb_squeeze', 'macd', 'macd_signal', 'macd_histogram', 'macd_normalized',
                      'atr', 'atr_normalized', 'williams_r', 'source', 'feature_version', 'created_at', 'updated_at',
                      'vol_ratio_short_med', 'vol_ratio_med_long']

            # Use only the number of columns returned by the query
            if result and len(result[0]) < len(columns):
                columns = columns[:len(result[0])]

            df = pd.DataFrame(result, columns=columns)

            # Convert timestamp to datetime and reset index to make it a column
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            self.logger.info(f"Retrieved {len(df)} feature records for {symbol}")
            return df

        except Exception as e:
            self.logger.error(f"Error retrieving feature data for {symbol}: {e}")
            return pd.DataFrame()


    def get_moving_averages(self, symbol: str, days: int = 30) -> Dict[str, pd.Series]:
        """
        Get pre-calculated moving averages from database.

        Returns:
            Dict with 'sma_short' (24h), 'sma_med' (120h), 'sma_long' (480h) and ratios
        """
        try:
            df = self.get_feature_data(symbol, days)

            if df.empty:
                return {}

            return {
                'sma_short': df['price_ma_short'],
                'sma_med': df['price_ma_med'],
                'sma_long': df['price_ma_long'],
                'price_to_ma_short': df['price_to_ma_short'],
                'price_to_ma_med': df['price_to_ma_med'],
                'price_to_ma_long': df['price_to_ma_long'],
                'ma_short_to_med': df['ma_short_to_med'],
                'ma_med_to_long': df['ma_med_to_long']
            }

        except Exception as e:
            self.logger.error(f"Error getting moving averages for {symbol}: {e}")
            return {}


    def get_bollinger_bands(self, symbol: str, days: int = 30) -> Dict[str, pd.Series]:
        """
        Get pre-calculated Bollinger Bands from database.

        Returns:
            Dict with 'middle', 'upper', 'lower', 'position', 'squeeze'
        """
        try:
            df = self.get_feature_data(symbol, days)

            if df.empty:
                return {}

            return {
                'middle': df['price_ma_short'],  # Uses short MA as middle band
                'upper': df['bb_upper'],
                'lower': df['bb_lower'],
                'position': df['bb_position'],
                'squeeze': df['bb_squeeze']
            }

        except Exception as e:
            self.logger.error(f"Error getting Bollinger Bands for {symbol}: {e}")
            return {}


    def get_rsi_data(self, symbol: str, days: int = 30) -> Dict[str, pd.Series]:
        """
        Get pre-calculated RSI data from database.

        Returns:
            Dict with multiple RSI timeframes: '1d', '3d', '1w', '2w', 'ema'
        """
        try:
            df = self.get_feature_data(symbol, days)

            if df.empty:
                return {}

            return {
                '1d': df['rsi_1d'],
                '3d': df['rsi_3d'],
                '1w': df['rsi_1w'],
                '2w': df['rsi_2w'],
                'ema': df['rsi_ema'],
                # Default 14-period equivalent to 1d for UI compatibility
                'rsi_14': df['rsi_1d']
            }

        except Exception as e:
            self.logger.error(f"Error getting RSI data for {symbol}: {e}")
            return {}


    def get_macd_data(self, symbol: str, days: int = 30) -> Dict[str, pd.Series]:
        """
        Get pre-calculated MACD data from database.

        Returns:
            Dict with 'macd', 'signal', 'histogram', 'normalized'
        """
        try:
            df = self.get_feature_data(symbol, days)

            if df.empty:
                return {}

            return {
                'macd': df['macd'],
                'signal': df['macd_signal'],
                'histogram': df['macd_histogram'],
                'normalized': df['macd_normalized']
            }

        except Exception as e:
            self.logger.error(f"Error getting MACD data for {symbol}: {e}")
            return {}


    def get_volatility_data(self, symbol: str, days: int = 30) -> Dict[str, pd.Series]:
        """
        Get comprehensive volatility data from database.

        Returns:
            Dict with various volatility measures and ATR
        """
        try:
            df = self.get_feature_data(symbol, days)

            if df.empty:
                return {}

            return {
                'atr': df['atr'],
                'atr_normalized': df['atr_normalized'],
                'realized_vol_short': df['realized_vol_short'],
                'realized_vol_med': df['realized_vol_med'],
                'realized_vol_long': df['realized_vol_long'],
                'gk_volatility': df['gk_volatility'],
                'vol_of_vol': df['vol_of_vol'],
                'vol_ratio_short_med': df['vol_ratio_short_med'],
                'vol_ratio_med_long': df['vol_ratio_med_long'],
                'returns_squared': df['returns_squared']
            }

        except Exception as e:
            self.logger.error(f"Error getting volatility data for {symbol}: {e}")
            return {}


    def get_volume_data(self, symbol: str, days: int = 30) -> Dict[str, pd.Series]:
        """
        Get comprehensive volume data from database.

        Returns:
            Dict with volume indicators including VPT and MFI
        """
        try:
            df = self.get_feature_data(symbol, days)

            if df.empty:
                return {}

            return {
                'volume_ma': df['volume_ma'],
                'volume_ratio': df['volume_ratio'],
                'log_volume': df['log_volume'],
                'vpt': df['vpt'],
                'vpt_ma': df['vpt_ma'],
                'vpt_normalized': df['vpt_normalized'],
                'mfi': df['mfi']
            }

        except Exception as e:
            self.logger.error(f"Error getting volume data for {symbol}: {e}")
            return {}


    def get_advanced_features(self, symbol: str, days: int = 30) -> Dict[str, pd.Series]:
        """
        Get advanced feature data including lagged features, rolling stats, and intraday.

        Returns:
            Dict with advanced features not available in traditional UI calculations
        """
        try:
            df = self.get_feature_data(symbol, days)

            if df.empty:
                return {}

            # Intraday features
            intraday_features = {
                'returns_from_daily_open': df['returns_from_daily_open'],
                'intraday_range_pct': df['intraday_range_pct'],
                'position_in_range': df['position_in_range'],
                'overnight_gap': df['overnight_gap'],
                'dist_from_intraday_high': df['dist_from_intraday_high'],
                'dist_from_intraday_low': df['dist_from_intraday_low']
            }

            # Lagged features (returns, volatility, volume)
            lagged_features = {}
            for lag in [1, 2, 4, 8, 24]:
                lagged_features[f'returns_lag_{lag}'] = df[f'returns_lag_{lag}']
                lagged_features[f'vol_lag_{lag}'] = df[f'vol_lag_{lag}']
                lagged_features[f'volume_ratio_lag_{lag}'] = df[f'volume_ratio_lag_{lag}']

            # Rolling statistics
            rolling_features = {}
            for window in [6, 12, 24]:
                rolling_features[f'returns_mean_{window}h'] = df[f'returns_mean_{window}h']
                rolling_features[f'returns_std_{window}h'] = df[f'returns_std_{window}h']
                rolling_features[f'returns_skew_{window}h'] = df[f'returns_skew_{window}h']
                rolling_features[f'returns_kurt_{window}h'] = df[f'returns_kurt_{window}h']
                rolling_features[f'price_momentum_{window}h'] = df[f'price_momentum_{window}h']

            # Combine all advanced features
            advanced_features = {**intraday_features, **lagged_features, **rolling_features}

            return advanced_features

        except Exception as e:
            self.logger.error(f"Error getting advanced features for {symbol}: {e}")
            return {}


    def get_all_indicators_from_db(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        Get all available pre-calculated indicators from database.

        This replaces the calculate_all_indicators method in TechnicalIndicatorService
        with much faster database queries.

        Returns:
            Comprehensive dict with all available indicators and features
        """
        try:
            df = self.get_feature_data(symbol, days)

            if df.empty:
                self.logger.warning(f"No feature data available for {symbol}")
                return {}

            # Organize indicators by category for UI compatibility
            indicators = {
                # Moving Averages (compatible with existing UI)
                'sma_20': df['price_ma_short'],
                'sma_50': df['price_ma_med'],
                'sma_200': df['price_ma_long'],
                'ema_12': df['price_ma_short'],  # Map to available data
                'ema_26': df['price_ma_med'],

                # Bollinger Bands
                'bollinger': {
                    'middle': df['price_ma_short'],
                    'upper': df['bb_upper'],
                    'lower': df['bb_lower'],
                    'position': df['bb_position'],
                    'squeeze': df['bb_squeeze']
                },

                # RSI (multiple timeframes available)
                'rsi': df['rsi_1d'],  # Primary RSI for compatibility
                'rsi_multi': {
                    '1d': df['rsi_1d'],
                    '3d': df['rsi_3d'],
                    '1w': df['rsi_1w'],
                    '2w': df['rsi_2w'],
                    'ema': df['rsi_ema']
                },

                # MACD
                'macd': {
                    'macd': df['macd'],
                    'signal': df['macd_signal'],
                    'histogram': df['macd_histogram'],
                    'normalized': df['macd_normalized']
                },

                # Volatility (much more comprehensive than UI calculations)
                'atr': df['atr'],
                'volatility': {
                    'atr': df['atr'],
                    'atr_normalized': df['atr_normalized'],
                    'realized_vol_short': df['realized_vol_short'],
                    'realized_vol_med': df['realized_vol_med'],
                    'realized_vol_long': df['realized_vol_long'],
                    'gk_volatility': df['gk_volatility'],
                    'vol_of_vol': df['vol_of_vol']
                },

                # Volume (comprehensive)
                'volume_sma': df['volume_ma'],
                'volume': {
                    'volume_ma': df['volume_ma'],
                    'volume_ratio': df['volume_ratio'],
                    'vpt': df['vpt'],
                    'mfi': df['mfi']
                },

                # Advanced features not available in traditional UI
                'advanced': self.get_advanced_features(symbol, days)
            }

            self.logger.info(f"Retrieved comprehensive indicators for {symbol}: {len(df)} records")
            return indicators

        except Exception as e:
            self.logger.error(f"Error getting all indicators for {symbol}: {e}")
            return {}


    def get_feature_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata about available features and their descriptions.

        Returns:
            Dict with feature names, types, descriptions, and UI display info
        """
        return {
            # Core OHLCV
            'ohlcv': {
                'features': ['open', 'high', 'low', 'close', 'volume'],
                'description': 'Basic OHLCV market data',
                'type': 'price_data'
            },

            # Phase 1 - Foundation Features
            'foundation': {
                'features': ['returns', 'log_returns', 'high_low_pct', 'open_close_pct',
                           'price_acceleration', 'returns_sign'],
                'description': 'Basic price-derived features',
                'type': 'foundation'
            },

            # Phase 2 - Core Technical
            'moving_averages': {
                'features': ['price_ma_short', 'price_ma_med', 'price_ma_long',
                           'price_to_ma_short', 'price_to_ma_med', 'price_to_ma_long'],
                'description': 'Moving averages and ratios (24h, 120h, 480h windows)',
                'type': 'overlay'
            },

            'technical_indicators': {
                'features': ['bb_upper', 'bb_lower', 'bb_position', 'bb_squeeze',
                           'macd', 'macd_signal', 'macd_histogram', 'atr', 'williams_r'],
                'description': 'Classic technical indicators',
                'type': 'technical'
            },

            'volatility': {
                'features': ['realized_vol_short', 'realized_vol_med', 'realized_vol_long',
                           'gk_volatility', 'vol_of_vol', 'returns_squared'],
                'description': 'Comprehensive volatility measures',
                'type': 'volatility'
            },

            # Phase 3 - Advanced Features
            'volume_indicators': {
                'features': ['volume_ma', 'volume_ratio', 'log_volume', 'vpt', 'mfi'],
                'description': 'Volume-based indicators',
                'type': 'volume'
            },

            'rsi_family': {
                'features': ['rsi_1d', 'rsi_3d', 'rsi_1w', 'rsi_2w', 'rsi_ema'],
                'description': 'RSI across multiple timeframes',
                'type': 'oscillator'
            },

            'intraday': {
                'features': ['returns_from_daily_open', 'intraday_range_pct', 'position_in_range',
                           'overnight_gap', 'dist_from_intraday_high', 'dist_from_intraday_low'],
                'description': 'Intraday reference points and gaps',
                'type': 'intraday'
            },

            'sequence_modeling': {
                'features': [f'{feat}_lag_{lag}' for feat in ['returns', 'vol', 'volume_ratio']
                           for lag in [1, 2, 4, 8, 24]] +
                          [f'returns_{stat}_{window}h' for stat in ['mean', 'std', 'skew', 'kurt']
                           for window in [6, 12, 24]],
                'description': 'Lagged features and rolling statistics for ML models',
                'type': 'sequence'
            }
        }


    def get_data_availability(self, symbol: str) -> Dict[str, Any]:
        """
        Check data availability and coverage for a symbol.

        Returns:
            Dict with availability info, record count, date range, etc.
        """
        try:
            query = """
                SELECT
                    COUNT(*) as total_records,
                    MIN(timestamp) as earliest_date,
                    MAX(timestamp) as latest_date,
                    feature_version,
                    COUNT(CASE WHEN rsi_1d IS NOT NULL THEN 1 END) as rsi_coverage,
                    COUNT(CASE WHEN price_ma_short IS NOT NULL THEN 1 END) as ma_coverage,
                    COUNT(CASE WHEN bb_upper IS NOT NULL THEN 1 END) as bb_coverage
                FROM feature_engineered_data
                WHERE symbol = %s
                GROUP BY feature_version
                ORDER BY feature_version DESC
            """

            result = self.execute_query(query, (symbol,))

            if not result:
                return {'available': False, 'message': f'No feature data found for {symbol}'}

            availability = []
            for row in result:
                availability.append({
                    'version': row[3],
                    'total_records': row[0],
                    'date_range': f"{row[1]} to {row[2]}",
                    'coverage': {
                        'rsi': f"{row[4]}/{row[0]} ({row[4]/row[0]*100:.1f}%)",
                        'moving_averages': f"{row[5]}/{row[0]} ({row[5]/row[0]*100:.1f}%)",
                        'bollinger_bands': f"{row[6]}/{row[0]} ({row[6]/row[0]*100:.1f}%)"
                    }
                })

            return {
                'available': True,
                'symbol': symbol,
                'versions': availability
            }

        except Exception as e:
            self.logger.error(f"Error checking data availability for {symbol}: {e}")
            return {'available': False, 'error': str(e)}

