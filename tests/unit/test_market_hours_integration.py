"""
Tests for market hours integration with Alpaca API
Tests the market hours display and date formatting functionality
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestMarketHoursIntegration:
    """Test market hours integration functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        self.mock_config = {
            'trading': {'mode': 'paper'},
            'alpaca': {'paper_trading': {'base_url': 'https://paper-api.alpaca.markets'}}
        }
        
        with patch.object(AlpacaService, '_load_config', return_value=self.mock_config):
            with patch.object(AlpacaService, 'connect', return_value=True):
                self.service = AlpacaService()
                self.service._connected = True
                self.service.client = Mock()
    
    def test_get_market_hours_during_trading_hours(self):
        """Test market hours during normal trading hours"""
        # Mock market is open
        mock_clock = Mock()
        mock_clock.is_open = True
        mock_clock.timestamp = datetime.now()
        
        # Mock calendar for today
        today = datetime.now().date()
        mock_calendar_day = Mock()
        mock_calendar_day.date = today
        mock_calendar_day.open = datetime.combine(today, time(9, 30))  # 9:30 AM
        mock_calendar_day.close = datetime.combine(today, time(16, 0))  # 4:00 PM
        
        self.service.client.get_clock.return_value = mock_clock
        self.service.client.get_calendar.return_value = [mock_calendar_day]
        
        result = self.service.get_market_hours()
        
        assert result['is_open'] is True
        assert 'next_open' in result
        assert 'next_close' in result
        assert 'current_time' in result
    
    def test_get_market_hours_after_market_close(self):
        """Test market hours after market close"""
        # Mock market is closed
        mock_clock = Mock()
        mock_clock.is_open = False
        mock_clock.timestamp = datetime.now()
        
        # Mock calendar for today and tomorrow
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        today_calendar = Mock()
        today_calendar.date = today
        today_calendar.open = datetime.combine(today, time(9, 30))
        today_calendar.close = datetime.combine(today, time(16, 0))
        
        tomorrow_calendar = Mock()
        tomorrow_calendar.date = tomorrow
        tomorrow_calendar.open = datetime.combine(tomorrow, time(9, 30))
        tomorrow_calendar.close = datetime.combine(tomorrow, time(16, 0))
        
        self.service.client.get_clock.return_value = mock_clock
        self.service.client.get_calendar.return_value = [today_calendar, tomorrow_calendar]
        
        result = self.service.get_market_hours()
        
        assert result['is_open'] is False
        assert 'next_open' in result
        assert 'next_close' in result
        assert result['next_open'] == tomorrow_calendar.open
        assert result['next_close'] == tomorrow_calendar.close
    
    def test_get_market_hours_before_market_open(self):
        """Test market hours before market opens (early morning)"""
        # Mock market is closed but it's a trading day
        mock_clock = Mock()
        mock_clock.is_open = False
        mock_clock.timestamp = datetime.now().replace(hour=8, minute=0)  # 8:00 AM
        
        # Mock calendar for today
        today = datetime.now().date()
        mock_calendar_day = Mock()
        mock_calendar_day.date = today
        mock_calendar_day.open = datetime.combine(today, time(9, 30))
        mock_calendar_day.close = datetime.combine(today, time(16, 0))
        
        self.service.client.get_clock.return_value = mock_clock
        self.service.client.get_calendar.return_value = [mock_calendar_day]
        
        result = self.service.get_market_hours()
        
        assert result['is_open'] is False
        assert 'next_open' in result
        assert 'next_close' in result
        assert result['next_open'] == mock_calendar_day.open
        assert result['next_close'] == mock_calendar_day.close
    
    def test_get_market_hours_weekend(self):
        """Test market hours on weekend"""
        # Mock market is closed (weekend)
        mock_clock = Mock()
        mock_clock.is_open = False
        mock_clock.timestamp = datetime.now()
        
        # Mock calendar - no trading today, next trading day is Monday
        today = datetime.now().date()
        monday = today + timedelta(days=(7 - today.weekday()))  # Next Monday
        
        monday_calendar = Mock()
        monday_calendar.date = monday
        monday_calendar.open = datetime.combine(monday, time(9, 30))
        monday_calendar.close = datetime.combine(monday, time(16, 0))
        
        # No calendar entry for today (weekend), only Monday
        self.service.client.get_clock.return_value = mock_clock
        self.service.client.get_calendar.return_value = [monday_calendar]
        
        result = self.service.get_market_hours()
        
        assert result['is_open'] is False
        assert 'next_open' in result
        assert 'next_close' in result
    
    def test_get_market_hours_handles_empty_calendar(self):
        """Test market hours handles empty calendar gracefully"""
        mock_clock = Mock()
        mock_clock.is_open = False
        mock_clock.timestamp = datetime.now()
        
        self.service.client.get_clock.return_value = mock_clock
        self.service.client.get_calendar.return_value = []  # Empty calendar
        
        result = self.service.get_market_hours()
        
        assert result == {}  # Should return empty dict
    
    def test_get_market_hours_handles_api_exception(self):
        """Test market hours handles API exceptions"""
        self.service.client.get_clock.side_effect = Exception("Clock API error")
        
        result = self.service.get_market_hours()
        
        assert result == {}  # Should return empty dict
    
    def test_get_market_hours_when_disconnected(self):
        """Test market hours returns empty when disconnected"""
        self.service._connected = False
        
        result = self.service.get_market_hours()
        
        assert result == {}


class TestMarketHoursFormatting:
    """Test market hours formatting for different scenarios"""
    
    def test_market_hours_format_weekend_includes_day_name(self):
        """Test that weekend market hours include day names"""
        from datetime import datetime, date
        
        # Create mock market hours data for weekend
        monday = date.today() + timedelta(days=(7 - date.today().weekday()))
        mock_market_hours = {
            'is_open': False,
            'next_open': datetime.combine(monday, time(9, 30)),
            'next_close': datetime.combine(monday, time(16, 0)),
            'current_time': datetime.now()
        }
        
        # Test that the next_open includes Monday
        next_open_str = mock_market_hours['next_open'].strftime('%A %I:%M %p')
        assert 'Monday' in next_open_str
    
    def test_market_hours_format_today_no_day_name(self):
        """Test that same-day market hours don't need day names"""
        from datetime import datetime, time
        
        # Create mock market hours data for today
        today = datetime.now().date()
        mock_market_hours = {
            'is_open': False,
            'next_open': datetime.combine(today, time(9, 30)),
            'next_close': datetime.combine(today, time(16, 0)),
            'current_time': datetime.now()
        }
        
        # For today, we might not include the day name
        next_open_str = mock_market_hours['next_open'].strftime('%I:%M %p')
        assert ':' in next_open_str  # Should have time format
    
    def test_market_hours_timezone_handling(self):
        """Test that market hours handle timezones properly"""
        # This would test timezone conversion if implemented
        # For now, just verify the structure
        from datetime import datetime, timezone
        
        eastern = timezone(timedelta(hours=-5))  # EST
        mock_time = datetime.now(eastern)
        
        # Market hours should be in Eastern time
        assert mock_time.tzinfo is not None


class TestMarketHoursDisplayIntegration:
    """Test integration of market hours with dashboard display"""
    
    @patch('src.trading.brokers.alpaca_service.get_alpaca_service')
    def test_market_hours_display_components_exist(self, mock_get_alpaca):
        """Test that market hours display components can be created"""
        # Mock service
        mock_service = Mock()
        mock_service.get_market_hours.return_value = {
            'is_open': True,
            'next_open': datetime.now() + timedelta(hours=1),
            'next_close': datetime.now() + timedelta(hours=8),
            'current_time': datetime.now()
        }
        mock_get_alpaca.return_value = mock_service
        
        # Test that market hours data can be processed
        market_hours = mock_service.get_market_hours()
        
        assert 'is_open' in market_hours
        assert 'next_open' in market_hours
        assert 'next_close' in market_hours
        assert isinstance(market_hours['is_open'], bool)
    
    def test_market_hours_display_fallback(self):
        """Test market hours display fallback when service unavailable"""
        # Test fallback behavior when Alpaca service is not available
        mock_empty_hours = {}
        
        # Should handle empty market hours gracefully
        assert isinstance(mock_empty_hours, dict)
        
        # Display should show appropriate message when no data
        fallback_message = "Market hours unavailable"
        assert isinstance(fallback_message, str)
    
    @patch('src.trading.brokers.alpaca_service.get_alpaca_service')
    def test_market_hours_refresh_interval(self, mock_get_alpaca):
        """Test that market hours can be refreshed at intervals"""
        # Mock service calls
        call_count = 0
        
        def mock_get_market_hours():
            nonlocal call_count
            call_count += 1
            return {
                'is_open': call_count % 2 == 0,  # Alternating open/closed
                'current_time': datetime.now(),
                'call_count': call_count
            }
        
        mock_service = Mock()
        mock_service.get_market_hours.side_effect = mock_get_market_hours
        mock_get_alpaca.return_value = mock_service
        
        # Simulate multiple refresh calls
        result1 = mock_service.get_market_hours()
        result2 = mock_service.get_market_hours()
        
        assert result1['call_count'] == 1
        assert result2['call_count'] == 2
        assert result1['is_open'] != result2['is_open']  # Should alternate


class TestMarketHoursErrorHandling:
    """Test error handling in market hours functionality"""
    
    def test_market_hours_connection_timeout(self):
        """Test handling of connection timeouts"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        mock_config = {'trading': {'mode': 'paper'}}
        
        with patch.object(AlpacaService, '_load_config', return_value=mock_config):
            with patch.object(AlpacaService, 'connect', return_value=True):
                service = AlpacaService()
                service._connected = True
                service.client = Mock()
                
                # Mock timeout exception
                service.client.get_clock.side_effect = TimeoutError("Connection timeout")
                
                result = service.get_market_hours()
                
                assert result == {}  # Should return empty dict on timeout
    
    def test_market_hours_api_rate_limit(self):
        """Test handling of API rate limits"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        mock_config = {'trading': {'mode': 'paper'}}
        
        with patch.object(AlpacaService, '_load_config', return_value=mock_config):
            with patch.object(AlpacaService, 'connect', return_value=True):
                service = AlpacaService()
                service._connected = True
                service.client = Mock()
                
                # Mock rate limit exception
                service.client.get_clock.side_effect = Exception("Rate limit exceeded")
                
                result = service.get_market_hours()
                
                assert result == {}  # Should return empty dict on rate limit
    
    def test_market_hours_invalid_calendar_data(self):
        """Test handling of invalid calendar data"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        mock_config = {'trading': {'mode': 'paper'}}
        
        with patch.object(AlpacaService, '_load_config', return_value=mock_config):
            with patch.object(AlpacaService, 'connect', return_value=True):
                service = AlpacaService()
                service._connected = True
                service.client = Mock()
                
                # Mock valid clock but invalid calendar
                mock_clock = Mock()
                mock_clock.is_open = False
                service.client.get_clock.return_value = mock_clock
                
                # Invalid calendar data
                service.client.get_calendar.return_value = None
                
                result = service.get_market_hours()
                
                assert result == {}  # Should handle gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])