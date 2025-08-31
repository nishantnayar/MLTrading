"""
Optimized dashboard tests demonstrating best practices.

This file shows how to use the new test utilities for better performance
and maintainability compared to the original test files.
"""

import pytest
import time
from test_utils.helpers import DashTestHelper, TestHelper, PerformanceTestHelper
from test_utils.data_generators import MarketDataGenerator
from test_utils.mocks import MockedServices


# Use session-scoped app fixture to avoid repeated startups
@pytest.mark.unit
class TestOptimizedDashboard:
    """Optimized dashboard tests with shared resources"""
    
    @pytest.fixture(scope="class")  # Class scope to share between test methods
    def started_app(self, app, dash_duo):
        """Start app once for the entire test class"""
        dash_duo.start_server(app)
        dash_duo.wait_for_element("#page-content", timeout=10)
        yield dash_duo
        # Cleanup happens automatically
    
    def test_app_startup_performance(self, started_app, performance_config):
        """Test app starts within performance benchmark"""
        def load_page():
            started_app.driver.refresh()
            started_app.wait_for_element("#main-tabs", timeout=10)
            return True
        
        # Use performance helper
        result = PerformanceTestHelper.assert_performance_benchmark(
            load_page, 
            performance_config['max_dashboard_load_time']
        )
        assert result
    
    def test_navigation_optimized(self, started_app, suppressed_logging):
        """Test navigation with optimized element interaction"""
        helper = DashTestHelper(started_app)
        
        # Use helper methods for reliable interaction
        assert helper.wait_for_element_with_retry("#nav-trading", timeout=5)
        assert helper.safe_click("#nav-trading")
        
        # Verify navigation without stale element issues
        trading_text = helper.get_text_with_retry("#nav-trading")
        assert "Trading" in trading_text
        
        # Assert no console errors using helper
        helper.assert_no_console_errors()
    
    def test_chart_rendering_with_mock_data(self, started_app, sample_market_data):
        """Test chart rendering with consistent mock data"""
        helper = DashTestHelper(started_app)
        
        # Wait for charts to load
        with helper.performance_timer(max_duration=5.0):
            helper.wait_for_element_with_retry("#sector-distribution-chart")
            helper.wait_for_element_with_retry("#top-volume-chart")
        
        # Verify charts are rendered (basic check)
        sector_chart = started_app.find_element("#sector-distribution-chart")
        assert sector_chart is not None
        
        helper.assert_no_console_errors()


@pytest.mark.integration
class TestOptimizedIntegration:
    """Integration tests with optimized setup"""
    
    def test_data_service_integration(self, mock_data_service, sample_market_data):
        """Test data service integration with optimized mocking"""
        # Use the optimized mock data service
        symbols = mock_data_service.get_available_symbols()
        assert len(symbols) == len(sample_market_data["symbols"])
        
        # Test market data retrieval
        market_data = mock_data_service.get_market_data("AAPL")
        assert not market_data.empty
        assert "close" in market_data.columns
    
    def test_technical_indicators_with_generated_data(self, technical_indicator_data):
        """Test technical indicators with purpose-built test data"""
        try:
            from src.dashboard.services.technical_indicators import TechnicalIndicatorService
            
            service = TechnicalIndicatorService()
            rsi_values = service.calculate_rsi(technical_indicator_data, period=14)
            
            # Verify RSI calculation
            assert not rsi_values.empty
            assert all(0 <= val <= 100 for val in rsi_values.dropna())
            
        except ImportError:
            pytest.skip("Technical indicators service not available")


@pytest.mark.performance
class TestPerformanceOptimized:
    """Performance tests with benchmarking"""
    
    def test_large_dataset_handling(self, large_market_dataset, performance_config):
        """Test performance with large datasets"""
        
        def process_large_dataset():
            # Simulate data processing
            result = large_market_dataset.groupby('symbol')['volume'].mean()
            return len(result)
        
        # Test with performance benchmark
        result, execution_time = PerformanceTestHelper.measure_execution_time(
            process_large_dataset
        )
        
        assert result > 0
        assert execution_time < 2.0  # Should process quickly
        
        # Optional memory test
        try:
            result, memory_used = PerformanceTestHelper.memory_usage_test(
                process_large_dataset,
                max_memory_mb=50
            )
            assert memory_used < 50
        except ImportError:
            pytest.skip("Memory testing requires psutil")
    
    @pytest.mark.slow
    def test_stress_test_with_multiple_symbols(self, performance_config):
        """Stress test with multiple symbols (marked as slow)"""
        generator = MarketDataGenerator(seed=123)
        
        # Generate data for many symbols
        symbols = [f"STRESS{i:03d}" for i in range(50)]
        
        start_time = time.time()
        data = generator.generate_multiple_symbols(symbols, periods=100)
        end_time = time.time()
        
        # Verify performance
        assert end_time - start_time < 5.0  # Should complete in 5 seconds
        assert len(data) == 50 * 100  # 50 symbols × 100 periods


@pytest.mark.unit
class TestOptimizedAlerts:
    """Optimized alert system tests"""
    
    def test_alert_creation_with_helper(self, alert_test_config):
        """Test alert creation using test helpers"""
        from test_utils.helpers import AlertTestHelper
        from src.utils.alerts import AlertManager
        
        # Create manager with test config
        alert_manager = AlertManager(alert_test_config)
        
        # Use helper to create test alert
        test_alert = AlertTestHelper.create_test_alert(
            title="Test Alert",
            severity="HIGH",
            metadata={"test_id": "opt_001"}
        )
        
        # Process alert
        status = alert_manager.process_alert(test_alert)
        
        # Use helper to verify
        if status.value == "sent":
            AlertTestHelper.assert_alert_sent(alert_manager, expected_count=1)
    
    def test_email_service_with_mock(self):
        """Test email service with comprehensive mock"""
        from test_utils.helpers import AlertTestHelper
        from src.utils.alerts.models import AlertSeverity, AlertCategory, Alert
        from datetime import datetime, timezone
        
        # Create mock email service
        mock_service = AlertTestHelper.mock_email_service(should_succeed=True)
        
        # Create test alert
        alert = Alert(
            title="Mock Test",
            message="Testing with mock service",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.SYSTEM_HEALTH,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Test service
        assert mock_service.is_available()
        result = mock_service.send_alert(alert)
        assert result is True
        
        status = mock_service.get_status()
        assert status['available'] is True


# Example of parametrized test with optimized data
@pytest.mark.parametrize("symbol,expected_min_records", [
    ("AAPL", 30),
    ("GOOGL", 30),
    ("MSFT", 30)
])
def test_market_data_generation_parametrized(symbol, expected_min_records):
    """Test market data generation for multiple symbols"""
    generator = MarketDataGenerator()
    data = generator.generate_ohlcv_data(symbol=symbol, periods=50)
    
    assert len(data) >= expected_min_records
    assert data['symbol'].iloc[0] == symbol
    assert all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume'])


# Example of fixture-scoped optimization
@pytest.fixture(scope="module")
def expensive_computation_result():
    """Expensive computation done once per module"""
    # Simulate expensive setup
    generator = MarketDataGenerator()
    large_dataset = generator.generate_multiple_symbols(
        symbols=[f"BULK{i:03d}" for i in range(20)],
        periods=500
    )
    
    # Pre-compute expensive aggregations
    result = {
        'total_records': len(large_dataset),
        'symbols': large_dataset['symbol'].unique().tolist(),
        'date_range': (large_dataset['timestamp'].min(), large_dataset['timestamp'].max()),
        'volume_stats': large_dataset.groupby('symbol')['volume'].agg(['mean', 'std']).to_dict()
    }
    
    return result


def test_using_expensive_computation(expensive_computation_result):
    """Test using pre-computed expensive result"""
    result = expensive_computation_result
    
    assert result['total_records'] > 0
    assert len(result['symbols']) == 20
    assert 'mean' in result['volume_stats']
    assert 'std' in result['volume_stats']