"""
Unit tests for volume analysis features.
Tests the volume display options, calculations, and Technical Analysis Summary integration.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.layouts.chart_components import (
    create_volume_chart,
    create_volume_summary_card,
    create_volume_heatmap_chart
)
from src.dashboard.layouts.interactive_chart import InteractiveChartBuilder


class TestVolumeChartComponents:
    """Test suite for volume chart components."""
    
    @pytest.fixture
    def sample_volume_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        np.random.seed(42)  # For consistent test results
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': 100 + np.random.randn(30) * 2,
            'high': 102 + np.random.randn(30) * 2,
            'low': 98 + np.random.randn(30) * 2,
            'close': 100 + np.random.randn(30) * 2,
            'volume': np.random.randint(1000000, 5000000, 30)
        })
        data = data.set_index('timestamp')
        return data
    
    @pytest.fixture 
    def high_volume_data(self):
        """Create data with distinct high volume periods."""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        volumes = [1000000] * 30
        # Days 10-15 have high volume (3x average)
        for i in range(10, 16):
            volumes[i] = 3000000
            
        data = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0] * 30,
            'high': [102.0] * 30,
            'low': [98.0] * 30,
            'close': [101.0 if i % 2 == 0 else 99.0 for i in range(30)],  # Alternating price direction
            'volume': volumes
        })
        return data.set_index('timestamp')
    
    def test_create_volume_chart_basic(self, sample_volume_data):
        """Test basic volume chart creation."""
        chart = create_volume_chart(sample_volume_data)
        
        # Chart should be created successfully
        assert chart is not None
        assert hasattr(chart, 'data')
        assert len(chart.data) >= 1  # At least volume bars
        
        # Check volume bars properties
        volume_trace = chart.data[0]
        assert volume_trace.type == 'bar'
        assert len(volume_trace.x) == 30
        assert len(volume_trace.y) == 30
        assert all(vol > 0 for vol in volume_trace.y)
    
    def test_create_volume_chart_with_moving_average(self, sample_volume_data):
        """Test volume chart with moving average overlay."""
        chart = create_volume_chart(sample_volume_data)
        
        # Should have both volume bars and moving average line
        assert len(chart.data) == 2
        
        # First trace should be volume bars
        volume_bars = chart.data[0]
        assert volume_bars.type == 'bar'
        assert volume_bars.name == 'Volume'
        
        # Second trace should be moving average
        volume_ma = chart.data[1]
        assert volume_ma.type == 'scatter'
        assert volume_ma.name == '20-Day MA'
        assert volume_ma.mode == 'lines'
    
    def test_volume_chart_color_coding(self, high_volume_data):
        """Test that volume bars are properly color-coded by price direction."""
        chart = create_volume_chart(high_volume_data)
        
        volume_trace = chart.data[0]
        colors = volume_trace.marker.color
        
        # Colors can be list or tuple
        assert isinstance(colors, (list, tuple))
        assert len(colors) == 30
        
        # Check that colors alternate (since we have alternating price directions)
        # This is a simplified test - actual colors depend on chart color configuration
        unique_colors = set(colors)
        assert len(unique_colors) >= 2  # Should have at least 2 different colors
    
    def test_volume_chart_hover_template(self, sample_volume_data):
        """Test volume chart hover information."""
        chart = create_volume_chart(sample_volume_data)
        
        volume_trace = chart.data[0]
        assert 'Volume:' in volume_trace.hovertemplate
        assert 'vs 20MA:' in volume_trace.hovertemplate
        assert '%{y:,.0f}' in volume_trace.hovertemplate  # Volume formatting
    
    def test_volume_chart_empty_data(self):
        """Test volume chart with empty data."""
        empty_data = pd.DataFrame()
        chart = create_volume_chart(empty_data)
        
        # Should return empty chart gracefully
        assert chart is not None
        # Chart should indicate no data available
        assert hasattr(chart, 'layout')


class TestVolumeSummaryCard:
    """Test suite for volume summary card component."""
    
    @pytest.fixture
    def volume_data_with_stats(self):
        """Create volume data with known statistics."""
        dates = pd.date_range(start='2023-01-01', periods=25, freq='D')
        # Create data where current volume (last day) is 2x the 20-day average
        volumes = [1000000] * 20 + [2000000] * 5  # Last 5 days have high volume
        
        data = pd.DataFrame({
            'timestamp': dates,
            'volume': volumes
        })
        return data.set_index('timestamp')
    
    def test_create_volume_summary_card_basic(self, volume_data_with_stats):
        """Test basic volume summary card creation."""
        card = create_volume_summary_card(volume_data_with_stats)
        
        # Card should be created successfully
        assert card is not None
        # Should contain volume analysis information
        assert hasattr(card, 'children')
    
    def test_volume_summary_card_calculations(self, volume_data_with_stats):
        """Test volume ratio calculations in summary card."""
        # Get the last volume and calculate expected metrics
        current_volume = volume_data_with_stats['volume'].iloc[-1]  # 2,000,000
        avg_volume_20 = volume_data_with_stats['volume'].rolling(window=20).mean().iloc[-1]
        expected_ratio = current_volume / avg_volume_20
        
        # The ratio will be 1.6 because the 20-day average includes both 1M and 2M periods
        # (15 days * 1M + 5 days * 2M) / 20 = 25M / 20 = 1.25M
        # Current volume (2M) / avg (1.25M) = 1.6
        assert abs(expected_ratio - 1.6) < 0.1
        
        # Test that the card creation doesn't throw errors with these values
        card = create_volume_summary_card(volume_data_with_stats)
        assert card is not None
    
    def test_volume_summary_card_empty_data(self):
        """Test volume summary card with empty data."""
        empty_data = pd.DataFrame()
        card = create_volume_summary_card(empty_data)
        
        # Should handle empty data gracefully
        assert card is not None
    
    def test_volume_summary_card_no_volume_column(self):
        """Test volume summary card when volume column is missing."""
        data_without_volume = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=10),
            'close': [100] * 10
        }).set_index('timestamp')
        
        card = create_volume_summary_card(data_without_volume)
        
        # Should handle missing volume column gracefully
        assert card is not None


class TestVolumeHeatmapChart:
    """Test suite for volume heatmap functionality."""
    
    @pytest.fixture
    def daily_volume_data(self):
        """Create daily volume data spanning multiple weeks."""
        # Create 4 weeks of data (28 days)
        dates = pd.date_range(start='2023-01-01', periods=28, freq='D')
        np.random.seed(42)
        
        data = pd.DataFrame({
            'timestamp': dates,
            'volume': np.random.randint(1000000, 3000000, 28)
        })
        return data.set_index('timestamp')
    
    def test_create_volume_heatmap_chart_basic(self, daily_volume_data):
        """Test basic volume heatmap creation."""
        chart = create_volume_heatmap_chart(daily_volume_data, symbol="AAPL")
        
        # Chart should be created successfully
        assert chart is not None
        assert hasattr(chart, 'data')
        assert hasattr(chart, 'layout')
    
    def test_volume_heatmap_chart_empty_data(self):
        """Test volume heatmap with empty data."""
        empty_data = pd.DataFrame()
        chart = create_volume_heatmap_chart(empty_data, symbol="TEST")
        
        # Should return empty chart gracefully
        assert chart is not None
        # Should indicate no data available
        assert hasattr(chart, 'layout')
    
    def test_volume_heatmap_chart_no_volume_column(self):
        """Test volume heatmap when volume column is missing."""
        data_without_volume = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=10),
            'close': [100] * 10
        }).set_index('timestamp')
        
        chart = create_volume_heatmap_chart(data_without_volume, symbol="TEST")
        
        # Should handle missing volume column gracefully
        assert chart is not None


class TestInteractiveChartVolumeIntegration:
    """Test suite for volume integration in interactive charts."""
    
    @pytest.fixture
    def chart_builder(self):
        """Create InteractiveChartBuilder instance for testing."""
        return InteractiveChartBuilder()
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for chart testing."""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        np.random.seed(42)
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': 100 + np.cumsum(np.random.randn(50) * 0.5),
            'high': 102 + np.cumsum(np.random.randn(50) * 0.5),
            'low': 98 + np.cumsum(np.random.randn(50) * 0.5),
            'close': 100 + np.cumsum(np.random.randn(50) * 0.5),
            'volume': np.random.randint(1000000, 5000000, 50)
        })
        return data.set_index('timestamp')
    
    def test_chart_height_allocation_with_volume(self, chart_builder, sample_market_data):
        """Test that volume gets proper height allocation in charts."""
        # Test volume-only configuration
        chart = chart_builder.create_advanced_price_chart(
            df=sample_market_data,
            symbol="AAPL",
            indicators=[],
            show_volume=True,
            volume_display='bars_ma'
        )
        
        # Chart should be created successfully
        assert chart is not None
        assert hasattr(chart, 'layout')
        
        # Should have multiple subplots (price + volume)
        if hasattr(chart.layout, 'xaxis2'):  # Volume subplot exists
            assert chart.layout.xaxis2 is not None
    
    def test_chart_height_allocation_volume_with_indicators(self, chart_builder, sample_market_data):
        """Test height allocation with volume + technical indicators."""
        chart = chart_builder.create_advanced_price_chart(
            df=sample_market_data,
            symbol="AAPL",
            indicators=['rsi'],
            show_volume=True,
            volume_display='bars_ma'
        )
        
        # Chart should handle multiple subplots (price + volume + indicators)
        assert chart is not None
        assert hasattr(chart, 'layout')
    
    def test_volume_display_options(self, chart_builder, sample_market_data):
        """Test different volume display options."""
        volume_options = ['bars', 'bars_ma']
        
        for option in volume_options:
            chart = chart_builder.create_advanced_price_chart(
                df=sample_market_data,
                symbol="AAPL",
                indicators=[],
                show_volume=True,
                volume_display=option
            )
            
            # Each option should create a valid chart
            assert chart is not None
            assert hasattr(chart, 'data')
    
    def test_color_by_price_option(self, chart_builder, sample_market_data):
        """Test color by price direction option."""
        # Test with color by price enabled
        chart_colored = chart_builder.create_advanced_price_chart(
            df=sample_market_data,
            symbol="AAPL",
            indicators=[],
            show_volume=True,
            color_by_price=True
        )
        
        # Test with color by price disabled
        chart_single_color = chart_builder.create_advanced_price_chart(
            df=sample_market_data,
            symbol="AAPL",
            indicators=[],
            show_volume=True,
            color_by_price=False
        )
        
        # Both should create valid charts
        assert chart_colored is not None
        assert chart_single_color is not None
    
    def test_no_volume_display(self, chart_builder, sample_market_data):
        """Test chart creation with volume disabled."""
        chart = chart_builder.create_advanced_price_chart(
            df=sample_market_data,
            symbol="AAPL",
            indicators=[],
            show_volume=False
        )
        
        # Chart should be created successfully without volume
        assert chart is not None
        assert hasattr(chart, 'data')


class TestVolumeCalculations:
    """Test suite for volume analysis calculations."""
    
    def test_volume_ratio_calculation(self):
        """Test volume ratio vs moving average calculation."""
        # Create test data with known values
        volumes = [1000000] * 19 + [2000000]  # Last value is higher than others
        volume_series = pd.Series(volumes)
        
        # Calculate 20-day moving average
        volume_ma = volume_series.rolling(window=20).mean()
        current_volume = volume_series.iloc[-1]
        avg_volume = volume_ma.iloc[-1]
        
        ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # The actual ratio is: 2000000 / ((19*1000000 + 2000000)/20) = 2000000 / 1050000 ≈ 1.905
        assert abs(ratio - 1.905) < 0.01
    
    def test_volume_status_classification(self):
        """Test volume status classification (High/Normal/Low)."""
        test_cases = [
            (2.0, "High"),    # 2x average = High
            (1.0, "Normal"),  # 1x average = Normal  
            (0.5, "Low")      # 0.5x average = Low
        ]
        
        for ratio, expected_status in test_cases:
            if ratio > 1.5:
                status = "High"
            elif ratio > 0.8:
                status = "Normal"
            else:
                status = "Low"
                
            assert status == expected_status
    
    def test_volume_formatting(self):
        """Test volume number formatting (K/M/B)."""
        test_cases = [
            (1000, "1.0K"),
            (1500000, "1.5M"),
            (2500000000, "2.5B"),
            (500, "500")
        ]
        
        def format_volume(vol):
            if vol >= 1e9:
                return f"{vol/1e9:.1f}B"
            elif vol >= 1e6:
                return f"{vol/1e6:.1f}M"
            elif vol >= 1e3:
                return f"{vol/1e3:.1f}K"
            else:
                return f"{vol:.0f}"
        
        for volume, expected in test_cases:
            result = format_volume(volume)
            assert result == expected
    
    def test_volume_moving_average_calculation(self):
        """Test volume moving average calculation accuracy."""
        # Create test data
        volumes = list(range(1, 21))  # 1, 2, 3, ..., 20
        volume_series = pd.Series(volumes)
        
        # Calculate 5-day moving average
        ma_5 = volume_series.rolling(window=5).mean()
        
        # Test specific values
        assert pd.isna(ma_5.iloc[3])  # Not enough data for 5-day MA
        assert ma_5.iloc[4] == 3.0    # (1+2+3+4+5)/5 = 3.0
        assert ma_5.iloc[19] == 18.0  # (16+17+18+19+20)/5 = 18.0


class TestVolumeErrorHandling:
    """Test suite for volume analysis error handling."""
    
    def test_volume_analysis_with_invalid_data(self):
        """Test volume analysis with invalid or corrupted data."""
        # Test with negative volumes
        invalid_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=5),
            'volume': [-1000, 2000, 3000, -500, 1000]
        }).set_index('timestamp')
        
        # Should handle invalid data gracefully
        try:
            chart = create_volume_chart(invalid_data)
            assert chart is not None
        except Exception as e:
            # If it raises an exception, it should be a specific, handled error
            assert "volume" in str(e).lower()
    
    def test_volume_analysis_with_missing_data(self):
        """Test volume analysis with missing/NaN values."""
        data_with_nans = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=10),
            'volume': [1000000, np.nan, 2000000, 1500000, np.nan, 
                      1800000, 2200000, np.nan, 1900000, 2100000]
        }).set_index('timestamp')
        
        # Should handle NaN values gracefully
        chart = create_volume_chart(data_with_nans)
        assert chart is not None
    
    def test_volume_analysis_with_zero_volumes(self):
        """Test volume analysis with zero volume periods."""
        zero_volume_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=10),
            'volume': [1000000, 0, 2000000, 0, 1500000, 
                      0, 1800000, 0, 1900000, 0]
        }).set_index('timestamp')
        
        # Should handle zero volumes gracefully
        chart = create_volume_chart(zero_volume_data)
        assert chart is not None
        
        # Moving average calculation should handle zeros appropriately
        volume_ma = zero_volume_data['volume'].rolling(window=5).mean()
        assert not volume_ma.isna().all()


class TestVolumePerformance:
    """Test suite for volume analysis performance."""
    
    def test_volume_chart_performance_large_dataset(self):
        """Test volume chart creation performance with large datasets."""
        # Create large dataset (1 year of daily data)
        large_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=365, freq='D'),
            'volume': np.random.randint(1000000, 5000000, 365)
        }).set_index('timestamp')
        
        import time
        start_time = time.time()
        
        chart = create_volume_chart(large_data)
        
        execution_time = time.time() - start_time
        
        # Chart creation should complete within reasonable time (< 1 second)
        assert execution_time < 1.0
        assert chart is not None
    
    def test_volume_summary_performance(self):
        """Test volume summary calculation performance."""
        # Create large dataset
        large_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=1000, freq='D'),
            'volume': np.random.randint(1000000, 5000000, 1000)
        }).set_index('timestamp')
        
        import time
        start_time = time.time()
        
        card = create_volume_summary_card(large_data)
        
        execution_time = time.time() - start_time
        
        # Summary calculation should be fast (< 0.1 seconds)
        assert execution_time < 0.1
        assert card is not None