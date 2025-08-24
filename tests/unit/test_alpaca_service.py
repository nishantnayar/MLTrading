"""
Unit tests for AlpacaService
Tests the core trading functionality and API integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from datetime import datetime, timedelta
import pandas as pd
import yaml
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestAlpacaServiceInitialization:
    """Test AlpacaService initialization and configuration"""
    
    @patch('src.trading.brokers.alpaca_service.ALPACA_AVAILABLE', True)
    @patch('src.trading.brokers.alpaca_service.load_dotenv')
    def test_config_loading_success(self, mock_load_dotenv):
        """Test successful configuration loading"""
        with patch('builtins.open', create=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = """
trading:
  mode: "paper"
alpaca:
  paper_trading:
    base_url: "https://paper-api.alpaca.markets"
  live_trading:
    base_url: "https://api.alpaca.markets"
risk:
  emergency_stop: false
  max_position_size: 1000
"""
            with patch('yaml.safe_load') as mock_yaml:
                mock_yaml.return_value = {
                    'trading': {'mode': 'paper'},
                    'alpaca': {
                        'paper_trading': {'base_url': 'https://paper-api.alpaca.markets'},
                        'live_trading': {'base_url': 'https://api.alpaca.markets'}
                    },
                    'risk': {'emergency_stop': False, 'max_position_size': 1000}
                }
                
                from src.trading.brokers.alpaca_service import AlpacaService
                
                with patch.object(AlpacaService, 'connect', return_value=True):
                    service = AlpacaService()
                    assert service.config['trading']['mode'] == 'paper'
    
    def test_invalid_trading_mode_raises_error(self):
        """Test that invalid trading mode raises ValueError"""
        with patch('builtins.open', create=True):
            with patch('yaml.safe_load') as mock_yaml:
                mock_yaml.return_value = {
                    'trading': {'mode': 'invalid_mode'},
                    'alpaca': {
                        'paper_trading': {'base_url': 'https://paper-api.alpaca.markets'},
                        'live_trading': {'base_url': 'https://api.alpaca.markets'}
                    }
                }
                
                from src.trading.brokers.alpaca_service import AlpacaService
                
                with pytest.raises(ValueError, match="Invalid trading mode: invalid_mode"):
                    with patch.object(AlpacaService, 'connect'):
                        AlpacaService()
    
    def test_missing_config_file_raises_error(self):
        """Test that missing config file raises FileNotFoundError"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        with patch('builtins.open', side_effect=FileNotFoundError("Config not found")):
            with pytest.raises(FileNotFoundError):
                with patch.object(AlpacaService, 'connect'):
                    AlpacaService()


class TestAlpacaServiceConnection:
    """Test AlpacaService connection functionality"""
    
    @patch('src.trading.brokers.alpaca_service.ALPACA_AVAILABLE', False)
    def test_connection_fails_when_alpaca_unavailable(self):
        """Test connection fails when Alpaca API is not available"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        with patch.object(AlpacaService, '_load_config', return_value={'trading': {'mode': 'paper'}}):
            service = AlpacaService()
            result = service.connect()
            assert result is False
            assert service._connected is False
    
    @patch('src.trading.brokers.alpaca_service.ALPACA_AVAILABLE', True)
    @patch.dict(os.environ, {
        'ALPACA_PAPER_API_KEY': 'test_key',
        'ALPACA_PAPER_SECRET_KEY': 'test_secret'
    })
    def test_successful_paper_connection(self):
        """Test successful connection to paper trading"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        mock_config = {
            'trading': {'mode': 'paper'},
            'alpaca': {'paper_trading': {'base_url': 'https://paper-api.alpaca.markets'}}
        }
        
        with patch.object(AlpacaService, '_load_config', return_value=mock_config):
            with patch('src.trading.brokers.alpaca_service.REST') as mock_rest:
                mock_client = Mock()
                mock_account = Mock()
                mock_account.id = 'test_account_id'
                mock_account.buying_power = '10000.00'
                mock_account.portfolio_value = '15000.00'
                
                mock_client.get_account.return_value = mock_account
                mock_rest.return_value = mock_client
                
                service = AlpacaService()
                assert service._connected is True
                assert service.client is not None
    
    @patch('src.trading.brokers.alpaca_service.ALPACA_AVAILABLE', True)
    @patch.dict(os.environ, {}, clear=True)
    def test_connection_fails_missing_credentials(self):
        """Test connection fails when credentials are missing"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        mock_config = {
            'trading': {'mode': 'paper'},
            'alpaca': {'paper_trading': {'base_url': 'https://paper-api.alpaca.markets'}}
        }
        
        with patch.object(AlpacaService, '_load_config', return_value=mock_config):
            service = AlpacaService()
            result = service.connect()
            assert result is False
            assert service._connected is False
    
    @patch('src.trading.brokers.alpaca_service.ALPACA_AVAILABLE', True)
    @patch.dict(os.environ, {
        'ALPACA_LIVE_API_KEY': 'test_live_key',
        'ALPACA_LIVE_SECRET_KEY': 'test_live_secret'
    })
    def test_successful_live_connection(self):
        """Test successful connection to live trading"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        mock_config = {
            'trading': {'mode': 'live'},
            'alpaca': {'live_trading': {'base_url': 'https://api.alpaca.markets'}}
        }
        
        with patch.object(AlpacaService, '_load_config', return_value=mock_config):
            with patch('src.trading.brokers.alpaca_service.REST') as mock_rest:
                mock_client = Mock()
                mock_account = Mock()
                mock_account.id = 'live_account_id'
                mock_account.buying_power = '50000.00'
                mock_account.portfolio_value = '75000.00'
                
                mock_client.get_account.return_value = mock_account
                mock_rest.return_value = mock_client
                
                service = AlpacaService()
                assert service._connected is True
                assert service.client is not None


class TestAlpacaServiceAccountOperations:
    """Test account-related operations"""
    
    def setup_method(self):
        """Set up mock service for each test"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        self.mock_config = {
            'trading': {'mode': 'paper'},
            'risk': {'emergency_stop': False, 'max_position_size': 1000}
        }
        
        with patch.object(AlpacaService, '_load_config', return_value=self.mock_config):
            with patch.object(AlpacaService, 'connect', return_value=True):
                self.service = AlpacaService()
                self.service._connected = True
                self.service.client = Mock()
    
    def test_get_account_info_success(self):
        """Test successful account info retrieval"""
        mock_account = Mock()
        mock_account.id = 'account_123'
        mock_account.buying_power = '10000.50'
        mock_account.portfolio_value = '15000.75'
        mock_account.cash = '5000.25'
        mock_account.daytrading_buying_power = '40000.00'
        mock_account.trading_blocked = False
        mock_account.account_blocked = False
        mock_account.pattern_day_trader = False
        
        self.service.client.get_account.return_value = mock_account
        
        result = self.service.get_account_info()
        
        assert result is not None
        assert result['account_id'] == 'account_123'
        assert result['buying_power'] == 10000.50
        assert result['portfolio_value'] == 15000.75
        assert result['cash'] == 5000.25
        assert result['trading_blocked'] is False
    
    def test_get_account_info_when_disconnected(self):
        """Test get_account_info returns None when disconnected"""
        self.service._connected = False
        result = self.service.get_account_info()
        assert result is None
    
    def test_get_account_info_handles_exception(self):
        """Test get_account_info handles API exceptions gracefully"""
        self.service.client.get_account.side_effect = Exception("API Error")
        result = self.service.get_account_info()
        assert result is None
    
    def test_get_positions_success(self):
        """Test successful positions retrieval"""
        mock_position1 = Mock()
        mock_position1.symbol = 'AAPL'
        mock_position1.qty = '10'
        mock_position1.market_value = '1500.00'
        mock_position1.cost_basis = '1400.00'
        mock_position1.unrealized_pl = '100.00'
        mock_position1.unrealized_plpc = '0.071'
        mock_position1.side = 'long'
        mock_position1.avg_entry_price = '140.00'
        
        mock_position2 = Mock()
        mock_position2.symbol = 'GOOGL'
        mock_position2.qty = '5'
        mock_position2.market_value = '7500.00'
        mock_position2.cost_basis = '7000.00'
        mock_position2.unrealized_pl = '500.00'
        mock_position2.unrealized_plpc = '0.071'
        mock_position2.side = 'long'
        mock_position2.avg_entry_price = '1400.00'
        
        self.service.client.list_positions.return_value = [mock_position1, mock_position2]
        
        result = self.service.get_positions()
        
        assert len(result) == 2
        assert result[0]['symbol'] == 'AAPL'
        assert result[0]['qty'] == 10
        assert result[1]['symbol'] == 'GOOGL'
        assert result[1]['qty'] == 5
    
    def test_get_positions_when_disconnected(self):
        """Test get_positions returns empty list when disconnected"""
        self.service._connected = False
        result = self.service.get_positions()
        assert result == []


class TestAlpacaServiceOrderOperations:
    """Test order-related operations"""
    
    def setup_method(self):
        """Set up mock service for each test"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        self.mock_config = {
            'trading': {'mode': 'paper'},
            'risk': {'emergency_stop': False, 'max_position_size': 1000}
        }
        
        with patch.object(AlpacaService, '_load_config', return_value=self.mock_config):
            with patch.object(AlpacaService, 'connect', return_value=True):
                self.service = AlpacaService()
                self.service._connected = True
                self.service.client = Mock()
    
    def test_submit_order_success(self):
        """Test successful order submission"""
        mock_order = Mock()
        mock_order.id = 'order_123'
        mock_order.symbol = 'AAPL'
        mock_order.qty = '10'
        mock_order.side = 'buy'
        mock_order.order_type = 'market'
        mock_order.status = 'accepted'
        mock_order.submitted_at = datetime.now()
        
        self.service.client.submit_order.return_value = mock_order
        
        result = self.service.submit_order('AAPL', 10, 'buy')
        
        assert result is not None
        assert result['id'] == 'order_123'
        assert result['symbol'] == 'AAPL'
        assert result['qty'] == 10
        assert result['side'] == 'buy'
    
    def test_submit_order_emergency_stop_blocks(self):
        """Test that emergency stop blocks order submission"""
        self.service.config['risk']['emergency_stop'] = True
        
        result = self.service.submit_order('AAPL', 10, 'buy')
        
        assert result is None
        self.service.client.submit_order.assert_not_called()
    
    def test_submit_order_max_position_size_blocks(self):
        """Test that exceeding max position size blocks order"""
        result = self.service.submit_order('AAPL', 2000, 'buy')  # Exceeds max of 1000
        
        assert result is None
        self.service.client.submit_order.assert_not_called()
    
    def test_submit_order_when_disconnected(self):
        """Test submit_order returns None when disconnected"""
        self.service._connected = False
        result = self.service.submit_order('AAPL', 10, 'buy')
        assert result is None
    
    def test_cancel_order_success(self):
        """Test successful order cancellation"""
        self.service.client.cancel_order.return_value = None  # Successful cancellation
        
        result = self.service.cancel_order('order_123')
        
        assert result is True
        self.service.client.cancel_order.assert_called_once_with('order_123')
    
    def test_cancel_order_handles_exception(self):
        """Test cancel_order handles exceptions gracefully"""
        self.service.client.cancel_order.side_effect = Exception("Cancel failed")
        
        result = self.service.cancel_order('order_123')
        
        assert result is False
    
    def test_get_orders_success(self):
        """Test successful orders retrieval"""
        mock_order = Mock()
        mock_order.id = 'order_123'
        mock_order.symbol = 'AAPL'
        mock_order.qty = '10'
        mock_order.filled_qty = '10'
        mock_order.side = 'buy'
        mock_order.order_type = 'market'
        mock_order.time_in_force = 'day'
        mock_order.status = 'filled'
        mock_order.submitted_at = datetime.now()
        mock_order.filled_at = datetime.now()
        mock_order.filled_avg_price = '150.00'
        
        self.service.client.list_orders.return_value = [mock_order]
        
        result = self.service.get_orders()
        
        assert len(result) == 1
        assert result[0]['id'] == 'order_123'
        assert result[0]['symbol'] == 'AAPL'
        assert result[0]['status'] == 'filled'


class TestAlpacaServiceMarketData:
    """Test market data operations"""
    
    def setup_method(self):
        """Set up mock service for each test"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        self.mock_config = {'trading': {'mode': 'paper'}}
        
        with patch.object(AlpacaService, '_load_config', return_value=self.mock_config):
            with patch.object(AlpacaService, 'connect', return_value=True):
                self.service = AlpacaService()
                self.service._connected = True
                self.service.client = Mock()
    
    def test_get_market_data_success(self):
        """Test successful market data retrieval"""
        mock_bars = Mock()
        mock_bars.df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [99, 100, 101],
            'close': [104, 105, 106],
            'volume': [1000, 1100, 1200]
        })
        
        self.service.client.get_bars.return_value = mock_bars
        
        result = self.service.get_market_data('AAPL')
        
        assert not result.empty
        assert len(result) == 3
        assert 'open' in result.columns
        assert 'close' in result.columns
    
    def test_get_market_data_when_disconnected(self):
        """Test get_market_data returns empty DataFrame when disconnected"""
        self.service._connected = False
        result = self.service.get_market_data('AAPL')
        assert result.empty
    
    def test_get_market_hours_success(self):
        """Test successful market hours retrieval"""
        mock_clock = Mock()
        mock_clock.is_open = True
        mock_clock.timestamp = datetime.now()
        
        mock_calendar_day = Mock()
        mock_calendar_day.date = datetime.now().date()
        mock_calendar_day.open = datetime.now().replace(hour=9, minute=30)
        mock_calendar_day.close = datetime.now().replace(hour=16, minute=0)
        
        self.service.client.get_clock.return_value = mock_clock
        self.service.client.get_calendar.return_value = [mock_calendar_day]
        
        result = self.service.get_market_hours()
        
        assert 'is_open' in result
        assert 'next_open' in result
        assert 'next_close' in result
        assert result['is_open'] is True
    
    def test_get_market_hours_when_disconnected(self):
        """Test get_market_hours returns empty dict when disconnected"""
        self.service._connected = False
        result = self.service.get_market_hours()
        assert result == {}


class TestAlpacaServiceStatus:
    """Test status and connection checking operations"""
    
    def setup_method(self):
        """Set up mock service for each test"""
        from src.trading.brokers.alpaca_service import AlpacaService
        
        self.mock_config = {'trading': {'mode': 'paper'}}
        
        with patch.object(AlpacaService, '_load_config', return_value=self.mock_config):
            with patch.object(AlpacaService, 'connect', return_value=True):
                self.service = AlpacaService()
                self.service._connected = True
                self.service.client = Mock()
                self.service.client._base_url = 'https://paper-api.alpaca.markets'
    
    def test_is_connected_returns_true_when_connected(self):
        """Test is_connected returns True when properly connected"""
        assert self.service.is_connected() is True
    
    def test_is_connected_returns_false_when_disconnected(self):
        """Test is_connected returns False when disconnected"""
        self.service._connected = False
        assert self.service.is_connected() is False
    
    def test_is_connected_returns_false_when_no_client(self):
        """Test is_connected returns False when client is None"""
        self.service.client = None
        assert self.service.is_connected() is False
    
    def test_get_connection_status_success(self):
        """Test successful connection status retrieval"""
        mock_account_info = {
            'account_id': 'test_account',
            'buying_power': 10000.0
        }
        
        with patch.object(self.service, 'get_account_info', return_value=mock_account_info):
            result = self.service.get_connection_status()
            
            assert result['connected'] is True
            assert result['mode'] == 'paper'
            assert result['base_url'] == 'https://paper-api.alpaca.markets'
            assert result['account_info'] == mock_account_info
    
    def test_get_connection_status_when_disconnected(self):
        """Test connection status when disconnected"""
        self.service._connected = False
        
        result = self.service.get_connection_status()
        
        assert result['connected'] is False
        assert result['account_info'] is None


class TestAlpacaServiceSingleton:
    """Test global service instance functionality"""
    
    def test_get_alpaca_service_creates_instance(self):
        """Test that get_alpaca_service creates and returns instance"""
        from src.trading.brokers.alpaca_service import get_alpaca_service
        
        # Reset global instance
        import src.trading.brokers.alpaca_service
        src.trading.brokers.alpaca_service.alpaca_service = None
        
        with patch('src.trading.brokers.alpaca_service.AlpacaService') as mock_alpaca_class:
            mock_instance = Mock()
            mock_alpaca_class.return_value = mock_instance
            
            result = get_alpaca_service()
            
            assert result is mock_instance
            mock_alpaca_class.assert_called_once()
    
    def test_get_alpaca_service_returns_same_instance(self):
        """Test that get_alpaca_service returns same instance on subsequent calls"""
        from src.trading.brokers.alpaca_service import get_alpaca_service
        
        # Reset global instance
        import src.trading.brokers.alpaca_service
        src.trading.brokers.alpaca_service.alpaca_service = None
        
        with patch('src.trading.brokers.alpaca_service.AlpacaService') as mock_alpaca_class:
            mock_instance = Mock()
            mock_alpaca_class.return_value = mock_instance
            
            result1 = get_alpaca_service()
            result2 = get_alpaca_service()
            
            assert result1 is result2
            mock_alpaca_class.assert_called_once()  # Should only be called once


if __name__ == "__main__":
    pytest.main([__file__, "-v"])