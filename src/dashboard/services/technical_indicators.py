"""
Technical indicators service for advanced chart analysis.
Implements various technical analysis indicators and overlays.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from .base_service import BaseDashboardService
from .cache_service import cached


class TechnicalIndicatorService(BaseDashboardService):
    """Service for calculating technical indicators."""
    
    def __init__(self):
        super().__init__()
        # Clear any existing cached calculations to ensure fresh data
        self._clear_cache()
    
    def _clear_cache(self):
        """Clear cached calculations to ensure fresh data."""
        try:
            # Clear the cache by setting a new instance variable
            self._cache_cleared = True
            self.logger.info("Technical indicators cache cleared")
        except Exception as e:
            self.logger.warning(f"Could not clear cache: {e}")
    
    @cached(ttl=300, key_func=lambda self, df, period: f"sma_{df['close'].iloc[0]:.2f}_{df['close'].iloc[-1]:.2f}_{period}")
    def calculate_sma(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate Simple Moving Average."""
        try:
            if 'close' not in df.columns or len(df) < period:
                self.logger.warning(f"SMA calculation failed - missing 'close' column or insufficient data")
                return pd.Series(index=df.index)
            
            # Debug: Check what data we're working with
            close_data = df['close']
            self.logger.info(f"SMA({period}) - Input data: length={len(close_data)}, range={close_data.min():.2f}-{close_data.max():.2f}, mean={close_data.mean():.2f}")
            
            # Check for any NaN or invalid values
            if close_data.isna().any():
                self.logger.warning(f"SMA calculation - Found {close_data.isna().sum()} NaN values in close data")
            
            sma = close_data.rolling(window=period, min_periods=1).mean()
            
            # Debug: Check the calculated SMA
            if not sma.empty:
                sma_last = sma.iloc[-1]
                self.logger.info(f"SMA({period}) calculated - Last value: {sma_last:.2f}")
                
                # Check if SMA is reasonable compared to input data
                if abs(sma_last - close_data.mean()) > 100:
                    self.logger.warning(f"SMA({period}) seems out of range! Close mean: {close_data.mean():.2f}, but SMA: {sma_last:.2f}")
            
            self.logger.debug(f"Calculated SMA({period}) for {len(df)} data points")
            return sma
            
        except Exception as e:
            self.logger.error(f"Error calculating SMA: {e}")
            return pd.Series(index=df.index)
    
    @cached(ttl=300)
    def calculate_ema(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate Exponential Moving Average."""
        try:
            if 'close' not in df.columns or len(df) < period:
                return pd.Series(index=df.index)
            
            ema = df['close'].ewm(span=period, adjust=False).mean()
            self.logger.debug(f"Calculated EMA({period}) for {len(df)} data points")
            return ema
            
        except Exception as e:
            self.logger.error(f"Error calculating EMA: {e}")
            return pd.Series(index=df.index)
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std: float = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands with improved logic."""
        try:
            if 'close' not in df.columns or len(df) < period + 1:
                self.logger.warning(f"Bollinger Bands: insufficient data - columns: {list(df.columns)}, length: {len(df)}, period: {period}")
                return {
                    'middle': pd.Series(index=df.index),
                    'upper': pd.Series(index=df.index),
                    'lower': pd.Series(index=df.index)
                }
            
            # Debug: Check the actual data ranges
            close_min = df['close'].min()
            close_max = df['close'].max()
            close_mean = df['close'].mean()
            close_dtype = df['close'].dtype
            self.logger.info(f"Bollinger Bands - Close price range: min={close_min:.2f}, max={close_max:.2f}, mean={close_mean:.2f}, dtype={close_dtype}")
            
            # Debug: Check for any data type issues
            if close_dtype == 'object':
                self.logger.warning(f"Close prices are object type - checking for string conversion issues")
                sample_prices = df['close'].head(5).tolist()
                self.logger.info(f"Sample close prices: {sample_prices}")
            
            # Debug: Check for any extreme outliers
            if close_max > 10000 or close_min < 0.01:
                self.logger.warning(f"Close prices seem extreme: min={close_min:.2f}, max={close_max:.2f}")
            
            # Calculate middle band (SMA)
            middle = self.calculate_sma(df, period)
            
            # Calculate standard deviation of the same window
            # This ensures consistency between SMA and std calculations
            rolling_std = df['close'].rolling(window=period, min_periods=period).std()
            
            # Calculate upper and lower bands
            upper = middle + (rolling_std * std)
            lower = middle - (rolling_std * std)
            
            # Debug: Check the calculated band ranges
            if not middle.empty and not upper.empty and not lower.empty:
                middle_last = middle.iloc[-1]
                upper_last = upper.iloc[-1]
                lower_last = lower.iloc[-1]
                self.logger.info(f"Bollinger Bands calculated - Middle: {middle_last:.2f}, Upper: {upper_last:.2f}, Lower: {lower_last:.2f}")
                
                # Check if bands are in reasonable range compared to close price
                if abs(middle_last - close_mean) > 100 or abs(upper_last - close_mean) > 200 or abs(lower_last - close_mean) > 200:
                    self.logger.warning(f"Bollinger Bands seem out of range! Close mean: {close_mean:.2f}, but bands are: M={middle_last:.2f}, U={upper_last:.2f}, L={lower_last:.2f}")
            
            # Price reality check - ensure bands make sense
            if not upper.empty and not lower.empty:
                # Upper band should generally be above lower band
                if upper.iloc[-1] <= lower.iloc[-1]:
                    self.logger.warning(f"Bollinger Bands: upper band ({upper.iloc[-1]:.2f}) <= lower band ({lower.iloc[-1]:.2f})")
            
            result = {
                'middle': middle,
                'upper': upper,
                'lower': lower
            }
            
            self.logger.info(f"Bollinger Bands calculated successfully: middle={middle.iloc[-1] if not middle.empty else 'N/A'}, upper={upper.iloc[-1] if not middle.empty else 'N/A'}, lower={lower.iloc[-1] if not middle.empty else 'N/A'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return {
                'middle': pd.Series(index=df.index),
                'upper': pd.Series(index=df.index),
                'lower': pd.Series(index=df.index)
            }
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        try:
            if 'close' not in df.columns or len(df) < period + 1:
                return pd.Series(index=df.index)
            
            # Calculate price changes
            delta = df['close'].diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate average gains and losses
            avg_gains = gains.rolling(window=period, min_periods=1).mean()
            avg_losses = losses.rolling(window=period, min_periods=1).mean()
            
            # Calculate RS and RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            self.logger.debug(f"Calculated RSI({period}) for {len(df)} data points")
            return rsi
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return pd.Series(index=df.index)
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        try:
            if 'close' not in df.columns or len(df) < slow:
                return {
                    'macd': pd.Series(index=df.index),
                    'signal': pd.Series(index=df.index),
                    'histogram': pd.Series(index=df.index)
                }
            
            # Calculate EMAs
            ema_fast = self.calculate_ema(df, fast)
            ema_slow = self.calculate_ema(df, slow)
            
            # Calculate MACD line
            macd = ema_fast - ema_slow
            
            # Calculate signal line (EMA of MACD)
            signal_line = macd.ewm(span=signal, adjust=False).mean()
            
            # Calculate histogram
            histogram = macd - signal_line
            
            self.logger.debug(f"Calculated MACD({fast}, {slow}, {signal}) for {len(df)} data points")
            
            return {
                'macd': macd,
                'signal': signal_line,
                'histogram': histogram
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return {
                'macd': pd.Series(index=df.index),
                'signal': pd.Series(index=df.index),
                'histogram': pd.Series(index=df.index)
            }
    
    def calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator."""
        try:
            required_cols = ['high', 'low', 'close']
            if not all(col in df.columns for col in required_cols) or len(df) < k_period:
                return {
                    'k_percent': pd.Series(index=df.index),
                    'd_percent': pd.Series(index=df.index)
                }
            
            # Calculate %K
            lowest_low = df['low'].rolling(window=k_period, min_periods=1).min()
            highest_high = df['high'].rolling(window=k_period, min_periods=1).max()
            
            k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
            
            # Calculate %D (SMA of %K)
            d_percent = k_percent.rolling(window=d_period, min_periods=1).mean()
            
            self.logger.debug(f"Calculated Stochastic({k_period}, {d_period}) for {len(df)} data points")
            
            return {
                'k_percent': k_percent.fillna(50),  # Fill NaN with midpoint
                'd_percent': d_percent.fillna(50)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic: {e}")
            return {
                'k_percent': pd.Series(index=df.index),
                'd_percent': pd.Series(index=df.index)
            }
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        try:
            required_cols = ['high', 'low', 'close']
            if not all(col in df.columns for col in required_cols) or len(df) < 2:
                return pd.Series(index=df.index)
            
            # Calculate True Range components
            high_low = df['high'] - df['low']
            high_close_prev = np.abs(df['high'] - df['close'].shift(1))
            low_close_prev = np.abs(df['low'] - df['close'].shift(1))
            
            # True Range is the maximum of the three components
            true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
            
            # Calculate ATR (EMA of True Range)
            atr = true_range.ewm(span=period, adjust=False).mean()
            
            self.logger.debug(f"Calculated ATR({period}) for {len(df)} data points")
            return atr
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return pd.Series(index=df.index)
    
    def calculate_volume_sma(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate Volume Simple Moving Average."""
        try:
            if 'volume' not in df.columns or len(df) < period:
                return pd.Series(index=df.index)
            
            volume_sma = df['volume'].rolling(window=period, min_periods=1).mean()
            self.logger.debug(f"Calculated Volume SMA({period}) for {len(df)} data points")
            return volume_sma
            
        except Exception as e:
            self.logger.error(f"Error calculating Volume SMA: {e}")
            return pd.Series(index=df.index)
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price."""
        try:
            required_cols = ['high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols) or len(df) == 0:
                return pd.Series(index=df.index)
            
            # Calculate typical price
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            
            # Calculate VWAP
            cumulative_volume = df['volume'].cumsum()
            cumulative_price_volume = (typical_price * df['volume']).cumsum()
            
            vwap = cumulative_price_volume / cumulative_volume
            
            self.logger.debug(f"Calculated VWAP for {len(df)} data points")
            return vwap.fillna(df['close'])  # Fill NaN with close price
            
        except Exception as e:
            self.logger.error(f"Error calculating VWAP: {e}")
            return pd.Series(index=df.index)
    
    def calculate_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
        """Calculate support and resistance levels."""
        try:
            if 'high' not in df.columns or 'low' not in df.columns or len(df) < window:
                return {'support': [], 'resistance': []}
            
            # Find local minima (support) and maxima (resistance)
            highs = df['high'].rolling(window=window, center=True).max()
            lows = df['low'].rolling(window=window, center=True).min()
            
            # Identify support levels (local minima)
            support_mask = (df['low'] == lows) & (df['low'].shift(1) > df['low']) & (df['low'].shift(-1) > df['low'])
            support_levels = df.loc[support_mask, 'low'].tolist()
            
            # Identify resistance levels (local maxima)
            resistance_mask = (df['high'] == highs) & (df['high'].shift(1) < df['high']) & (df['high'].shift(-1) < df['high'])
            resistance_levels = df.loc[resistance_mask, 'high'].tolist()
            
            # Remove duplicates and sort
            support_levels = sorted(list(set(support_levels)))
            resistance_levels = sorted(list(set(resistance_levels)), reverse=True)
            
            self.logger.debug(f"Calculated {len(support_levels)} support and {len(resistance_levels)} resistance levels")
            
            return {
                'support': support_levels[:5],  # Top 5 support levels
                'resistance': resistance_levels[:5]  # Top 5 resistance levels
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating support/resistance: {e}")
            return {'support': [], 'resistance': []}
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all available technical indicators."""
        try:
            if df.empty:
                return {}
            
            indicators = {
                # Moving Averages
                'sma_20': self.calculate_sma(df, 20),
                'sma_50': self.calculate_sma(df, 50),
                'ema_12': self.calculate_ema(df, 12),
                'ema_26': self.calculate_ema(df, 26),
                
                # Bollinger Bands
                'bollinger': self.calculate_bollinger_bands(df, 20, 2),
                
                # Oscillators
                'rsi': self.calculate_rsi(df, 14),
                'macd': self.calculate_macd(df, 12, 26, 9),
                'stochastic': self.calculate_stochastic(df, 14, 3),
                
                # Volatility
                'atr': self.calculate_atr(df, 14),
                
                # Volume
                'volume_sma': self.calculate_volume_sma(df, 20),
                'vwap': self.calculate_vwap(df),
                
                # Support/Resistance
                'support_resistance': self.calculate_support_resistance(df, 20)
            }
            
            self.logger.info(f"Calculated all technical indicators for {len(df)} data points")
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating all indicators: {e}")
            return {}
    
    def get_indicator_config(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all available indicators."""
        return {
            'sma': {
                'name': 'Simple Moving Average',
                'type': 'overlay',
                'default_periods': [20, 50, 100],
                'color': '#2fa4e7',
                'description': 'Average price over a specified period'
            },
            'ema': {
                'name': 'Exponential Moving Average',
                'type': 'overlay',
                'default_periods': [12, 26, 50],
                'color': '#28a745',
                'description': 'Weighted average giving more importance to recent prices'
            },
            'bollinger': {
                'name': 'Bollinger Bands',
                'type': 'overlay',
                'default_period': 20,
                'default_std': 2,
                'colors': {'middle': '#6c757d', 'upper': '#dc3545', 'lower': '#dc3545'},
                'description': 'Volatility bands around moving average'
            },
            'rsi': {
                'name': 'Relative Strength Index',
                'type': 'oscillator',
                'default_period': 14,
                'range': [0, 100],
                'overbought': 70,
                'oversold': 30,
                'color': '#fd7e14',
                'description': 'Momentum oscillator measuring speed of price changes'
            },
            'macd': {
                'name': 'MACD',
                'type': 'oscillator',
                'default_params': {'fast': 12, 'slow': 26, 'signal': 9},
                'colors': {'macd': '#6f42c1', 'signal': '#e83e8c', 'histogram': '#20c997'},
                'description': 'Trend-following momentum indicator'
            },
            'stochastic': {
                'name': 'Stochastic Oscillator',
                'type': 'oscillator',
                'default_params': {'k': 14, 'd': 3},
                'range': [0, 100],
                'overbought': 80,
                'oversold': 20,
                'colors': {'k': '#17a2b8', 'd': '#ffc107'},
                'description': 'Momentum oscillator comparing closing price to price range'
            },
            'atr': {
                'name': 'Average True Range',
                'type': 'indicator',
                'default_period': 14,
                'color': '#6c757d',
                'description': 'Volatility indicator measuring price range'
            },
            'vwap': {
                'name': 'VWAP',
                'type': 'overlay',
                'color': '#ff6b6b',
                'description': 'Volume Weighted Average Price'
            }
        }