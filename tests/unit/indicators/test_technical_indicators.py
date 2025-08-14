"""
Unit tests for technical indicators accuracy and calculations.
Tests the core technical analysis indicators used in the dashboard.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.dashboard.services.technical_indicators import TechnicalIndicatorService
except ImportError:
    # Handle missing imports gracefully for testing
    pass


class TestRSICalculation:
    """Test suite for RSI (Relative Strength Index) calculations."""
    
    @pytest.fixture
    def known_rsi_data(self):
        """Create test data with known RSI values for verification."""
        # Create simple trending data where RSI behavior is predictable
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        
        # Create data that starts at 100 and has alternating gains/losses
        prices = []
        current_price = 100.0
        changes = [1, -0.5, 1.5, -1, 2, -0.8, 1.2, -1.5, 2.5, -0.3,
                  1.8, -1.2, 0.8, -0.5, 1.5, -0.9, 2.1, -0.7, 1.3, -1.1,
                  1.7, -0.6, 1.1, -1.3, 2.2, -0.4, 1.6, -1.0, 1.4, -0.8]
        
        for change in changes:
            current_price += change
            prices.append(current_price)
        
        data = pd.DataFrame({
            'timestamp': dates,
            'close': prices
        })
        return data.set_index('timestamp')
    
    def test_rsi_calculation_bounds(self, known_rsi_data):
        """Test that RSI values stay within 0-100 bounds."""
        try:
            service = TechnicalIndicatorService()
            rsi_values = service.calculate_rsi(known_rsi_data, period=14)
            
            # RSI should never go below 0 or above 100
            assert all(0 <= val <= 100 for val in rsi_values.dropna())
            
            # Should have reasonable non-NaN values after warmup period
            assert len(rsi_values.dropna()) >= 10  # At least some calculated values
            
        except ImportError:
            pytest.skip("Technical analysis module not available")
    
    def test_rsi_extreme_conditions(self):
        """Test RSI with extreme market conditions."""
        # All gains (should approach RSI = 100)
        all_gains = pd.Series([100 + i for i in range(30)])  # Continuous uptrend
        
        # All losses (should approach RSI = 0)  
        all_losses = pd.Series([100 - i for i in range(30)])  # Continuous downtrend
        
        try:
            service = TechnicalIndicatorService()
            
            rsi_gains = service.calculate_rsi(pd.DataFrame({'close': all_gains}), period=14)
            rsi_losses = service.calculate_rsi(pd.DataFrame({'close': all_losses}), period=14)
            
            # RSI for continuous gains should be high (>70)
            final_gain_rsi = rsi_gains.iloc[-1]
            assert final_gain_rsi > 70
            
            # RSI for continuous losses should be low (<30)
            final_loss_rsi = rsi_losses.iloc[-1]
            assert final_loss_rsi < 30
            
        except ImportError:
            pytest.skip("Technical analysis module not available")
    
    def test_rsi_period_sensitivity(self, known_rsi_data):
        """Test RSI calculation with different periods."""
        periods = [7, 14, 21]
        
        try:
            service = TechnicalIndicatorService()
            rsi_results = {}
            
            for period in periods:
                rsi_results[period] = service.calculate_rsi(known_rsi_data, period=period)
            
            # All periods should produce valid results
            for period, rsi in rsi_results.items():
                assert not rsi.dropna().empty
                assert all(0 <= val <= 100 for val in rsi.dropna())
                
            # Shorter periods should be more volatile (have wider range)
            rsi_7_range = rsi_results[7].dropna().max() - rsi_results[7].dropna().min()
            rsi_21_range = rsi_results[21].dropna().max() - rsi_results[21].dropna().min()
            assert rsi_7_range >= rsi_21_range * 0.8  # Allow some tolerance
            
        except ImportError:
            pytest.skip("Technical analysis module not available")


class TestMovingAverages:
    """Test suite for moving average calculations (SMA/EMA)."""
    
    @pytest.fixture
    def simple_price_data(self):
        """Create simple price data for moving average testing."""
        # Use sequential numbers for easy verification
        prices = list(range(1, 21))  # 1, 2, 3, ..., 20
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        
        return pd.Series(prices, index=dates)
    
    def test_sma_calculation_accuracy(self, simple_price_data):
        """Test SMA calculation accuracy with known values."""
        try:
            service = TechnicalIndicatorService()
            sma_5 = service.calculate_sma(pd.DataFrame({'close': simple_price_data}), period=5)
            
            # Test specific known values
            # SMA(5) for values [1,2,3,4,5] = 3.0
            assert abs(sma_5.iloc[4] - 3.0) < 0.001
            
            # SMA(5) for values [6,7,8,9,10] = 8.0  
            assert abs(sma_5.iloc[9] - 8.0) < 0.001
            
            # SMA(5) for values [16,17,18,19,20] = 18.0
            assert abs(sma_5.iloc[-1] - 18.0) < 0.001
            
            # Service uses min_periods=1, so early values are calculated
            # Just verify we have reasonable values for early periods
            assert sma_5.iloc[0] == 1.0  # First value should be just the first price
            assert sma_5.iloc[1] == 1.5  # (1+2)/2 = 1.5
            
        except ImportError:
            pytest.skip("Technical analysis module not available")
    
    def test_ema_vs_sma_responsiveness(self, simple_price_data):
        """Test that EMA is more responsive than SMA."""
        # Add a sudden price jump at the end
        price_with_jump = simple_price_data.copy()
        price_with_jump.iloc[-1] = 100  # Big jump from 20 to 100
        
        try:
            service = TechnicalIndicatorService()
            sma_10 = service.calculate_sma(pd.DataFrame({'close': price_with_jump}), period=10)
            ema_10 = service.calculate_ema(pd.DataFrame({'close': price_with_jump}), period=10)
            
            # EMA should react more to the recent jump than SMA
            sma_final = sma_10.iloc[-1]
            ema_final = ema_10.iloc[-1]
            
            assert ema_final > sma_final  # EMA should be higher due to recent jump
            
        except ImportError:
            pytest.skip("Technical analysis module not available")
    
    def test_moving_average_convergence(self):
        """Test moving averages converge to mean for constant values."""
        # Constant price should make MA converge to that price
        constant_price = pd.Series([50.0] * 30)
        
        try:
            service = TechnicalIndicatorService()
            sma_10 = service.calculate_sma(pd.DataFrame({'close': constant_price}), period=10)
            ema_10 = service.calculate_ema(pd.DataFrame({'close': constant_price}), period=10)
            
            # After enough periods, both should converge to 50
            assert abs(sma_10.iloc[-1] - 50.0) < 0.001
            assert abs(ema_10.iloc[-1] - 50.0) < 0.1  # EMA might have small error
            
        except ImportError:
            pytest.skip("Technical analysis module not available")


class TestMACDCalculation:
    """Test suite for MACD (Moving Average Convergence Divergence) calculations."""
    
    @pytest.fixture
    def trending_data(self):
        """Create trending data for MACD testing."""
        # Create clear uptrend followed by downtrend
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        # Uptrend for first 50 days, then downtrend
        uptrend = np.linspace(100, 200, 50)
        downtrend = np.linspace(200, 150, 50)
        prices = np.concatenate([uptrend, downtrend])
        
        return pd.Series(prices, index=dates)
    
    def test_macd_signal_generation(self, trending_data):
        """Test MACD signal line generation."""
        try:
            service = TechnicalIndicatorService()
            macd_result = service.calculate_macd(pd.DataFrame({'close': trending_data}))
            macd_line = macd_result['macd']
            signal_line = macd_result['signal']
            histogram = macd_result['histogram']
            
            # All components should have same length (after warmup)
            valid_macd = macd_line.dropna()
            valid_signal = signal_line.dropna()
            valid_histogram = histogram.dropna()
            
            assert len(valid_macd) == len(valid_signal)
            assert len(valid_signal) == len(valid_histogram)
            
            # Histogram should be MACD - Signal
            calculated_histogram = valid_macd - valid_signal
            assert np.allclose(calculated_histogram, valid_histogram.values, rtol=1e-5)
            
        except ImportError:
            pytest.skip("Technical analysis module not available")
    
    def test_macd_trend_following(self, trending_data):
        """Test MACD follows trend direction."""
        try:
            service = TechnicalIndicatorService()
            macd_result = service.calculate_macd(pd.DataFrame({'close': trending_data}))
            macd_line = macd_result['macd']
            
            # During uptrend (first half), MACD should generally be positive
            mid_point = len(trending_data) // 2
            uptrend_macd = macd_line.iloc[35:mid_point].dropna()  # Allow warmup
            
            if not uptrend_macd.empty:
                # Most MACD values during uptrend should be positive
                positive_ratio = (uptrend_macd > 0).sum() / len(uptrend_macd)
                assert positive_ratio > 0.5  # At least half should be positive
            
        except ImportError:
            pytest.skip("Technical analysis module not available")


class TestBollingerBands:
    """Test suite for Bollinger Bands calculations."""
    
    @pytest.fixture
    def volatile_data(self):
        """Create data with varying volatility for Bollinger Bands testing."""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        # Create data with changing volatility
        base_price = 100
        prices = [base_price]
        
        for i in range(99):
            # Increase volatility in middle section
            if 30 <= i <= 60:
                volatility = 3.0  # High volatility period
            else:
                volatility = 1.0  # Low volatility period
                
            change = np.random.randn() * volatility
            new_price = prices[-1] + change
            prices.append(max(new_price, 1))  # Ensure positive prices
        
        return pd.Series(prices, index=dates)
    
    def test_bollinger_bands_structure(self, volatile_data):
        """Test Bollinger Bands structure and relationships."""
        try:
            service = TechnicalIndicatorService()
            bb_result = service.calculate_bollinger_bands(pd.DataFrame({'close': volatile_data}), period=20, std=2)
            upper = bb_result['upper']
            middle = bb_result['middle']
            lower = bb_result['lower']
            
            # Middle band should be SMA
            sma_20 = service.calculate_sma(pd.DataFrame({'close': volatile_data}), period=20)
            assert np.allclose(middle.dropna(), sma_20.dropna(), rtol=1e-5)
            
            # Upper band should always be >= Middle band
            valid_indices = ~(upper.isna() | middle.isna())
            assert all(upper[valid_indices] >= middle[valid_indices])
            
            # Lower band should always be <= Middle band  
            valid_indices = ~(lower.isna() | middle.isna())
            assert all(lower[valid_indices] <= middle[valid_indices])
            
        except ImportError:
            pytest.skip("Technical analysis module not available")
    
    def test_bollinger_bands_volatility_response(self, volatile_data):
        """Test that Bollinger Bands widen/narrow with volatility."""
        try:
            service = TechnicalIndicatorService()
            bb_result = service.calculate_bollinger_bands(pd.DataFrame({'close': volatile_data}), period=20, std=2)
            upper = bb_result['upper']
            middle = bb_result['middle']
            lower = bb_result['lower']
            
            # Calculate band width (upper - lower)
            band_width = upper - lower
            
            # High volatility period (days 30-60) should have wider bands
            high_vol_width = band_width.iloc[50:70].mean()  # Sample from high vol period
            low_vol_width = band_width.iloc[80:95].mean()   # Sample from low vol period
            
            assert high_vol_width > low_vol_width * 0.8  # Allow some tolerance
            
        except ImportError:
            pytest.skip("Technical analysis module not available")


class TestIndicatorCombinations:
    """Test suite for indicator combinations and cross-validation."""
    
    @pytest.fixture
    def market_data(self):
        """Create realistic market data for combination testing."""
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        
        # Create OHLCV data with realistic patterns
        np.random.seed(42)
        base_price = 100
        
        ohlcv_data = []
        current_price = base_price
        
        for i in range(200):
            # Daily price change
            change = np.random.randn() * 2
            current_price = max(current_price + change, 1)
            
            # Create OHLC from close
            daily_range = abs(np.random.randn()) * 1.5
            high = current_price + daily_range
            low = current_price - daily_range
            open_price = current_price + np.random.randn() * 0.5
            
            volume = max(int(1000000 + np.random.randn() * 500000), 100000)
            
            ohlcv_data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': current_price,
                'volume': volume
            })
        
        df = pd.DataFrame(ohlcv_data, index=dates)
        return df
    
    def test_sma_crossover_signals(self, market_data):
        """Test SMA crossover signal generation."""
        try:
            service = TechnicalIndicatorService()
            sma_fast = service.calculate_sma(market_data, period=10)
            sma_slow = service.calculate_sma(market_data, period=20)
            
            # Generate crossover signals
            crossover_up = (sma_fast > sma_slow) & (sma_fast.shift(1) <= sma_slow.shift(1))
            crossover_down = (sma_fast < sma_slow) & (sma_fast.shift(1) >= sma_slow.shift(1))
            
            # Should have some crossovers in 200 days of data
            assert crossover_up.sum() > 0
            assert crossover_down.sum() > 0
            
            # Crossovers should not happen simultaneously
            assert not (crossover_up & crossover_down).any()
            
        except ImportError:
            pytest.skip("Technical analysis module not available")
    
    def test_rsi_bollinger_confluence(self, market_data):
        """Test RSI and Bollinger Band confluence for signal confirmation."""
        try:
            service = TechnicalIndicatorService()
            rsi = service.calculate_rsi(market_data, period=14)
            bb_result = service.calculate_bollinger_bands(market_data, period=20, std=2)
            upper = bb_result['upper']
            middle = bb_result['middle']
            lower = bb_result['lower']
            
            # Find potential oversold conditions
            price_touches_lower = market_data['close'] <= lower
            rsi_oversold = rsi <= 30
            
            # Find confluence signals
            oversold_confluence = price_touches_lower & rsi_oversold
            
            # Should have valid data for analysis
            valid_data = ~(rsi.isna() | lower.isna())
            assert valid_data.sum() > 150  # Most data should be valid
            
            # Confluence events should be relatively rare
            confluence_ratio = oversold_confluence.sum() / valid_data.sum()
            assert confluence_ratio < 0.1  # Less than 10% of the time
            
        except ImportError:
            pytest.skip("Technical analysis module not available")


class TestIndicatorPerformance:
    """Test suite for indicator calculation performance."""
    
    def test_indicator_calculation_speed(self):
        """Test that indicators calculate quickly on large datasets."""
        # Create large dataset (2 years of daily data)
        large_data = pd.Series(
            100 + np.random.randn(730).cumsum(),
            index=pd.date_range(start='2021-01-01', periods=730, freq='D')
        )
        
        import time
        
        try:
            service = TechnicalIndicatorService()
            
            # Test RSI performance
            start_time = time.time()
            rsi = service.calculate_rsi(pd.DataFrame({'close': large_data}), period=14)
            rsi_time = time.time() - start_time
            
            # Test SMA performance  
            start_time = time.time()
            sma = service.calculate_sma(pd.DataFrame({'close': large_data}), period=20)
            sma_time = time.time() - start_time
            
            # Test MACD performance
            start_time = time.time()
            macd_result = service.calculate_macd(pd.DataFrame({'close': large_data}))
            macd = macd_result['macd']
            signal = macd_result['signal']
            histogram = macd_result['histogram']
            macd_time = time.time() - start_time
            
            # All calculations should complete quickly (< 0.1 seconds each)
            assert rsi_time < 0.1
            assert sma_time < 0.1
            assert macd_time < 0.1
            
            # Results should be valid
            assert not rsi.dropna().empty
            assert not sma.dropna().empty
            assert not macd.dropna().empty
            
        except ImportError:
            pytest.skip("Technical analysis module not available")
    
    def test_memory_efficiency(self):
        """Test memory efficiency of indicator calculations."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        try:
            service = TechnicalIndicatorService()
            
            # Calculate multiple indicators on multiple datasets
            for _ in range(5):
                data = pd.Series(100 + np.random.randn(1000).cumsum())
                
                df_data = pd.DataFrame({'close': data})
                rsi = service.calculate_rsi(df_data, period=14)
                sma = service.calculate_sma(df_data, period=20)
                ema = service.calculate_ema(df_data, period=12)
                bb_result = service.calculate_bollinger_bands(df_data, period=20)
                upper = bb_result['upper']
                middle = bb_result['middle']
                lower = bb_result['lower']
                
                # Clean up
                del rsi, sma, ema, upper, middle, lower, data
                gc.collect()
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (< 50MB)
            assert memory_increase < 50 * 1024 * 1024
            
        except ImportError:
            pytest.skip("Technical analysis module not available")


class TestIndicatorEdgeCases:
    """Test suite for indicator edge cases and error handling."""
    
    def test_insufficient_data_handling(self):
        """Test indicator behavior with insufficient data."""
        # Very short data series
        short_data = pd.Series([100, 101, 102])
        
        try:
            service = TechnicalIndicatorService()
            
            # RSI with period longer than data
            rsi = service.calculate_rsi(pd.DataFrame({'close': short_data}), period=14)
            # Should have very few valid values due to insufficient data
            assert len(rsi.dropna()) <= 2  # Very few valid values
            
            # SMA with period longer than data
            sma = service.calculate_sma(pd.DataFrame({'close': short_data}), period=10)
            # Should have very few valid values due to insufficient data
            assert len(sma.dropna()) <= 3  # Very few valid values
            
        except ImportError:
            pytest.skip("Technical analysis module not available")
    
    def test_constant_price_handling(self):
        """Test indicators with constant price data."""
        constant_data = pd.Series([100.0] * 50)
        
        try:
            service = TechnicalIndicatorService()
            
            # RSI with constant prices should be around 50 (neutral)
            rsi = service.calculate_rsi(pd.DataFrame({'close': constant_data}), period=14)
            if not rsi.dropna().empty:
                final_rsi = rsi.dropna().iloc[-1]
                assert 30 <= final_rsi <= 70  # Should be reasonable range for constant price
            
            # Bollinger Bands with constant prices should have narrow width
            bb_result = service.calculate_bollinger_bands(pd.DataFrame({'close': constant_data}), period=20, std=2)
            upper = bb_result['upper']
            lower = bb_result['lower']
            if not upper.dropna().empty and not lower.dropna().empty:
                final_upper = upper.dropna().iloc[-1]
                final_lower = lower.dropna().iloc[-1]
                assert abs(final_upper - final_lower) < 10  # Bands should be close for constant prices
            
        except ImportError:
            pytest.skip("Technical analysis module not available")
    
    def test_missing_data_handling(self):
        """Test indicators with missing/NaN data."""
        data_with_gaps = pd.Series([100, 101, np.nan, 103, np.nan, np.nan, 106, 107])
        
        try:
            service = TechnicalIndicatorService()
            
            # Indicators should handle NaN values gracefully
            rsi = service.calculate_rsi(pd.DataFrame({'close': data_with_gaps}), period=5)
            sma = service.calculate_sma(pd.DataFrame({'close': data_with_gaps}), period=3)
            
            # Should not crash and should produce some valid results
            assert not rsi.isna().all()  # Some values should be calculated
            assert not sma.isna().all()  # Some values should be calculated
            
        except ImportError:
            pytest.skip("Technical analysis module not available")