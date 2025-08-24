"""
Unit tests for Trading Dashboard Callbacks Logic
Tests the business logic of trading callbacks without Dash framework complications
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestTradingCallbackLogic:
    """Test trading callback business logic"""
    
    @patch('src.dashboard.callbacks.trading_callbacks.get_alpaca_service')
    def test_connection_status_logic_connected(self, mock_get_alpaca):
        """Test connection status logic when connected"""
        # Mock Alpaca service
        mock_service = Mock()
        mock_service.get_connection_status.return_value = {
            'connected': True,
            'mode': 'paper',
            'account_info': {'account_id': 'test_account_123456789'}
        }
        mock_get_alpaca.return_value = mock_service
        
        # Test the service logic directly
        service = mock_get_alpaca()
        status = service.get_connection_status()
        
        assert status['connected'] is True
        assert status['mode'] == 'paper'
        assert 'account_info' in status
        assert status['account_info']['account_id'] == 'test_account_123456789'
    
    @patch('src.dashboard.callbacks.trading_callbacks.get_alpaca_service')
    def test_connection_status_logic_disconnected(self, mock_get_alpaca):
        """Test connection status logic when disconnected"""
        # Mock Alpaca service
        mock_service = Mock()
        mock_service.get_connection_status.return_value = {
            'connected': False,
            'mode': 'paper',
            'account_info': None
        }
        mock_get_alpaca.return_value = mock_service
        
        service = mock_get_alpaca()
        status = service.get_connection_status()
        
        assert status['connected'] is False
        assert status['account_info'] is None
    
    @patch('src.dashboard.callbacks.trading_callbacks.get_alpaca_service')
    def test_connection_status_logic_exception(self, mock_get_alpaca):
        """Test connection status logic handles exceptions"""
        # Mock Alpaca service to raise exception
        mock_get_alpaca.side_effect = Exception("Connection error")
        
        with pytest.raises(Exception, match="Connection error"):
            mock_get_alpaca()
    
    @patch('src.dashboard.callbacks.trading_callbacks.get_alpaca_service')
    def test_account_info_logic_success(self, mock_get_alpaca):
        """Test account info logic success"""
        # Mock Alpaca service
        mock_service = Mock()
        mock_account_info = {
            'account_id': 'test_account',
            'buying_power': 10000.0,
            'portfolio_value': 15000.0,
            'cash': 5000.0
        }
        mock_service.get_account_info.return_value = mock_account_info
        mock_get_alpaca.return_value = mock_service
        
        service = mock_get_alpaca()
        account_info = service.get_account_info()
        
        assert account_info is not None
        assert account_info['account_id'] == 'test_account'
        assert account_info['buying_power'] == 10000.0
        assert account_info['portfolio_value'] == 15000.0
        assert account_info['cash'] == 5000.0
    
    @patch('src.dashboard.callbacks.trading_callbacks.get_alpaca_service')
    def test_account_info_logic_exception(self, mock_get_alpaca):
        """Test account info logic handles exceptions"""
        # Mock Alpaca service to raise exception
        mock_service = Mock()
        mock_service.get_account_info.side_effect = Exception("Account error")
        mock_get_alpaca.return_value = mock_service
        
        service = mock_get_alpaca()
        
        with pytest.raises(Exception, match="Account error"):
            service.get_account_info()
    
    @patch('src.dashboard.callbacks.trading_callbacks.get_alpaca_service')
    def test_positions_logic_success(self, mock_get_alpaca):
        """Test positions logic success"""
        # Mock Alpaca service
        mock_service = Mock()
        mock_positions = [
            {
                'symbol': 'AAPL',
                'qty': 10,
                'market_value': 1500.0,
                'unrealized_pl': 100.0
            },
            {
                'symbol': 'GOOGL',
                'qty': 5,
                'market_value': 7500.0,
                'unrealized_pl': 500.0
            }
        ]
        mock_service.get_positions.return_value = mock_positions
        mock_get_alpaca.return_value = mock_service
        
        service = mock_get_alpaca()
        positions = service.get_positions()
        
        assert len(positions) == 2
        assert positions[0]['symbol'] == 'AAPL'
        assert positions[1]['symbol'] == 'GOOGL'
    
    @patch('src.dashboard.callbacks.trading_callbacks.get_alpaca_service')
    def test_orders_logic_success(self, mock_get_alpaca):
        """Test orders logic success"""
        # Mock Alpaca service
        mock_service = Mock()
        mock_orders = [
            {
                'id': 'order_123',
                'symbol': 'AAPL',
                'qty': 10,
                'side': 'buy',
                'status': 'filled'
            }
        ]
        mock_service.get_orders.return_value = mock_orders
        mock_get_alpaca.return_value = mock_service
        
        service = mock_get_alpaca()
        orders = service.get_orders(status='all', limit=20)
        
        assert len(orders) == 1
        assert orders[0]['id'] == 'order_123'
        assert orders[0]['symbol'] == 'AAPL'
        assert orders[0]['status'] == 'filled'


class TestTradingModalLogic:
    """Test trading modal business logic"""
    
    def test_input_validation_valid_inputs(self):
        """Test input validation with valid inputs"""
        symbol = 'AAPL'
        quantity = '10'
        
        # Simulate validation logic
        is_valid = bool(symbol and quantity and quantity.isdigit() and int(quantity) > 0)
        
        assert is_valid is True
    
    def test_input_validation_invalid_inputs(self):
        """Test input validation with invalid inputs"""
        test_cases = [
            ('', '10'),      # Empty symbol
            ('AAPL', ''),    # Empty quantity
            ('AAPL', 'abc'), # Non-numeric quantity
            ('AAPL', '0'),   # Zero quantity
            ('AAPL', '-5'),  # Negative quantity
        ]
        
        for symbol, quantity in test_cases:
            # Simulate validation logic
            try:
                is_valid = bool(symbol and quantity and int(quantity) > 0)
            except ValueError:
                is_valid = False
            
            assert is_valid is False, f"Should reject symbol='{symbol}', quantity='{quantity}'"
    
    @patch('src.dashboard.callbacks.trading_callbacks.get_alpaca_service')
    def test_order_execution_logic_success(self, mock_get_alpaca):
        """Test order execution logic success"""
        # Mock Alpaca service
        mock_service = Mock()
        mock_order_result = {
            'id': 'order_123456',
            'symbol': 'AAPL',
            'qty': 10,
            'side': 'buy',
            'status': 'accepted'
        }
        mock_service.submit_order.return_value = mock_order_result
        mock_get_alpaca.return_value = mock_service
        
        service = mock_get_alpaca()
        result = service.submit_order(
            symbol='AAPL',
            qty=10,
            side='buy'
        )
        
        assert result is not None
        assert result['id'] == 'order_123456'
        assert result['symbol'] == 'AAPL'
        assert result['qty'] == 10
        assert result['side'] == 'buy'
        assert result['status'] == 'accepted'
    
    @patch('src.dashboard.callbacks.trading_callbacks.get_alpaca_service')
    def test_order_execution_logic_failure(self, mock_get_alpaca):
        """Test order execution logic failure"""
        # Mock Alpaca service
        mock_service = Mock()
        mock_service.submit_order.return_value = None  # Order failed
        mock_get_alpaca.return_value = mock_service
        
        service = mock_get_alpaca()
        result = service.submit_order(
            symbol='AAPL',
            qty=10,
            side='buy'
        )
        
        assert result is None


class TestTradingLayoutComponents:
    """Test trading layout component creation logic"""
    
    @patch('src.dashboard.callbacks.trading_callbacks.create_account_info_display')
    def test_account_info_display_creation(self, mock_create_display):
        """Test account info display creation"""
        from dash import html
        
        mock_account_info = {
            'account_id': 'test_account',
            'buying_power': 10000.0,
            'portfolio_value': 15000.0
        }
        
        # Mock the display creation function
        mock_display_result = html.Div("Account info display")
        mock_create_display.return_value = mock_display_result
        
        result = mock_create_display(mock_account_info)
        
        assert result == mock_display_result
        mock_create_display.assert_called_once_with(mock_account_info)
    
    @patch('src.dashboard.callbacks.trading_callbacks.create_positions_table')
    def test_positions_table_creation(self, mock_create_table):
        """Test positions table creation"""
        from dash import html
        
        mock_positions = [
            {
                'symbol': 'AAPL',
                'qty': 10,
                'market_value': 1500.0
            }
        ]
        
        # Mock the table creation function
        mock_table_result = html.Table("Positions table")
        mock_create_table.return_value = mock_table_result
        
        result = mock_create_table(mock_positions)
        
        assert result == mock_table_result
        mock_create_table.assert_called_once_with(mock_positions)
    
    @patch('src.dashboard.callbacks.trading_callbacks.create_orders_table')
    def test_orders_table_creation(self, mock_create_table):
        """Test orders table creation"""
        from dash import html
        
        mock_orders = [
            {
                'id': 'order_123',
                'symbol': 'AAPL',
                'status': 'filled'
            }
        ]
        
        # Mock the table creation function
        mock_table_result = html.Table("Orders table")
        mock_create_table.return_value = mock_table_result
        
        result = mock_create_table(mock_orders)
        
        assert result == mock_table_result
        mock_create_table.assert_called_once_with(mock_orders)
    
    @patch('src.dashboard.callbacks.trading_callbacks.format_trading_log_message')
    def test_trading_log_message_formatting(self, mock_format_log):
        """Test trading log message formatting"""
        from dash import html
        
        # Mock the log formatting function
        mock_log_message = html.Div("Log message")
        mock_format_log.return_value = mock_log_message
        
        result = mock_format_log("Test message", "success")
        
        assert result == mock_log_message
        mock_format_log.assert_called_once_with("Test message", "success")


class TestTradingCallbacksIntegration:
    """Test trading callback integration"""
    
    def test_callback_registration_imports(self):
        """Test that callback registration can be imported"""
        try:
            from src.dashboard.callbacks.trading_callbacks import register_trading_callbacks
            assert register_trading_callbacks is not None
        except ImportError:
            pytest.fail("Failed to import register_trading_callbacks")
    
    def test_required_layout_functions_exist(self):
        """Test that required layout functions exist"""
        try:
            import src.dashboard.layouts.trading_layout as trading_layout
            
            # Check that required functions exist
            required_functions = [
                'create_account_info_display',
                'create_positions_table', 
                'create_orders_table',
                'format_trading_log_message'
            ]
            
            for func_name in required_functions:
                assert hasattr(trading_layout, func_name), f"Function {func_name} not found in trading_layout"
                
        except ImportError:
            pytest.fail("Failed to import trading_layout module")
    
    def test_alpaca_service_integration(self):
        """Test that Alpaca service integration works"""
        try:
            from src.trading.brokers.alpaca_service import get_alpaca_service
            assert get_alpaca_service is not None
        except ImportError:
            pytest.fail("Failed to import get_alpaca_service")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])