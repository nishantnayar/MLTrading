"""
Mock objects and services for testing.

Provides comprehensive mock implementations for external services and dependencies.
"""

from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime, timezone
import json


class MockAlpacaAPI:
    """Mock Alpaca API for trading tests"""
    
    def __init__(self, paper=True):
        self.paper = paper
        self.orders = []
        self.positions = []
        self.account_data = {
            'account_id': 'test_account',
            'cash': 100000.0,
            'portfolio_value': 100000.0,
            'buying_power': 100000.0,
            'status': 'ACTIVE'
        }
        self.connected = False
    
    def connect(self):
        """Mock connection"""
        self.connected = True
        return True
    
    def get_account(self):
        """Mock account information"""
        if not self.connected:
            raise ConnectionError("Not connected to API")
        return self.account_data
    
    def list_orders(self, status='all', limit=100):
        """Mock order listing"""
        return self.orders[-limit:] if self.orders else []
    
    def submit_order(self, symbol, qty, side, type='market', time_in_force='day', **kwargs):
        """Mock order submission"""
        if not self.connected:
            raise ConnectionError("Not connected to API")
        
        order = {
            'id': f"order_{len(self.orders)}",
            'client_order_id': f"client_{len(self.orders)}",
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'order_type': type,
            'time_in_force': time_in_force,
            'status': 'filled',
            'filled_qty': qty,
            'filled_avg_price': 100.0,  # Mock price
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        self.orders.append(order)
        return order
    
    def get_order(self, order_id):
        """Mock order retrieval"""
        for order in self.orders:
            if order['id'] == order_id:
                return order
        raise ValueError(f"Order {order_id} not found")
    
    def cancel_order(self, order_id):
        """Mock order cancellation"""
        for order in self.orders:
            if order['id'] == order_id:
                order['status'] = 'canceled'
                return order
        raise ValueError(f"Order {order_id} not found")
    
    def list_positions(self):
        """Mock positions listing"""
        return self.positions
    
    def get_position(self, symbol):
        """Mock position retrieval"""
        for pos in self.positions:
            if pos['symbol'] == symbol:
                return pos
        raise ValueError(f"Position for {symbol} not found")
    
    def get_bars(self, symbol, timeframe='1Day', start=None, end=None, limit=1000):
        """Mock historical data retrieval"""
        # Generate mock OHLCV data
        from .data_generators import MarketDataGenerator
        
        data = MarketDataGenerator.generate_ohlcv_data(
            symbol=symbol,
            periods=min(limit, 100)
        )
        
        # Convert to Alpaca-like format
        bars = []
        for _, row in data.iterrows():
            bars.append({
                't': row['timestamp'].isoformat(),
                'o': row['open'],
                'h': row['high'],
                'l': row['low'],
                'c': row['close'],
                'v': row['volume']
            })
        
        return bars


class MockDataService:
    """Mock data service for dashboard and API tests"""
    
    def __init__(self):
        from .data_generators import MarketDataGenerator
        self.generator = MarketDataGenerator()
        self.symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'AMZN', 'META']
        self._market_data_cache = {}
    
    def get_available_symbols(self):
        """Mock available symbols"""
        return [
            {"symbol": symbol, "company_name": f"{symbol} Inc.", "sector": "Technology"}
            for symbol in self.symbols
        ]
    
    def get_market_data(self, symbol, start_date=None, end_date=None, limit=100):
        """Mock market data retrieval"""
        if symbol not in self._market_data_cache:
            self._market_data_cache[symbol] = self.generator.generate_ohlcv_data(
                symbol=symbol, periods=200
            )
        
        data = self._market_data_cache[symbol].copy()
        
        # Apply filters
        if start_date:
            data = data[data['timestamp'] >= start_date]
        if end_date:
            data = data[data['timestamp'] <= end_date]
        if limit:
            data = data.tail(limit)
        
        return data
    
    def get_sector_distribution(self):
        """Mock sector distribution"""
        return {
            "sectors": ["Technology", "Healthcare", "Finance"],
            "counts": [5, 1, 1]
        }
    
    def get_top_symbols_by_volume(self, limit=10):
        """Mock top volume symbols"""
        return self.get_available_symbols()[:limit]
    
    def get_technical_indicators(self, symbol, indicators=None):
        """Mock technical indicators"""
        data = self.get_market_data(symbol)
        
        # Generate mock technical indicators
        indicators_data = {}
        if not indicators or 'rsi' in indicators:
            indicators_data['rsi'] = pd.Series(
                [50 + i % 20 - 10 for i in range(len(data))],
                index=data.index
            )
        
        if not indicators or 'sma_20' in indicators:
            indicators_data['sma_20'] = data['close'].rolling(20).mean()
        
        if not indicators or 'bollinger_upper' in indicators:
            sma = data['close'].rolling(20).mean()
            std = data['close'].rolling(20).std()
            indicators_data['bollinger_upper'] = sma + (2 * std)
            indicators_data['bollinger_lower'] = sma - (2 * std)
        
        return indicators_data


class MockEmailService:
    """Mock email service for alert testing"""
    
    def __init__(self, should_succeed=True, delay=0):
        self.should_succeed = should_succeed
        self.delay = delay
        self.emails_sent = []
        self.available = True
        self.circuit_breaker_state = 'closed'
    
    def is_available(self):
        """Mock availability check"""
        return self.available
    
    def send_alert(self, alert):
        """Mock email sending"""
        if self.delay:
            import time
            time.sleep(self.delay)
        
        if not self.should_succeed:
            raise ConnectionError("Mock email service failure")
        
        self.emails_sent.append({
            'to': 'test@example.com',
            'subject': alert.to_email_subject(),
            'body': alert.to_email_body(),
            'timestamp': datetime.now(timezone.utc)
        })
        
        return True
    
    def get_status(self):
        """Mock status retrieval"""
        return {
            'enabled': True,
            'available': self.available,
            'circuit_breaker_state': self.circuit_breaker_state,
            'circuit_breaker_failures': 0,
            'emails_sent_count': len(self.emails_sent)
        }
    
    def test_connection(self):
        """Mock connection test"""
        return self.should_succeed
    
    def set_failure_mode(self, should_fail=True):
        """Configure service to fail for testing"""
        self.should_succeed = not should_fail
        self.available = not should_fail


class MockDatabaseManager:
    """Mock database manager for testing database operations"""
    
    def __init__(self):
        self.connected = False
        self.query_results = {}
        self.connection_count = 0
        self.max_connections = 20
    
    def get_connection(self):
        """Mock database connection"""
        if self.connection_count >= self.max_connections:
            raise ConnectionError("Connection pool exhausted")
        
        self.connection_count += 1
        return MockDatabaseConnection(self)
    
    def execute_query(self, query, params=None):
        """Mock query execution"""
        if not self.connected:
            raise ConnectionError("Not connected to database")
        
        # Return predefined results or empty list
        query_key = query.strip().lower().split()[0]  # First word (SELECT, INSERT, etc.)
        return self.query_results.get(query_key, [])
    
    def set_query_result(self, query_type, result):
        """Set predefined query result"""
        self.query_results[query_type.lower()] = result
    
    def connect(self):
        """Mock connection"""
        self.connected = True
        return True
    
    def disconnect(self):
        """Mock disconnection"""
        self.connected = False
        self.connection_count = 0


class MockDatabaseConnection:
    """Mock database connection context manager"""
    
    def __init__(self, manager):
        self.manager = manager
        self.cursor_instance = MockDatabaseCursor(manager)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.connection_count -= 1
    
    def cursor(self):
        """Mock cursor creation"""
        return self.cursor_instance
    
    def commit(self):
        """Mock transaction commit"""
        pass
    
    def rollback(self):
        """Mock transaction rollback"""
        pass


class MockDatabaseCursor:
    """Mock database cursor"""
    
    def __init__(self, manager):
        self.manager = manager
        self.results = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def execute(self, query, params=None):
        """Mock query execution"""
        query_key = query.strip().lower().split()[0]
        self.results = self.manager.query_results.get(query_key, [])
    
    def fetchall(self):
        """Mock fetch all results"""
        return self.results
    
    def fetchone(self):
        """Mock fetch one result"""
        return self.results[0] if self.results else None
    
    def fetchmany(self, size=1):
        """Mock fetch many results"""
        return self.results[:size]


class MockPrefectClient:
    """Mock Prefect client for workflow testing"""
    
    def __init__(self):
        self.flows = {}
        self.deployments = {}
        self.flow_runs = {}
        self.task_runs = {}
    
    def create_deployment(self, deployment_spec):
        """Mock deployment creation"""
        deployment_id = f"deployment_{len(self.deployments)}"
        self.deployments[deployment_id] = deployment_spec
        return {"id": deployment_id}
    
    def create_flow_run(self, flow_id, parameters=None):
        """Mock flow run creation"""
        run_id = f"run_{len(self.flow_runs)}"
        self.flow_runs[run_id] = {
            "id": run_id,
            "flow_id": flow_id,
            "state": "PENDING",
            "parameters": parameters or {},
            "start_time": datetime.now(timezone.utc)
        }
        return {"id": run_id}
    
    def get_flow_run(self, run_id):
        """Mock flow run retrieval"""
        return self.flow_runs.get(run_id)
    
    def set_flow_run_state(self, run_id, state):
        """Mock flow run state update"""
        if run_id in self.flow_runs:
            self.flow_runs[run_id]["state"] = state


def create_mock_dash_component(component_id, children=None, **kwargs):
    """Create mock Dash component for testing"""
    mock_component = Mock()
    mock_component.id = component_id
    mock_component.children = children or []
    
    for key, value in kwargs.items():
        setattr(mock_component, key, value)
    
    return mock_component


def mock_external_api_response(url_pattern, response_data, status_code=200):
    """Create mock for external API responses"""
    def mock_response(*args, **kwargs):
        mock_resp = Mock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = response_data
        mock_resp.text = json.dumps(response_data)
        return mock_resp
    
    return patch('requests.get', side_effect=mock_response)


# Context managers for common mocking scenarios

class MockedServices:
    """Context manager for mocking multiple services at once"""
    
    def __init__(self, mock_database=True, mock_alpaca=True, mock_email=True):
        self.mock_database = mock_database
        self.mock_alpaca = mock_alpaca
        self.mock_email = mock_email
        self.patches = []
    
    def __enter__(self):
        if self.mock_database:
            db_patch = patch('src.data.storage.database.DatabaseManager', MockDatabaseManager)
            self.patches.append(db_patch)
            db_patch.start()
        
        if self.mock_alpaca:
            alpaca_patch = patch('src.trading.brokers.alpaca_service.AlpacaAPI', MockAlpacaAPI)
            self.patches.append(alpaca_patch)
            alpaca_patch.start()
        
        if self.mock_email:
            email_patch = patch('src.utils.alerts.email_service.EmailService', MockEmailService)
            self.patches.append(email_patch)
            email_patch.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for patch_obj in self.patches:
            patch_obj.stop()


class MockedEnvironment:
    """Context manager for mocking environment variables"""
    
    def __init__(self, **env_vars):
        self.env_vars = env_vars
        self.patch = None
    
    def __enter__(self):
        self.patch = patch.dict('os.environ', self.env_vars)
        self.patch.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.patch:
            self.patch.stop()