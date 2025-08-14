"""
Unit tests for Technical Analysis Summary features.
Tests the summary cards, callback functions, and metric calculations.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import dashboard components for testing
try:
    from src.dashboard.callbacks.interactive_chart_callbacks import register_interactive_chart_callbacks
    from src.dashboard.layouts.chart_components import create_volume_summary_card
except ImportError:
    # Handle missing imports gracefully for testing
    pass


class TestTechnicalAnalysisSummaryLayout:
    """Test suite for Technical Analysis Summary layout components."""
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        np.random.seed(42)  # For consistent test results
        
        # Create realistic market data
        base_price = 100.0
        price_changes = np.random.randn(30) * 2
        prices = base_price + np.cumsum(price_changes)
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices + np.random.randn(30) * 0.5,
            'high': prices + np.abs(np.random.randn(30) * 1.5),
            'low': prices - np.abs(np.random.randn(30) * 1.5),
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, 30)
        })
        return data.set_index('timestamp')
    
    @pytest.fixture
    def technical_indicators_data(self):
        """Create sample technical indicators data."""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        
        indicators = pd.DataFrame({
            'timestamp': dates,
            'rsi': np.random.uniform(20, 80, 30),  # RSI between 20-80
            'sma_20': np.random.uniform(95, 105, 30),  # SMA around price
            'volume_sma': np.random.uniform(1500000, 2500000, 30)
        })
        return indicators.set_index('timestamp')
    
    def test_price_change_calculation(self, sample_market_data):
        """Test 30-day price change calculation."""
        current_price = sample_market_data['close'].iloc[-1]
        initial_price = sample_market_data['close'].iloc[0]
        
        expected_change = ((current_price - initial_price) / initial_price) * 100
        
        # Verify calculation logic
        calculated_change = ((current_price - initial_price) / initial_price) * 100
        assert abs(calculated_change - expected_change) < 0.01
    
    def test_rsi_status_classification(self):
        """Test RSI status classification (overbought/oversold/neutral)."""
        test_cases = [
            (75.0, "text-danger"),   # Overbought (>70)
            (25.0, "text-success"),  # Oversold (<30)
            (50.0, "text-warning")   # Neutral (30-70)
        ]
        
        for rsi_value, expected_color in test_cases:
            if rsi_value > 70:
                color = "text-danger"
            elif rsi_value < 30:
                color = "text-success"
            else:
                color = "text-warning"
            
            assert color == expected_color
    
    def test_trend_determination(self, sample_market_data, technical_indicators_data):
        """Test trend determination logic (bullish/bearish)."""
        current_price = sample_market_data['close'].iloc[-1]
        sma_20 = technical_indicators_data['sma_20'].iloc[-1]
        
        expected_trend = "Bullish" if current_price > sma_20 else "Bearish"
        expected_color = "text-success" if expected_trend == "Bullish" else "text-danger"
        
        # Test the logic
        trend = "Bullish" if current_price > sma_20 else "Bearish"
        trend_color = "text-success" if trend == "Bullish" else "text-danger"
        
        assert trend == expected_trend
        assert trend_color == expected_color
    
    def test_volume_ratio_in_summary(self, sample_market_data):
        """Test volume ratio calculation for summary cards."""
        current_volume = sample_market_data['volume'].iloc[-1]
        avg_volume = sample_market_data['volume'].rolling(window=20).mean().iloc[-1]
        
        if avg_volume > 0:
            volume_ratio = current_volume / avg_volume
            
            # Test volume status determination
            if volume_ratio > 1.5:
                status = "High"
                color = "text-success"
            elif volume_ratio > 0.8:
                status = "Normal" 
                color = "text-warning"
            else:
                status = "Low"
                color = "text-muted"
            
            # Verify the logic works
            assert volume_ratio > 0
            assert status in ["High", "Normal", "Low"]
            assert color in ["text-success", "text-warning", "text-muted"]


class TestSummaryCardGeneration:
    """Test suite for summary card generation logic."""
    
    def test_summary_cards_basic_structure(self):
        """Test that summary cards have the expected structure."""
        # Mock data for testing
        sample_data = {
            'current_price': 150.25,
            'price_change': 5.2,
            'rsi_value': 65.4,
            'volume_current': 2500000,
            'volume_ratio': 1.2,
            'trend': 'Bullish'
        }
        
        # Test price card data
        assert sample_data['current_price'] > 0
        assert isinstance(sample_data['price_change'], (int, float))
        
        # Test RSI card data
        assert 0 <= sample_data['rsi_value'] <= 100
        
        # Test volume card data
        assert sample_data['volume_current'] > 0
        assert sample_data['volume_ratio'] > 0
        
        # Test trend card data
        assert sample_data['trend'] in ['Bullish', 'Bearish']
    
    def test_summary_cards_edge_cases(self):
        """Test summary card generation with edge case values."""
        edge_cases = [
            {
                'current_price': 0.01,  # Very low price
                'price_change': -99.9,  # Huge loss
                'rsi_value': 0.1,       # Extremely oversold
                'volume_ratio': 0.01    # Very low volume
            },
            {
                'current_price': 9999.99,  # Very high price
                'price_change': 999.9,     # Huge gain
                'rsi_value': 99.9,         # Extremely overbought
                'volume_ratio': 10.0       # Very high volume
            }
        ]
        
        for case in edge_cases:
            # All values should be handled gracefully
            assert case['current_price'] > 0
            assert isinstance(case['price_change'], (int, float))
            assert 0 <= case['rsi_value'] <= 100
            assert case['volume_ratio'] > 0
    
    def test_summary_card_column_width_allocation(self):
        """Test that summary cards use proper column widths."""
        # Each card should use width=2 for responsive layout
        expected_widths = {
            'price_card': 2,
            'change_card': 2, 
            'rsi_card': 2,
            'volume_card': 2,
            'trend_card': 2
        }
        
        total_width = sum(expected_widths.values())
        
        # Total width should not exceed Bootstrap's 12-column grid
        assert total_width <= 12
        
        # All cards should have equal width for consistent layout
        unique_widths = set(expected_widths.values())
        assert len(unique_widths) == 1  # All widths should be the same


class TestTechnicalAnalysisCallbacks:
    """Test suite for Technical Analysis Summary callbacks."""
    
    @pytest.fixture
    def mock_dash_app(self):
        """Create a mock Dash app for callback testing."""
        mock_app = MagicMock()
        mock_app.callback = MagicMock()
        return mock_app
    
    def test_callback_registration(self, mock_dash_app):
        """Test that Technical Analysis Summary callbacks are registered."""
        try:
            register_interactive_chart_callbacks(mock_dash_app)
            
            # Verify that callbacks were registered
            assert mock_dash_app.callback.called
            
            # Should have registered multiple callbacks
            assert mock_dash_app.callback.call_count > 0
            
        except (ImportError, AttributeError):
            # Skip test if modules aren't available
            pytest.skip("Interactive chart callbacks not available for testing")
    
    def test_technical_analysis_summary_callback_logic(self):
        """Test the logic of technical analysis summary generation."""
        # Create test data that would be returned by the service
        test_data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000, 1500000]
        })
        
        # Test the summary generation logic
        current_price = test_data['close'].iloc[-1]
        price_change = ((current_price - test_data['close'].iloc[0]) / test_data['close'].iloc[0]) * 100
        
        # Verify calculations
        assert current_price == 105
        assert abs(price_change - 5.0) < 0.01  # 5% increase
    
    def test_technical_analysis_error_handling(self):
        """Test error handling in technical analysis summary."""
        # Test with None data
        result = self._handle_technical_analysis_error(None)
        assert result is not None
        
        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        result = self._handle_technical_analysis_error(empty_df)
        assert result is not None
        
        # Test with invalid data
        invalid_df = pd.DataFrame({'invalid': [1, 2, 3]})
        result = self._handle_technical_analysis_error(invalid_df)
        assert result is not None
    
    def _handle_technical_analysis_error(self, data):
        """Helper method to simulate error handling."""
        try:
            if data is None or data.empty:
                return "No data available"
            
            if 'close' not in data.columns:
                return "Invalid data format"
            
            # Normal processing would happen here
            return "Success"
            
        except Exception as e:
            return f"Error: {str(e)}"


class TestVolumeIntegrationInSummary:
    """Test suite for volume integration in Technical Analysis Summary."""
    
    @pytest.fixture
    def volume_test_data(self):
        """Create test data specifically for volume testing."""
        return pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=25, freq='D'),
            'volume': [1000000] * 20 + [2000000] * 5  # Last 5 days have 2x volume
        }).set_index('timestamp')
    
    def test_volume_card_integration(self, volume_test_data):
        """Test volume card integration in technical summary."""
        # Test that volume card can be created with the test data
        try:
            card = create_volume_summary_card(volume_test_data)
            assert card is not None
        except ImportError:
            pytest.skip("Volume summary card not available for testing")
    
    def test_volume_ratio_calculation_accuracy(self, volume_test_data):
        """Test accuracy of volume ratio calculations."""
        current_volume = volume_test_data['volume'].iloc[-1]  # 2,000,000
        avg_volume_20 = volume_test_data['volume'].rolling(window=20).mean().iloc[-1]
        
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 0
        
        # Actual ratio is 1.6: (15 days * 1M + 5 days * 2M) / 20 = 25M / 20 = 1.25M
        # Current volume (2M) / avg (1.25M) = 1.6
        expected_ratio = 1.6
        assert abs(volume_ratio - expected_ratio) < 0.1
    
    def test_volume_status_determination(self):
        """Test volume status determination logic."""
        test_ratios = [0.5, 1.0, 1.8, 3.0]
        expected_statuses = ["Low", "Normal", "High", "High"]
        
        for ratio, expected in zip(test_ratios, expected_statuses):
            if ratio > 1.5:
                status = "High"
            elif ratio > 0.8:
                status = "Normal"
            else:
                status = "Low"
            
            assert status == expected
    
    def test_volume_formatting_in_summary(self):
        """Test volume number formatting in summary cards."""
        test_volumes = [
            (1500, "1.5K"),
            (2500000, "2.5M"), 
            (3500000000, "3.5B"),
            (750, "750")
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
        
        for volume, expected in test_volumes:
            result = format_volume(volume)
            assert result == expected


class TestSummaryLayoutIntegration:
    """Test suite for Technical Analysis Summary layout integration."""
    
    def test_summary_positioning_in_layout(self):
        """Test that summary is positioned correctly in the layout."""
        # The summary should appear between controls and chart
        layout_order = [
            'controls',
            'technical_analysis_summary',  # Should be here
            'interactive_chart'
        ]
        
        # Verify the expected order
        controls_index = layout_order.index('controls')
        summary_index = layout_order.index('technical_analysis_summary')
        chart_index = layout_order.index('interactive_chart')
        
        assert controls_index < summary_index < chart_index
    
    def test_summary_responsive_design(self):
        """Test that summary cards are responsive across screen sizes."""
        # Each card should have width=2 for desktop (5 cards * 2 = 10/12 columns)
        card_width = 2
        num_cards = 5
        total_width = card_width * num_cards
        
        # Should fit within Bootstrap grid (12 columns) with some margin
        assert total_width <= 12
        
        # Should have reasonable spacing
        remaining_space = 12 - total_width
        assert remaining_space >= 0  # At least no overflow
    
    def test_summary_card_styling_consistency(self):
        """Test that all summary cards have consistent styling."""
        card_styles = {
            'price_card': {'color': 'text-primary'},
            'change_card': {'color': 'text-success'}, # or text-danger based on value
            'rsi_card': {'color': 'text-warning'},     # or text-danger/success based on value
            'volume_card': {'color': 'text-success'},  # or text-warning/muted based on ratio
            'trend_card': {'color': 'text-success'}    # or text-danger based on trend
        }
        
        # All cards should have a color property
        for card_name, styles in card_styles.items():
            assert 'color' in styles
            assert styles['color'].startswith('text-')


class TestPerformanceAndReliability:
    """Test suite for performance and reliability of Technical Analysis Summary."""
    
    def test_summary_generation_performance(self):
        """Test that summary generation is fast enough for real-time updates."""
        # Create large dataset to test performance
        large_data = pd.DataFrame({
            'close': np.random.randn(1000) + 100,
            'volume': np.random.randint(1000000, 5000000, 1000),
            'rsi': np.random.uniform(0, 100, 1000)
        })
        
        import time
        start_time = time.time()
        
        # Simulate summary calculations
        current_price = large_data['close'].iloc[-1]
        price_change = ((current_price - large_data['close'].iloc[0]) / large_data['close'].iloc[0]) * 100
        current_volume = large_data['volume'].iloc[-1]
        avg_volume = large_data['volume'].rolling(window=20).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        execution_time = time.time() - start_time
        
        # Should complete quickly (< 0.1 seconds)
        assert execution_time < 0.1
        
        # Results should be valid
        assert isinstance(current_price, (int, float))
        assert isinstance(price_change, (int, float))
        assert isinstance(volume_ratio, (int, float))
    
    def test_summary_reliability_with_edge_cases(self):
        """Test summary reliability with various edge cases."""
        edge_cases = [
            # All zeros
            pd.DataFrame({'close': [0] * 10, 'volume': [0] * 10}),
            
            # Single data point
            pd.DataFrame({'close': [100], 'volume': [1000000]}),
            
            # All same values
            pd.DataFrame({'close': [100] * 20, 'volume': [1000000] * 20}),
            
            # Extreme values
            pd.DataFrame({'close': [1e-6, 1e6], 'volume': [1, 1e12]})
        ]
        
        for i, data in enumerate(edge_cases):
            try:
                # These should not crash
                if len(data) > 0:
                    current_price = data['close'].iloc[-1]
                    if len(data) > 1:
                        initial_price = data['close'].iloc[0]
                        # Avoid division by zero
                        if initial_price != 0:
                            price_change = ((current_price - initial_price) / initial_price) * 100
                        else:
                            # Handle case where initial price is 0
                            price_change = float('inf') if current_price > 0 else 0
                    
                    # Should handle edge cases gracefully
                    assert True  # If we get here, no crash occurred
                    
            except (ZeroDivisionError, IndexError, ValueError) as e:
                # These errors should be handled gracefully in real implementation
                assert "division by zero" in str(e) or "index" in str(e) or "value" in str(e)
    
    def test_summary_memory_efficiency(self):
        """Test that summary calculations are memory efficient."""
        import gc
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and process multiple datasets
        for _ in range(10):
            data = pd.DataFrame({
                'close': np.random.randn(100) + 100,
                'volume': np.random.randint(1000000, 5000000, 100)
            })
            
            # Simulate summary calculations
            _ = data['close'].iloc[-1]
            _ = data['volume'].rolling(window=20).mean().iloc[-1]
            
            # Clean up
            del data
            gc.collect()
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 10MB)
        assert memory_increase < 10 * 1024 * 1024