#!/usr/bin/env python3
"""
Feature Engineering Module for ML Trading System
Phase 1: Foundation Features (13 features) - Exact match to Analysis-v4.ipynb

This module implements the EXACT feature calculations from the Analysis-v4.ipynb notebook
starting with Phase 1 foundation features for validation and baseline performance.
"""

import os
import sys
import pandas as pd
import numpy as np
import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.data.storage.database import get_db_manager
from src.utils.logging_config import setup_logger, log_operation

# Configure logging
logger = setup_logger('mltrading.feature_engineering', 'feature_engineering.log', enable_database_logging=False)

class FeatureEngineerPhase1And2:
    """
    Comprehensive Feature Engineering - Foundation + Core Technical + Advanced Features
    
    Phase 1 - Foundation Features (13):
    - Basic Price Features (6): returns, log_returns, high_low_pct, open_close_pct, price_acceleration, returns_sign
    - Time Features (7): hour, day_of_week, hour_sin, hour_cos, dow_sin, dow_cos, is_market_open
    
    Phase 2 - Core Technical Features (23):
    - Moving Averages (8): price_ma_short/med/long, ratios
    - Technical Indicators (10): Bollinger Bands, MACD, ATR, Williams %R  
    - Volatility Features (5): realized volatility, Garman-Klass, vol of vol
    
    Phase 3 - Advanced Features (~50+ additional features):
    - Volume Features (7): volume_ma, volume_ratio, log_volume, VPT, MFI
    - RSI Features (5): Multiple timeframes + EMA RSI  
    - Intraday Features (6): daily open returns, range position, gaps
    - Lagged Features (15): returns/volatility/volume lags
    - Rolling Statistics (15): mean/std/skew/kurt over multiple windows
    - Advanced Technical (variable): Additional ATR, Williams %R variants
    """
    
    def __init__(self):
        self.db_manager = get_db_manager()
        
        # Feature constants from Analysis-v4.ipynb - EXACT MATCH
        self.SHORT_WINDOW = 24        # 1 day
        self.MED_WINDOW = 120         # 5 days  
        self.LONG_WINDOW = 480        # 20 days
        self.VOL_WINDOWS = [12, 24, 120]  # 12h, 1d, 5d

        self.RSI_WINDOWS = {
            'rsi_1d': 24,        # 1 day
            'rsi_3d': 72,        # 3 days
            'rsi_1w': 168,       # 1 week
            'rsi_2w': 336        # 2 weeks
        }

        self.LAG_PERIODS = [1, 2, 4, 8, 24]  # 1h, 2h, 4h, 8h, 1day
        self.ROLLING_WINDOWS = [6, 12, 24]   # 6h, 12h, 24h windows
        
        # Lookback requirement for calculations
        self.MIN_LOOKBACK_HOURS = 600  # 25 days buffer for stable calculations
    
    def clean_sequence_data(self, sequence_data: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
        """Clean sequence data by handling NaN values with multiple strategies"""
        
        # Handle empty data
        if sequence_data.empty:
            return sequence_data.copy(), True
        
        sequence_clean = sequence_data.copy()
        initial_nans = sequence_clean.isnull().sum().sum()
        
        if initial_nans > 0:
            logger.info(f"Cleaning {initial_nans} NaN values from feature data")
        
        # Strategy 1: Forward fill then backward fill
        sequence_clean = sequence_clean.ffill().bfill()
        nans_after_fill = sequence_clean.isnull().sum().sum()
        
        # Strategy 2: If still NaNs, fill with column means (only for numeric columns)
        if nans_after_fill > 0:
            # Only calculate means for numeric columns to avoid date arithmetic issues
            numeric_columns = sequence_clean.select_dtypes(include=[np.number]).columns
            column_means = sequence_clean[numeric_columns].mean()
            
            # Only fill numeric columns that have valid means (avoid NaN means)
            for col in numeric_columns:
                if sequence_clean[col].isnull().any() and not pd.isna(column_means[col]):
                    sequence_clean[col].fillna(column_means[col], inplace=True)
        
        nans_after_mean = sequence_clean.isnull().sum().sum()
        
        # Strategy 3: If still NaNs (shouldn't happen), fill with 0
        if nans_after_mean > 0:
            sequence_clean = sequence_clean.fillna(0)
            logger.warning(f"Applied fallback: {nans_after_mean} NaNs filled with 0 as last resort")
        
        # Final check
        remaining_nans = sequence_clean.isnull().sum().sum()
        
        if initial_nans > 0:
            logger.info(f"NaN cleaning complete: {initial_nans} -> {remaining_nans} remaining")
        
        return sequence_clean, remaining_nans == 0
    
    def get_market_data_for_features(self, symbol: str, initial_run: bool = False) -> pd.DataFrame:
        """
        Get market data for feature calculation
        
        Args:
            symbol: Stock symbol
            initial_run: If True, get ALL historical data. If False, get recent data only (600 hours)
            
        Returns:
            DataFrame with market data for feature calculation
        """
        with log_operation(f"get_market_data_{symbol}", logger, symbol=symbol):
            try:
                conn = self.db_manager.get_connection()
                try:
                    if initial_run:
                        # Initial run: Get ALL historical data for complete feature backfill
                        query = """
                            SELECT symbol, timestamp, open, high, low, close, volume, source
                            FROM market_data 
                            WHERE symbol = %s 
                            ORDER BY timestamp ASC
                        """
                        df = pd.read_sql_query(query, conn, params=[symbol])
                        data_description = "ALL historical data"
                    else:
                        # Production incremental run: Get recent data only for performance
                        query = """
                            SELECT symbol, timestamp, open, high, low, close, volume, source
                            FROM market_data 
                            WHERE symbol = %s 
                            AND timestamp >= NOW() - INTERVAL '%s hours'
                            ORDER BY timestamp ASC
                        """
                        df = pd.read_sql_query(query, conn, params=[symbol, self.MIN_LOOKBACK_HOURS])
                        data_description = f"last {self.MIN_LOOKBACK_HOURS} hours"
                    
                    if df.empty:
                        logger.warning(f"No market data found for {symbol}")
                        return pd.DataFrame()
                    
                    # Convert timestamp to datetime  
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.sort_values('timestamp').reset_index(drop=True)
                    
                    logger.info(f"Retrieved {len(df)} records for {symbol} ({data_description})")
                    return df
                    
                finally:
                    self.db_manager.return_connection(conn)
                    
            except Exception as e:
                logger.error(f"Failed to retrieve market data for {symbol}: {e}")
                return pd.DataFrame()
    
    def calculate_basic_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Phase 1 basic price features (6 features) - exact match to notebook
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with basic price features added
        """
        if df.empty or len(df) < 2:
            logger.warning("Insufficient data for basic price features")
            return df
            
        logger.info("Calculating basic price features (6 features)")
        
        # Basic price features - EXACT match to notebook add_basic_price_features()
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['high_low_pct'] = (df['high'] - df['low']) / df['close']
        df['open_close_pct'] = (df['close'] - df['open']) / df['open']
        
        # Price momentum features - EXACT match to notebook
        df['price_acceleration'] = df['returns'].diff()  # Second derivative of price
        df['returns_sign'] = np.sign(df['returns'])  # Direction indicator
        
        logger.info("Completed basic price features calculation")
        return df
    
    def calculate_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Phase 1 time features (7 features) - exact match to notebook
        
        Args:
            df: DataFrame with timestamp column
            
        Returns:
            DataFrame with time features added
        """
        if df.empty:
            logger.warning("No data for time features")
            return df
            
        logger.info("Calculating time features (7 features)")
        
        # Time features - EXACT match to notebook add_time_features()
        # Basic time features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['date'] = df['timestamp'].dt.date
        
        # Cyclical encoding for time features (better for neural networks)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Market session features - EXACT match to notebook
        df['is_market_open'] = ((df['hour'] >= 9) & (df['hour'] <= 16)).astype(int)
        df['is_morning'] = ((df['hour'] >= 9) & (df['hour'] <= 12)).astype(int)
        df['is_afternoon'] = ((df['hour'] >= 13) & (df['hour'] <= 16)).astype(int)
        df['hours_since_open'] = np.clip(df['hour'] - 9, 0, 7)
        df['hours_to_close'] = np.clip(16 - df['hour'], 0, 7)
        
        logger.info("Completed time features calculation")
        return df
    
    def calculate_moving_average_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Phase 2 moving average features (8 features) - exact match to notebook
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with moving average features added
        """
        if df.empty:
            logger.warning("No data for moving averages")
            return df
        
        if len(df) < self.LONG_WINDOW:
            logger.warning(f"Limited data for moving averages: {len(df)} records, optimal: {self.LONG_WINDOW}")
        
        logger.info("Calculating moving average features (8 features)")
        
        # Moving averages - EXACT match to notebook add_moving_average_features()
        # Use min_periods=1 to allow calculation even with limited data
        df['price_ma_short'] = df['close'].rolling(self.SHORT_WINDOW, min_periods=1).mean()
        df['price_ma_med'] = df['close'].rolling(self.MED_WINDOW, min_periods=1).mean()
        df['price_ma_long'] = df['close'].rolling(self.LONG_WINDOW, min_periods=1).mean()
        
        # Price to moving average ratios - EXACT match to notebook
        df['price_to_ma_short'] = df['close'] / df['price_ma_short']
        df['price_to_ma_med'] = df['close'] / df['price_ma_med']
        df['price_to_ma_long'] = df['close'] / df['price_ma_long']
        
        # Moving average convergence/divergence ratios - EXACT match to notebook
        df['ma_short_to_med'] = df['price_ma_short'] / df['price_ma_med']
        df['ma_med_to_long'] = df['price_ma_med'] / df['price_ma_long']
        
        logger.info("Completed moving average features calculation")
        return df
    
    def calculate_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate volatility features - exact match to notebook
        
        Args:
            df: DataFrame with OHLCV data and returns
            
        Returns:
            DataFrame with volatility features added
        """
        if df.empty or 'returns' not in df.columns:
            logger.warning("No returns data for volatility features")
            return df
            
        logger.info("Calculating volatility features (8 features)")
        
        # Basic volatility features - EXACT match to notebook
        df['returns_squared'] = df['returns'] ** 2
        
        # Realized volatility for different windows - EXACT match to notebook
        df['realized_vol_short'] = df['returns'].rolling(12).std() * np.sqrt(24)  # 12h window
        df['realized_vol_med'] = df['returns'].rolling(24).std() * np.sqrt(24)    # 24h window  
        df['realized_vol_long'] = df['returns'].rolling(120).std() * np.sqrt(24)  # 120h window
        
        # Volatility ratios
        df['vol_ratio_short_med'] = df['realized_vol_short'] / (df['realized_vol_med'] + 1e-10)
        df['vol_ratio_med_long'] = df['realized_vol_med'] / (df['realized_vol_long'] + 1e-10)
        
        # Garman-Klass volatility - EXACT match to notebook
        ln_hl = np.log(df['high'] / df['low'])
        ln_co = np.log(df['close'] / df['open'])
        gk_vol = 0.5 * ln_hl**2 - (2*np.log(2) - 1) * ln_co**2
        df['gk_volatility'] = np.sqrt(gk_vol.rolling(24).mean() * 24)
        
        # Volatility of volatility - EXACT match to notebook
        df['vol_of_vol'] = df['realized_vol_med'].rolling(24).std()
        
        logger.info("Completed volatility features calculation")
        return df
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Phase 2 technical indicators (10 features) - exact match to notebook
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with technical indicators added
        """
        if df.empty or len(df) < 50:
            logger.warning(f"Insufficient data for technical indicators: {len(df)} records")
            return df
            
        logger.info("Calculating technical indicators (10 features)")
        
        # Bollinger Bands - exact match to notebook (20-period, 2 std dev)
        bb_window = 20
        bb_std_multiplier = 2
        
        bb_mean = df['close'].rolling(window=bb_window, min_periods=1).mean()
        bb_std = df['close'].rolling(window=bb_window, min_periods=1).std()
        
        df['bb_upper'] = bb_mean + (bb_std_multiplier * bb_std)
        df['bb_lower'] = bb_mean - (bb_std_multiplier * bb_std)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_squeeze'] = (df['bb_upper'] - df['bb_lower']) / bb_mean
        
        # MACD - exact match to notebook (12, 26, 9)
        ema_fast = df['close'].ewm(span=12, min_periods=1).mean()
        ema_slow = df['close'].ewm(span=26, min_periods=1).mean()
        
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=9, min_periods=1).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        df['macd_normalized'] = df['macd'] / df['close']
        
        # ATR - Average True Range (14-period) - exact match to notebook
        high_low = df['high'] - df['low']
        high_close_prev = abs(df['high'] - df['close'].shift(1))
        low_close_prev = abs(df['low'] - df['close'].shift(1))
        
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(window=14, min_periods=1).mean()
        df['atr_normalized'] = df['atr'] / df['close']
        
        # Williams %R - exact match to notebook (14-period)
        williams_window = 14
        highest_high = df['high'].rolling(window=williams_window, min_periods=1).max()
        lowest_low = df['low'].rolling(window=williams_window, min_periods=1).min()
        df['williams_r'] = -100 * (highest_high - df['close']) / (highest_high - lowest_low)
        
        logger.info("Completed technical indicators calculation")
        return df
    
    def calculate_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate volume-based features - exact match to notebook
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with volume features added
        """
        if df.empty or 'volume' not in df.columns:
            logger.warning("No volume data for volume features")
            return df
            
        logger.info("Calculating volume features")
        
        # Basic volume features
        df['volume_ma'] = df['volume'].rolling(self.MED_WINDOW).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        df['log_volume'] = np.log(df['volume'] + 1)
        
        # Volume-Price Trend (VPT) indicator
        df['vpt'] = (df['volume'] * df['returns']).cumsum()
        df['vpt_ma'] = df['vpt'].rolling(self.SHORT_WINDOW).mean()
        df['vpt_normalized'] = df['vpt'] / df['vpt_ma']
        
        # Money Flow Index components
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        money_flow = typical_price * df['volume']
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
        
        money_ratio = (positive_flow.rolling(14).sum() / 
                      (negative_flow.rolling(14).sum() + 1e-10))
        df['mfi'] = 100 - (100 / (1 + money_ratio))
        
        logger.info("Completed volume features calculation")
        return df
    
    def calculate_rsi_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate multiple RSI timeframes - exact match to notebook
        
        Args:
            df: DataFrame with close prices
            
        Returns:
            DataFrame with RSI features added
        """
        if df.empty or 'close' not in df.columns:
            logger.warning("No close price data for RSI features")
            return df
            
        logger.info("Calculating RSI features")
        
        # Multiple RSI timeframes
        for rsi_name, window in self.RSI_WINDOWS.items():
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
            rs = gain / (loss + 1e-10)
            df[rsi_name] = 100 - (100 / (1 + rs))
        
        # Exponential Moving Average RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        alpha = 2 / (14 + 1)
        avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()
        rs_ema = avg_gain / (avg_loss + 1e-10)
        df['rsi_ema'] = 100 - (100 / (1 + rs_ema))
        
        logger.info("Completed RSI features calculation")
        return df
    
    def calculate_intraday_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate intraday reference points with enhanced error handling - exact match to notebook
        
        Args:
            df: DataFrame with OHLCV data and timestamp
            
        Returns:
            DataFrame with intraday features added
        """
        if df.empty or 'timestamp' not in df.columns:
            logger.warning("No timestamp data for intraday features")
            return df
            
        logger.info("Calculating intraday features")
        
        try:
            # Ensure date column exists
            if 'date' not in df.columns:
                df['date'] = df['timestamp'].dt.date
            
            daily_opens = df.groupby('date')['open'].transform('first')
            df['returns_from_daily_open'] = ((df['close'] - daily_opens) / 
                                           daily_opens).fillna(0)
            
            df['intraday_high'] = df.groupby('date')['high'].transform('max')
            df['intraday_low'] = df.groupby('date')['low'].transform('min')
            
            intraday_range = df['intraday_high'] - df['intraday_low']
            df['intraday_range_pct'] = (intraday_range / daily_opens).fillna(0)
            
            range_denominator = intraday_range.replace(0, np.nan)
            df['position_in_range'] = ((df['close'] - df['intraday_low']) / 
                                     range_denominator).fillna(0.5)
            
            prev_day_close = (df.groupby('date')['close']
                             .transform('last')
                             .shift(df.groupby('date').cumcount().max() + 1))
            df['overnight_gap'] = ((daily_opens - prev_day_close) / 
                                prev_day_close).fillna(0)
            
            df['dist_from_intraday_high'] = ((df['close'] - df['intraday_high']) / 
                                           df['intraday_high']).fillna(0)
            df['dist_from_intraday_low'] = ((df['close'] - df['intraday_low']) / 
                                          df['intraday_low']).fillna(0)
            
        except Exception as e:
            symbol = df['symbol'].iloc[0] if 'symbol' in df.columns and not df.empty else 'unknown'
            logger.warning(f"Error in intraday features for {symbol}: {e}")
            # Create dummy features if calculation fails
            for col in ['returns_from_daily_open', 'intraday_range_pct', 'position_in_range', 
                       'overnight_gap', 'dist_from_intraday_high', 'dist_from_intraday_low']:
                df[col] = 0 if 'gap' in col or 'range' in col or 'dist' in col else 0.5
        
        logger.info("Completed intraday features calculation")
        return df
    
    def calculate_lagged_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate lagged features for sequence modeling - exact match to notebook
        
        Args:
            df: DataFrame with calculated features
            
        Returns:
            DataFrame with lagged features added
        """
        if df.empty:
            logger.warning("No data for lagged features")
            return df
            
        logger.info("Calculating lagged features")
        
        # Enhanced lagged features
        for lag in self.LAG_PERIODS:
            if 'returns' in df.columns:
                df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
            if 'realized_vol_short' in df.columns:
                df[f'vol_lag_{lag}'] = df['realized_vol_short'].shift(lag)
            if 'volume_ratio' in df.columns:
                df[f'volume_ratio_lag_{lag}'] = df['volume_ratio'].shift(lag)
        
        logger.info("Completed lagged features calculation")
        return df
    
    def calculate_rolling_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate rolling statistics for sequence modeling - exact match to notebook
        
        Args:
            df: DataFrame with returns
            
        Returns:
            DataFrame with rolling statistics added
        """
        if df.empty or 'returns' not in df.columns:
            logger.warning("No returns data for rolling statistics")
            return df
            
        logger.info("Calculating rolling statistics")
        
        # Rolling statistics for different windows
        for window in self.ROLLING_WINDOWS:
            df[f'returns_mean_{window}h'] = df['returns'].rolling(window).mean()
            df[f'returns_std_{window}h'] = df['returns'].rolling(window).std()
            df[f'returns_skew_{window}h'] = df['returns'].rolling(window).skew()
            df[f'returns_kurt_{window}h'] = df['returns'].rolling(window).kurt()
            
            # Price momentum over different windows
            df[f'price_momentum_{window}h'] = (df['close'] / df['close'].shift(window) - 1)
        
        logger.info("Completed rolling statistics calculation")
        return df
    
    def calculate_advanced_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate advanced technical indicators - exact match to notebook
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with advanced technical indicators added
        """
        if df.empty:
            logger.warning("No data for advanced technical indicators")
            return df
            
        logger.info("Calculating advanced technical indicators")
        
        # Average True Range (ATR) for volatility normalization
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        df['atr'] = true_range.rolling(14).mean()
        df['atr_normalized'] = df['atr'] / df['close']
        
        # Williams %R
        highest_high = df['high'].rolling(14).max()
        lowest_low = df['low'].rolling(14).min()
        df['williams_r'] = -100 * ((highest_high - df['close']) / 
                                 (highest_high - lowest_low + 1e-10))
        
        logger.info("Completed advanced technical indicators calculation")
        return df
    
    def calculate_phase1_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all Phase 1 foundation features (13 total)
        
        Args:
            df: DataFrame with OHLCV data and timestamp
            
        Returns:
            DataFrame with Phase 1 features calculated
        """
        with log_operation("calculate_phase1_features", logger, 
                          symbol=df['symbol'].iloc[0] if not df.empty else 'unknown',
                          records=len(df)):
            
            if df.empty:
                logger.error("Empty DataFrame provided")
                return df
            
            logger.info(f"Starting Phase 1 feature calculation for {len(df)} records")
            
            # Validate required columns
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return df
            
            # Make a copy to avoid modifying original
            df_features = df.copy()
            
            # Calculate Phase 1 features
            df_features = self.calculate_basic_price_features(df_features)
            df_features = self.calculate_time_features(df_features)
            
            # Add metadata  
            df_features['source'] = 'yahoo'
            df_features['feature_version'] = '1.0'
            df_features['created_at'] = datetime.now()
            df_features['updated_at'] = datetime.now()
            
            # Add date column for compatibility (string format as in notebook)
            df_features['date'] = df_features['timestamp'].dt.strftime('%Y-%m-%d')
            
            logger.info(f"Phase 1 features calculated successfully: {len(df_features)} records")
            return df_features
    
    def calculate_phase1_and_phase2_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Phase 1+2 features (36 total) - exact match to notebook
        
        Args:
            df: DataFrame with OHLCV data and timestamp
            
        Returns:
            DataFrame with Phase 1+2 features calculated
        """
        with log_operation("calculate_phase1_and_phase2_features", logger, 
                          symbol=df['symbol'].iloc[0] if not df.empty else 'unknown',
                          records=len(df)):
            
            if df.empty:
                logger.error("Empty DataFrame provided")
                return df
            
            logger.info(f"Starting Phase 1+2 feature calculation for {len(df)} records")
            
            # Validate required columns
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return df
            
            # Check minimum data requirements
            if len(df) < self.LONG_WINDOW:
                logger.warning(f"Limited data for Phase 2: {len(df)} records, need {self.LONG_WINDOW} for optimal calculations")
            
            # Make a copy to avoid modifying original
            df_features = df.copy()
            
            # Calculate Phase 1 features (foundation)
            df_features = self.calculate_basic_price_features(df_features)
            df_features = self.calculate_time_features(df_features)
            
            # Calculate Phase 2 features (core technical)
            df_features = self.calculate_moving_average_features(df_features)
            df_features = self.calculate_volatility_features(df_features)
            df_features = self.calculate_technical_indicators(df_features)
            
            # Clean NaN values using multi-strategy approach
            logger.info("Applying comprehensive NaN cleaning to calculated features")
            df_features, is_clean = self.clean_sequence_data(df_features)
            
            if not is_clean:
                logger.error("Failed to clean all NaN values from feature data")
                # Continue processing but log the issue
            
            # Add metadata  
            df_features['source'] = 'yahoo'
            df_features['feature_version'] = '2.0'  # Updated for Phase 1+2
            df_features['created_at'] = datetime.now()
            df_features['updated_at'] = datetime.now()
            
            # Add date column for compatibility (string format as in notebook)
            df_features['date'] = df_features['timestamp'].dt.strftime('%Y-%m-%d')
            
            logger.info(f"Phase 1+2 features calculated successfully: {len(df_features)} records, 36 features, clean: {is_clean}")
            return df_features
    
    def calculate_phase3_comprehensive_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive Phase 1+2+3 features (~90+ total) - exact match to notebook
        
        Args:
            df: DataFrame with OHLCV data and timestamp
            
        Returns:
            DataFrame with all Phase 1+2+3 features calculated
        """
        with log_operation("calculate_phase3_comprehensive_features", logger, 
                          symbol=df['symbol'].iloc[0] if not df.empty else 'unknown',
                          records=len(df)):
            
            if df.empty:
                logger.error("Empty DataFrame provided")
                return df
            
            logger.info(f"Starting Phase 1+2+3 comprehensive feature calculation for {len(df)} records")
            
            # Validate required columns
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return df
            
            # Check minimum data requirements
            if len(df) < self.LONG_WINDOW:
                logger.warning(f"Limited data for comprehensive features: {len(df)} records, need {self.LONG_WINDOW} for optimal calculations")
            
            # Make a copy to avoid modifying original
            df_features = df.copy()
            
            # Phase 1 features (foundation)
            df_features = self.calculate_basic_price_features(df_features)
            df_features = self.calculate_time_features(df_features)
            
            # Phase 2 features (core technical)
            df_features = self.calculate_moving_average_features(df_features)
            df_features = self.calculate_volatility_features(df_features)
            df_features = self.calculate_technical_indicators(df_features)
            
            # Phase 3 features (advanced)
            df_features = self.calculate_volume_features(df_features)
            df_features = self.calculate_rsi_features(df_features)
            df_features = self.calculate_intraday_features(df_features)
            df_features = self.calculate_lagged_features(df_features)
            df_features = self.calculate_rolling_statistics(df_features)
            
            # Clean NaN values using multi-strategy approach
            logger.info("Applying comprehensive NaN cleaning to calculated features")
            df_features, is_clean = self.clean_sequence_data(df_features)
            
            if not is_clean:
                logger.error("Failed to clean all NaN values from feature data")
                # Continue processing but log the issue
            
            # Add metadata  
            df_features['source'] = 'yahoo'
            df_features['feature_version'] = '3.0'  # Updated for Phase 1+2+3
            df_features['created_at'] = datetime.now()
            df_features['updated_at'] = datetime.now()
            
            # Add date column for compatibility (string format as in notebook)
            df_features['date'] = df_features['timestamp'].dt.strftime('%Y-%m-%d')
            
            feature_count = len([col for col in df_features.columns if col not in ['symbol', 'timestamp', 'source', 'created_at', 'updated_at']])
            logger.info(f"Phase 1+2+3 comprehensive features calculated successfully: {len(df_features)} records, {feature_count} features, clean: {is_clean}")
            return df_features
    
    def prepare_features_for_storage(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Prepare feature data for database insertion
        
        Args:
            df: DataFrame with calculated features
            
        Returns:
            List of dictionaries ready for database insertion
        """
        if df.empty:
            return []
        
        # Comprehensive Phase 1+2+3 feature columns for database storage (~90+ features total)
        feature_columns = [
            # Base data
            'symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume',
            
            # Phase 1 features (13) - Foundation
            'returns', 'log_returns', 'high_low_pct', 'open_close_pct', 
            'price_acceleration', 'returns_sign',
            'hour', 'day_of_week', 'date', 'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 
            'is_market_open',
            
            # Phase 2 features (24) - Core Technical
            # Moving averages (8)
            'price_ma_short', 'price_ma_med', 'price_ma_long',
            'price_to_ma_short', 'price_to_ma_med', 'price_to_ma_long',
            'ma_short_to_med', 'ma_med_to_long',
            
            # Volatility features (5)
            'realized_vol_short', 'realized_vol_med', 'realized_vol_long',
            'gk_volatility', 'vol_of_vol',
            
            # Technical indicators (10)
            'bb_upper', 'bb_lower', 'bb_position', 'bb_squeeze',
            'macd', 'macd_signal', 'macd_histogram', 'macd_normalized',
            'atr', 'atr_normalized', 'williams_r',
            
            # Phase 3 features - Advanced Features
            # Volume features (7)
            'volume_ma', 'volume_ratio', 'log_volume', 'vpt', 'vpt_ma', 'vpt_normalized', 'mfi',
            
            # RSI features (5)
            'rsi_1d', 'rsi_3d', 'rsi_1w', 'rsi_2w', 'rsi_ema',
            
            # Extended time features from Phase 1
            'is_morning', 'is_afternoon', 'hours_since_open', 'hours_to_close',
            
            # Intraday features (6)
            'returns_from_daily_open', 'intraday_high', 'intraday_low', 
            'intraday_range_pct', 'position_in_range', 'overnight_gap',
            'dist_from_intraday_high', 'dist_from_intraday_low',
            
            # Lagged features (15)
            'returns_lag_1', 'vol_lag_1', 'volume_ratio_lag_1',
            'returns_lag_2', 'vol_lag_2', 'volume_ratio_lag_2',
            'returns_lag_4', 'vol_lag_4', 'volume_ratio_lag_4',
            'returns_lag_8', 'vol_lag_8', 'volume_ratio_lag_8',
            'returns_lag_24', 'vol_lag_24', 'volume_ratio_lag_24',
            
            # Rolling statistics (15)
            'returns_mean_6h', 'returns_std_6h', 'returns_skew_6h', 'returns_kurt_6h', 'price_momentum_6h',
            'returns_mean_12h', 'returns_std_12h', 'returns_skew_12h', 'returns_kurt_12h', 'price_momentum_12h',
            'returns_mean_24h', 'returns_std_24h', 'returns_skew_24h', 'returns_kurt_24h', 'price_momentum_24h',
            
            # Missing columns that exist in database schema
            'returns_squared', 'vol_ratio_short_med', 'vol_ratio_med_long',
            
            # Metadata
            'source', 'feature_version', 'created_at', 'updated_at'
        ]
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in feature_columns:
                if col in df.columns:
                    value = row[col]
                    # Handle NaN values
                    if pd.isna(value):
                        record[col] = None
                    else:
                        record[col] = value
                else:
                    record[col] = None
            records.append(record)
        
        return records
    
    def store_phase1_features(self, df: pd.DataFrame, symbol: str) -> bool:
        """
        Store Phase 1 features in database
        
        Args:
            df: DataFrame with Phase 1 features
            symbol: Stock symbol
            
        Returns:
            bool: Success status
        """
        with log_operation(f"store_phase1_features_{symbol}", logger, 
                          symbol=symbol, records=len(df)):
            
            if df.empty:
                logger.warning(f"No features to store for {symbol}")
                return False
            
            try:
                records = self.prepare_features_for_storage(df)
                
                if not records:
                    logger.warning(f"No valid records to store for {symbol}")
                    return False
                
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # Dynamic INSERT statement based on available columns
                        sample_record = records[0]
                        columns = list(sample_record.keys())
                        placeholders = ', '.join(['%s'] * len(columns))
                        columns_str = ', '.join(columns)
                        
                        # ON CONFLICT handling for updates
                        update_columns = [col for col in columns 
                                        if col not in ['symbol', 'timestamp', 'source']]
                        update_str = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
                        
                        insert_query = f"""
                            INSERT INTO feature_engineered_data ({columns_str})
                            VALUES ({placeholders})
                            ON CONFLICT (symbol, timestamp, source) 
                            DO UPDATE SET {update_str}
                        """
                        
                        # Prepare data for batch insertion
                        data_rows = []
                        for record in records:
                            data_rows.append(tuple(record[col] for col in columns))
                        
                        # Batch insert
                        cursor.executemany(insert_query, data_rows)
                        conn.commit()
                        
                        inserted_count = cursor.rowcount
                        logger.info(f"Stored {inserted_count} Phase 1 feature records for {symbol}")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to store Phase 1 features for {symbol}: {e}")
                return False
    
    def process_symbol_phase1(self, symbol: str) -> bool:
        """
        Complete Phase 1 feature engineering pipeline for a single symbol
        
        Args:
            symbol: Stock symbol to process
            
        Returns:
            bool: Success status
        """
        with log_operation(f"process_symbol_phase1_{symbol}", logger, symbol=symbol):
            
            logger.info(f"Starting Phase 1 feature engineering for {symbol}")
            
            # Step 1: Get optimized market data
            df = self.get_market_data_for_features(symbol)
            
            if df.empty:
                logger.warning(f"No market data available for {symbol}")
                return False
            
            if len(df) < 25:  # Minimum for basic calculations
                logger.warning(f"Insufficient data for {symbol}: {len(df)} records")
                return False
            
            # Step 2: Calculate Phase 1 features
            df_with_features = self.calculate_phase1_features(df)
            
            if df_with_features.empty:
                logger.error(f"Phase 1 feature calculation failed for {symbol}")
                return False
            
            # Step 3: Store features
            success = self.store_phase1_features(df_with_features, symbol)
            
            if success:
                logger.info(f"Phase 1 feature engineering completed successfully for {symbol}")
            else:
                logger.error(f"Failed to store Phase 1 features for {symbol}")
            
            return success
    
    def process_symbol_phase1_and_phase2(self, symbol: str, initial_run: bool = False) -> bool:
        """
        Complete Phase 1+2 feature engineering pipeline for a single symbol
        
        Args:
            symbol: Stock symbol to process
            initial_run: If True, process ALL historical data. If False, process recent data only
            
        Returns:
            bool: Success status
        """
        with log_operation(f"process_symbol_phase1_and_phase2_{symbol}", logger, symbol=symbol):
            
            run_type = "INITIAL (ALL historical data)" if initial_run else "INCREMENTAL (recent data)"
            logger.info(f"Starting Phase 1+2 feature engineering for {symbol} - {run_type}")
            
            # Step 1: Get market data (all historical for initial run, recent for incremental)
            df = self.get_market_data_for_features(symbol, initial_run=initial_run)
            
            if df.empty:
                logger.warning(f"No market data available for {symbol}")
                return False
            
            if len(df) < 50:  # Minimum for technical indicators
                logger.warning(f"Insufficient data for {symbol}: {len(df)} records")
                return False
            
            # Step 2: Calculate Phase 1+2 features
            df_with_features = self.calculate_phase1_and_phase2_features(df)
            
            if df_with_features.empty:
                logger.error(f"Phase 1+2 feature calculation failed for {symbol}")
                return False
            
            # Step 3: Store features (using same storage method - it's dynamic)
            success = self.store_phase1_features(df_with_features, symbol)
            
            if success:
                logger.info(f"Phase 1+2 feature engineering completed successfully for {symbol}")
            else:
                logger.error(f"Failed to store Phase 1+2 features for {symbol}")
            
            return success
    
    def process_multiple_symbols_phase1_and_phase2(self, symbols: List[str], initial_run: bool = False) -> Dict[str, bool]:
        """
        Process Phase 1+2 features for multiple symbols
        
        Args:
            symbols: List of stock symbols
            initial_run: If True, process ALL historical data for each symbol
            
        Returns:
            Dict mapping symbol to success status
        """
        with log_operation("process_multiple_symbols_phase1_and_phase2", logger, symbol_count=len(symbols)):
            
            run_type = "INITIAL" if initial_run else "INCREMENTAL"
            logger.info(f"Starting Phase 1+2 processing for {len(symbols)} symbols - {run_type} RUN")
            
            results = {}
            successful = 0
            
            for symbol in symbols:
                try:
                    success = self.process_symbol_phase1_and_phase2(symbol, initial_run=initial_run)
                    results[symbol] = success
                    if success:
                        successful += 1
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    results[symbol] = False
            
            logger.info(f"Phase 1+2 {run_type} processing completed: {successful}/{len(symbols)} successful")
            return results
    
    def process_symbol_phase3_comprehensive(self, symbol: str, initial_run: bool = False) -> bool:
        """
        Complete Phase 1+2+3 comprehensive feature engineering pipeline for a single symbol
        
        Args:
            symbol: Stock symbol to process
            initial_run: If True, process ALL historical data. If False, process recent data only
            
        Returns:
            bool: Success status
        """
        with log_operation(f"process_symbol_phase3_comprehensive_{symbol}", logger, symbol=symbol):
            
            run_type = "INITIAL (ALL historical data)" if initial_run else "INCREMENTAL (recent data)"
            logger.info(f"Starting Phase 1+2+3 comprehensive feature engineering for {symbol} - {run_type}")
            
            # Step 1: Get market data (all historical for initial run, recent for incremental)
            df = self.get_market_data_for_features(symbol, initial_run=initial_run)
            
            if df.empty:
                logger.warning(f"No market data available for {symbol}")
                return False
            
            if len(df) < 100:  # Minimum for comprehensive features
                logger.warning(f"Insufficient data for {symbol}: {len(df)} records")
                return False
            
            # Step 2: Calculate comprehensive Phase 1+2+3 features
            df_with_features = self.calculate_phase3_comprehensive_features(df)
            
            if df_with_features.empty:
                logger.error(f"Phase 1+2+3 comprehensive feature calculation failed for {symbol}")
                return False
            
            # Step 3: Store features (using same storage method - it's dynamic)
            success = self.store_phase1_features(df_with_features, symbol)
            
            if success:
                logger.info(f"Phase 1+2+3 comprehensive feature engineering completed successfully for {symbol}")
            else:
                logger.error(f"Failed to store Phase 1+2+3 comprehensive features for {symbol}")
            
            return success
    
    def process_multiple_symbols_phase3_comprehensive(self, symbols: List[str], initial_run: bool = False) -> Dict[str, bool]:
        """
        Process Phase 1+2+3 comprehensive features for multiple symbols
        
        Args:
            symbols: List of stock symbols
            initial_run: If True, process ALL historical data for each symbol
            
        Returns:
            Dict mapping symbol to success status
        """
        with log_operation("process_multiple_symbols_phase3_comprehensive", logger, symbol_count=len(symbols)):
            
            run_type = "INITIAL" if initial_run else "INCREMENTAL"
            logger.info(f"Starting Phase 1+2+3 comprehensive processing for {len(symbols)} symbols - {run_type} RUN")
            
            results = {}
            successful = 0
            
            for symbol in symbols:
                try:
                    success = self.process_symbol_phase3_comprehensive(symbol, initial_run=initial_run)
                    results[symbol] = success
                    if success:
                        successful += 1
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    results[symbol] = False
            
            logger.info(f"Phase 1+2+3 comprehensive {run_type} processing completed: {successful}/{len(symbols)} successful")
            return results
    
    def process_multiple_symbols_phase1(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Process Phase 1 features for multiple symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dict mapping symbol to success status
        """
        with log_operation("process_multiple_symbols_phase1", logger, symbol_count=len(symbols)):
            
            logger.info(f"Starting Phase 1 processing for {len(symbols)} symbols")
            
            results = {}
            successful = 0
            
            for symbol in symbols:
                try:
                    success = self.process_symbol_phase1(symbol)
                    results[symbol] = success
                    if success:
                        successful += 1
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    results[symbol] = False
            
            logger.info(f"Phase 1 processing completed: {successful}/{len(symbols)} successful")
            return results


def test_phase1_features():
    """Test Phase 1 feature engineering with sample symbols"""
    
    logger.info("Testing Phase 1 feature engineering")
    
    # Initialize Phase 1+2 feature engineer (backward compatible)
    engineer = FeatureEngineerPhase1And2()
    
    # Test with a few symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    results = engineer.process_multiple_symbols_phase1(test_symbols)
    
    for symbol, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"Phase 1 features for {symbol}: {status}")
    
    successful_count = sum(results.values())
    print(f"\nOverall results: {successful_count}/{len(test_symbols)} symbols processed successfully")
    
    return results

def test_phase1_and_phase2_features():
    """Test Phase 1+2 feature engineering with sample symbols"""
    
    logger.info("Testing Phase 1+2 feature engineering")
    
    # Initialize Phase 1+2 feature engineer
    engineer = FeatureEngineerPhase1And2()
    
    # Test with a few symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    results = engineer.process_multiple_symbols_phase1_and_phase2(test_symbols)
    
    for symbol, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"Phase 1+2 features for {symbol}: {status}")
    
    successful_count = sum(results.values())
    print(f"\nOverall results: {successful_count}/{len(test_symbols)} symbols processed successfully")
    
    return results

def test_phase3_comprehensive_features():
    """Test Phase 1+2+3 comprehensive feature engineering with sample symbols"""
    
    logger.info("Testing Phase 1+2+3 comprehensive feature engineering")
    
    # Initialize comprehensive feature engineer
    engineer = FeatureEngineerPhase1And2()
    
    # Test with a few symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    results = engineer.process_multiple_symbols_phase3_comprehensive(test_symbols)
    
    for symbol, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"Phase 1+2+3 comprehensive features for {symbol}: {status}")
    
    successful_count = sum(results.values())
    print(f"\nOverall results: {successful_count}/{len(test_symbols)} symbols processed successfully")
    
    return results


if __name__ == "__main__":
    # Test Phase 1+2+3 comprehensive feature engineering
    print("=" * 70)
    print("TESTING PHASE 1+2+3 COMPREHENSIVE FEATURE ENGINEERING")
    print("=" * 70)
    
    test_results = test_phase3_comprehensive_features()
    
    print("\n" + "=" * 70)
    print("PHASE 1+2+3 COMPREHENSIVE FEATURE ENGINEERING TEST COMPLETE")
    print("=" * 70)