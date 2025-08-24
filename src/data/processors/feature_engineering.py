#!/usr/bin/env python3
"""
Feature Engineering Module for ML Trading System
Calculates technical indicators and features from raw market data
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import talib

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.data.storage.database import get_db_manager
from src.utils.logging_config import get_combined_logger, log_operation

logger = get_combined_logger("mltrading.feature_engineering", enable_database_logging=False)


class FeatureEngineer:
    """
    Handles feature engineering calculations for market data
    """
    
    def __init__(self):
        self.db_manager = get_db_manager()
        
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for a DataFrame of market data
        
        Args:
            df: DataFrame with columns [open, high, low, close, volume]
            
        Returns:
            DataFrame with technical indicators added
        """
        with log_operation("calculate_technical_indicators", logger, 
                          symbol=df['symbol'].iloc[0] if not df.empty else 'unknown',
                          records=len(df)):
            
            if df.empty or len(df) < 50:
                logger.warning(f"Insufficient data for feature calculation: {len(df)} records")
                return df
            
            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    logger.error(f"Missing required column: {col}")
                    return df
            
            # Convert to numpy arrays for talib
            open_prices = df['open'].astype(float).values
            high_prices = df['high'].astype(float).values
            low_prices = df['low'].astype(float).values
            close_prices = df['close'].astype(float).values
            volumes = df['volume'].astype(float).values
            
            # Moving Averages
            df['sma_5'] = talib.SMA(close_prices, timeperiod=5)
            df['sma_10'] = talib.SMA(close_prices, timeperiod=10)
            df['sma_20'] = talib.SMA(close_prices, timeperiod=20)
            df['sma_50'] = talib.SMA(close_prices, timeperiod=50)
            
            df['ema_12'] = talib.EMA(close_prices, timeperiod=12)
            df['ema_26'] = talib.EMA(close_prices, timeperiod=26)
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
            df['macd'] = macd
            df['macd_signal'] = macd_signal
            df['macd_histogram'] = macd_hist
            
            # RSI
            df['rsi_14'] = talib.RSI(close_prices, timeperiod=14)
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close_prices, timeperiod=20, nbdevup=2, nbdevdn=2)
            df['bb_upper'] = bb_upper
            df['bb_middle'] = bb_middle
            df['bb_lower'] = bb_lower
            df['bb_width'] = (bb_upper - bb_lower) / bb_middle
            df['bb_position'] = (close_prices - bb_lower) / (bb_upper - bb_lower)
            
            # Volume Indicators
            df['volume_sma_20'] = talib.SMA(volumes, timeperiod=20)
            df['volume_ratio'] = volumes / df['volume_sma_20']
            
            # Price Action Features
            df['daily_return'] = df['close'].pct_change()
            df['price_change'] = df['close'].diff()
            df['price_change_pct'] = df['price_change'] / df['close'].shift(1)
            df['intraday_range'] = df['high'] - df['low']
            df['range_pct'] = df['intraday_range'] / df['close']
            df['gap_open'] = df['open'] - df['close'].shift(1)
            df['gap_open_pct'] = df['gap_open'] / df['close'].shift(1)
            
            # Volatility Features
            df['volatility_5d'] = df['daily_return'].rolling(window=5).std()
            df['volatility_20d'] = df['daily_return'].rolling(window=20).std()
            df['atr_14'] = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)
            
            # Support/Resistance Levels (simplified)
            df['support_level_1'] = df['low'].rolling(window=20).min()
            df['support_level_2'] = df['low'].rolling(window=50).min()
            df['resistance_level_1'] = df['high'].rolling(window=20).max()
            df['resistance_level_2'] = df['high'].rolling(window=50).max()
            
            # Momentum Features
            df['momentum_5'] = talib.MOM(close_prices, timeperiod=5)
            df['momentum_10'] = talib.MOM(close_prices, timeperiod=10)
            df['rate_of_change'] = talib.ROC(close_prices, timeperiod=10)
            
            # Volume Profile (simplified)
            df['volume_profile'] = volumes / df['volume'].rolling(window=50).mean()
            
            # Add metadata
            df['feature_version'] = '1.0'
            df['created_at'] = datetime.now()
            df['updated_at'] = datetime.now()
            
            logger.info(f"Calculated features for {len(df)} records")
            return df
    
    def get_market_data_for_feature_calculation(self, symbol: str, 
                                               lookback_days: int = 100) -> pd.DataFrame:
        """
        Retrieve market data for feature calculation
        
        Args:
            symbol: Stock symbol
            lookback_days: Number of days of historical data to retrieve
            
        Returns:
            DataFrame with market data
        """
        with log_operation(f"get_market_data_{symbol}", logger, 
                          symbol=symbol, lookback_days=lookback_days):
            
            try:
                conn = self.db_manager.get_connection()
                
                # Get data from the last N days
                query = """
                    SELECT symbol, timestamp, open, high, low, close, volume, source
                    FROM market_data 
                    WHERE symbol = %s 
                    AND timestamp >= NOW() - INTERVAL '%s days'
                    ORDER BY timestamp ASC
                """
                
                df = pd.read_sql_query(query, conn, params=[symbol, lookback_days])
                
                if df.empty:
                    logger.warning(f"No market data found for {symbol}")
                    return df
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                logger.info(f"Retrieved {len(df)} market data records for {symbol}")
                return df
                
            except Exception as e:
                logger.error(f"Failed to retrieve market data for {symbol}: {e}")
                return pd.DataFrame()
            finally:
                if 'conn' in locals():
                    self.db_manager.return_connection(conn)
    
    def store_feature_data(self, df: pd.DataFrame, symbol: str) -> bool:
        """
        Store calculated features in the database
        
        Args:
            df: DataFrame with calculated features
            symbol: Stock symbol
            
        Returns:
            bool: Success status
        """
        with log_operation(f"store_feature_data_{symbol}", logger, 
                          symbol=symbol, records=len(df)):
            
            if df.empty:
                logger.warning(f"No feature data to store for {symbol}")
                return False
            
            try:
                conn = self.db_manager.get_connection()
                
                # Prepare data for insertion
                feature_columns = [
                    'symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'sma_5', 'sma_10', 'sma_20', 'sma_50', 'ema_12', 'ema_26',
                    'macd', 'macd_signal', 'macd_histogram', 'rsi_14',
                    'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
                    'volume_sma_20', 'volume_ratio', 'volume_profile',
                    'daily_return', 'price_change', 'price_change_pct',
                    'intraday_range', 'range_pct', 'gap_open', 'gap_open_pct',
                    'volatility_5d', 'volatility_20d', 'atr_14',
                    'support_level_1', 'support_level_2', 'resistance_level_1', 'resistance_level_2',
                    'momentum_5', 'momentum_10', 'rate_of_change',
                    'source', 'feature_version', 'created_at', 'updated_at'
                ]
                
                # Filter only available columns
                available_columns = [col for col in feature_columns if col in df.columns]
                
                with conn.cursor() as cursor:
                    # Create INSERT statement with ON CONFLICT handling
                    placeholders = ', '.join(['%s'] * len(available_columns))
                    columns_str = ', '.join(available_columns)
                    update_columns = ', '.join([f"{col} = EXCLUDED.{col}" for col in available_columns 
                                              if col not in ['symbol', 'timestamp', 'source']])
                    
                    insert_query = f"""
                        INSERT INTO feature_engineered_data ({columns_str})
                        VALUES ({placeholders})
                        ON CONFLICT (symbol, timestamp, source) 
                        DO UPDATE SET {update_columns}
                    """
                    
                    # Prepare data rows
                    data_rows = []
                    for _, row in df.iterrows():
                        # Handle NaN values
                        row_data = []
                        for col in available_columns:
                            value = row[col]
                            if pd.isna(value):
                                row_data.append(None)
                            else:
                                row_data.append(value)
                        data_rows.append(tuple(row_data))
                    
                    # Batch insert
                    cursor.executemany(insert_query, data_rows)
                    conn.commit()
                    
                    inserted_count = cursor.rowcount
                    logger.info(f"Stored {inserted_count} feature records for {symbol}")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to store feature data for {symbol}: {e}")
                return False
            finally:
                if 'conn' in locals():
                    self.db_manager.return_connection(conn)
    
    def process_symbol_features(self, symbol: str, lookback_days: int = 100) -> bool:
        """
        Complete feature engineering process for a single symbol
        
        Args:
            symbol: Stock symbol to process
            lookback_days: Days of historical data to use
            
        Returns:
            bool: Success status
        """
        with log_operation(f"process_features_{symbol}", logger, 
                          symbol=symbol, lookback_days=lookback_days):
            
            logger.info(f"Starting feature engineering for {symbol}")
            
            # Step 1: Get market data
            df = self.get_market_data_for_feature_calculation(symbol, lookback_days)
            
            if df.empty:
                logger.warning(f"No market data available for {symbol}")
                return False
            
            # Step 2: Calculate features
            df_with_features = self.calculate_technical_indicators(df)
            
            if df_with_features.empty:
                logger.error(f"Feature calculation failed for {symbol}")
                return False
            
            # Step 3: Store features
            success = self.store_feature_data(df_with_features, symbol)
            
            if success:
                logger.info(f"Feature engineering completed successfully for {symbol}")
            else:
                logger.error(f"Failed to store features for {symbol}")
            
            return success


def create_feature_tables():
    """
    Create the feature engineering table in the database
    """
    with log_operation("create_feature_tables", logger):
        
        db_manager = get_db_manager()
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS feature_engineered_data (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            
            -- Original OHLCV data (reference)
            open NUMERIC(10,4),
            high NUMERIC(10,4),
            low NUMERIC(10,4),
            close NUMERIC(10,4),
            volume BIGINT,
            
            -- Technical Indicators
            sma_5 NUMERIC(10,4),
            sma_10 NUMERIC(10,4),
            sma_20 NUMERIC(10,4),
            sma_50 NUMERIC(10,4),
            ema_12 NUMERIC(10,4),
            ema_26 NUMERIC(10,4),
            macd NUMERIC(10,6),
            macd_signal NUMERIC(10,6),
            macd_histogram NUMERIC(10,6),
            rsi_14 NUMERIC(5,2),
            bb_upper NUMERIC(10,4),
            bb_middle NUMERIC(10,4),
            bb_lower NUMERIC(10,4),
            bb_width NUMERIC(10,6),
            bb_position NUMERIC(5,4),
            
            -- Volume Indicators
            volume_sma_20 NUMERIC(15,2),
            volume_ratio NUMERIC(8,4),
            volume_profile NUMERIC(8,4),
            
            -- Price Action Features
            daily_return NUMERIC(10,6),
            price_change NUMERIC(10,4),
            price_change_pct NUMERIC(8,6),
            intraday_range NUMERIC(10,4),
            range_pct NUMERIC(8,6),
            gap_open NUMERIC(10,4),
            gap_open_pct NUMERIC(8,6),
            
            -- Volatility Features
            volatility_5d NUMERIC(10,6),
            volatility_20d NUMERIC(10,6),
            atr_14 NUMERIC(10,4),
            
            -- Support/Resistance Levels
            support_level_1 NUMERIC(10,4),
            support_level_2 NUMERIC(10,4),
            resistance_level_1 NUMERIC(10,4),
            resistance_level_2 NUMERIC(10,4),
            
            -- Momentum Features  
            momentum_5 NUMERIC(10,6),
            momentum_10 NUMERIC(10,6),
            rate_of_change NUMERIC(8,6),
            
            -- Meta Information
            source VARCHAR(20) DEFAULT 'yahoo',
            feature_version VARCHAR(20) DEFAULT '1.0',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            CONSTRAINT unique_symbol_timestamp_features UNIQUE (symbol, timestamp, source)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_features_symbol_timestamp ON feature_engineered_data(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_features_symbol_date ON feature_engineered_data(symbol, DATE(timestamp));
        CREATE INDEX IF NOT EXISTS idx_features_created_at ON feature_engineered_data(created_at);
        """
        
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(create_table_sql)
                conn.commit()
                logger.info("Feature engineering table created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create feature engineering table: {e}")
            raise
        finally:
            if 'conn' in locals():
                db_manager.return_connection(conn)


if __name__ == "__main__":
    # Create feature table
    create_feature_tables()
    
    # Test feature engineering
    engineer = FeatureEngineer()
    symbols = ['AAPL', 'MSFT']  # Test symbols
    
    for symbol in symbols:
        success = engineer.process_symbol_features(symbol)
        print(f"Feature engineering for {symbol}: {'Success' if success else 'Failed'}")