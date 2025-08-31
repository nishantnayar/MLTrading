"""
Alpaca Trading Service
Handles connection and operations with Alpaca Markets API
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from alpaca_trade_api import REST, Stream
    from alpaca_trade_api.entity import Account, Position, Order
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    print("[WARNING] alpaca-trade-api not installed.")
    print("         Due to dependency conflicts with Prefect, install separately:")
    print("         pip install alpaca-trade-api==3.1.1")
    print("         Note: This will conflict with Prefect's websockets requirements")

from ...utils.logging_config import get_ui_logger
from ...config.settings import get_settings

logger = get_ui_logger("alpaca_service")


class AlpacaService:
    """Service for interacting with Alpaca Markets API"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Alpaca service with configuration"""
        self.config = self._load_config(config_path)
        self.client = None
        self.stream = None
        self._connected = False
        
        # Initialize connection
        self.connect()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load Alpaca configuration from unified settings"""
        try:
            # Use unified configuration system
            settings = get_settings()
            
            # Convert unified config to legacy format for compatibility
            config = {
                'alpaca': {
                    'paper_trading': {
                        'base_url': settings.alpaca.paper_base_url
                    },
                    'live_trading': {
                        'base_url': settings.alpaca.live_base_url
                    }
                },
                'trading': {
                    'mode': settings.trading.mode,
                    'default_order_type': settings.trading.default_order_type,
                    'default_time_in_force': settings.trading.default_time_in_force,
                    'max_order_value': settings.trading.max_order_value
                },
                'risk': {
                    'max_daily_orders': settings.risk.max_daily_orders,
                    'max_position_size': settings.risk.max_position_size,
                    'emergency_stop': settings.risk.emergency_stop
                }
            }
            
            logger.info(f"Loaded Alpaca config from unified settings - mode: {settings.trading.mode}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading unified Alpaca config: {e}")
            
            # Fallback to legacy file if unified config fails
            if config_path is None:
                project_root = Path(__file__).parent.parent.parent.parent
                config_path = project_root / "config" / "legacy_backup" / "alpaca_config.yaml"
            
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.warning(f"Fallback: Loaded legacy Alpaca config from {config_path}")
                return config
            except Exception as fallback_error:
                logger.error(f"Both unified and legacy config loading failed: {fallback_error}")
                raise
    
    def connect(self) -> bool:
        """Establish connection to Alpaca API"""
        if not ALPACA_AVAILABLE:
            logger.error("Alpaca Trade API not available. Install with: pip install alpaca-trade-api")
            return False
        
        try:
            # Get credentials from environment variables (secure approach)
            mode = self.config['trading']['mode']
            
            if mode == 'paper':
                api_key = os.getenv('ALPACA_PAPER_API_KEY')
                secret_key = os.getenv('ALPACA_PAPER_SECRET_KEY')
                base_url = self.config['alpaca']['paper_trading']['base_url']
            else:  # live mode
                api_key = os.getenv('ALPACA_LIVE_API_KEY')
                secret_key = os.getenv('ALPACA_LIVE_SECRET_KEY') 
                base_url = self.config['alpaca']['live_trading']['base_url']
            
            # Validate credentials are set
            if not api_key or not secret_key:
                logger.error(f"[ERROR] Missing Alpaca API credentials for {mode} mode")
                logger.error("   Please set environment variables:")
                if mode == 'paper':
                    logger.error("   - ALPACA_PAPER_API_KEY")
                    logger.error("   - ALPACA_PAPER_SECRET_KEY")
                else:
                    logger.error("   - ALPACA_LIVE_API_KEY") 
                    logger.error("   - ALPACA_LIVE_SECRET_KEY")
                logger.error("   Check your .env file")
                return False
            
            # Initialize REST client
            self.client = REST(
                key_id=api_key,
                secret_key=secret_key,
                base_url=base_url,
                api_version='v2'
            )
            
            # Test connection
            account = self.client.get_account()
            logger.info(f"[SUCCESS] Connected to Alpaca ({mode} mode)")
            logger.info(f"   Account: {account.id}")
            logger.info(f"   Buying Power: ${float(account.buying_power):,.2f}")
            logger.info(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
            
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to Alpaca: {e}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to Alpaca"""
        return self._connected and self.client is not None
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        if not self.is_connected():
            return None
        
        try:
            account = self.client.get_account()
            return {
                'account_id': account.id,
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'cash': float(account.cash),
                'daytrading_buying_power': float(account.daytrading_buying_power),
                'trading_blocked': account.trading_blocked,
                'account_blocked': account.account_blocked,
                'pattern_day_trader': account.pattern_day_trader
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        if not self.is_connected():
            return []
        
        try:
            positions = self.client.list_positions()
            return [
                {
                    'symbol': pos.symbol,
                    'qty': int(pos.qty),
                    'market_value': float(pos.market_value),
                    'cost_basis': float(pos.cost_basis),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc),
                    'side': pos.side,
                    'avg_entry_price': float(pos.avg_entry_price)
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(self, status: str = 'all', limit: int = 50) -> List[Dict]:
        """Get recent orders"""
        if not self.is_connected():
            return []
        
        try:
            orders = self.client.list_orders(
                status=status,
                limit=limit,
                direction='desc'
            )
            return [
                {
                    'id': order.id,
                    'symbol': order.symbol,
                    'qty': int(order.qty),
                    'filled_qty': int(order.filled_qty) if order.filled_qty else 0,
                    'side': order.side,
                    'order_type': order.order_type,
                    'time_in_force': order.time_in_force,
                    'status': order.status,
                    'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                    'filled_at': order.filled_at.isoformat() if order.filled_at else None,
                    'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def submit_order(self, symbol: str, qty: int, side: str, 
                    order_type: str = 'market', time_in_force: str = 'day') -> Optional[Dict]:
        """Submit a trading order"""
        if not self.is_connected():
            logger.error("Not connected to Alpaca")
            return None
        
        # Safety checks
        if self.config['risk']['emergency_stop']:
            logger.warning("[BLOCKED] Emergency stop enabled - order blocked")
            return None
        
        if abs(qty) > self.config['risk']['max_position_size']:
            logger.warning(f"[BLOCKED] Order quantity {qty} exceeds max position size")
            return None
        
        try:
            order = self.client.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force=time_in_force
            )
            
            logger.info(f"[SUCCESS] Order submitted: {side} {qty} {symbol}")
            
            return {
                'id': order.id,
                'symbol': order.symbol,
                'qty': int(order.qty),
                'side': order.side,
                'order_type': order.order_type,
                'status': order.status,
                'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Error submitting order: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if not self.is_connected():
            return False
        
        try:
            self.client.cancel_order(order_id)
            logger.info(f"[SUCCESS] Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Error cancelling order: {e}")
            return False
    
    def get_market_data(self, symbol: str, timeframe: str = '1Day', 
                       start: Optional[datetime] = None, end: Optional[datetime] = None) -> pd.DataFrame:
        """Get market data for a symbol"""
        if not self.is_connected():
            return pd.DataFrame()
        
        try:
            # Default to last 30 days if no dates provided
            if end is None:
                end = datetime.now()
            if start is None:
                start = end - timedelta(days=30)
            
            bars = self.client.get_bars(
                symbol,
                timeframe,
                start=start.isoformat(),
                end=end.isoformat()
            ).df
            
            return bars
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_market_hours(self) -> Dict:
        """Get market hours and status from Alpaca"""
        if not self.is_connected():
            return {}
        
        try:
            # Get market clock
            clock = self.client.get_clock()
            
            # Get market calendar for today and next trading day
            calendar = self.client.get_calendar(start=datetime.now().date(), end=(datetime.now() + timedelta(days=7)).date())
            
            if not calendar:
                return {}
            
            # Find next trading day
            today = datetime.now().date()
            next_trading_day = None
            
            for day in calendar:
                # Handle both pandas Timestamp and datetime.date objects
                day_date = day.date.date() if hasattr(day.date, 'date') else day.date
                if day_date >= today:
                    next_trading_day = day
                    break
            
            if not next_trading_day:
                return {}
            
            # Calculate next market open and close times
            current_time = datetime.now()
            
            # Initialize default values
            next_open = next_trading_day.open
            next_close = next_trading_day.close
            
            # If market is closed and it's after market close, find next trading day
            # Check if market is closed and we need to find next trading day
            market_open_time = next_trading_day.open.time() if hasattr(next_trading_day.open, 'time') else next_trading_day.open
            # Handle both pandas Timestamp and datetime.date objects for next_trading_day.date
            next_trading_day_date = next_trading_day.date.date() if hasattr(next_trading_day.date, 'date') else next_trading_day.date
            if not clock.is_open and not (next_trading_day_date == today and current_time.time() < market_open_time):
                # Market is closed, find next trading day
                found_next = False
                for day in calendar[1:]:  # Skip today
                    next_open = day.open
                    next_close = day.close
                    found_next = True
                    break
                
                # If no next trading day found in calendar, use the current trading day
                if not found_next:
                    next_open = next_trading_day.open
                    next_close = next_trading_day.close
            
            return {
                'is_open': clock.is_open,
                'next_open': next_open,
                'next_close': next_close,
                'current_time': clock.timestamp
            }
            
        except Exception as e:
            logger.error(f"Error getting market hours: {e}")
            return {}
    
    def get_connection_status(self) -> Dict:
        """Get detailed connection status"""
        return {
            'connected': self._connected,
            'mode': self.config['trading']['mode'] if self.config else 'unknown',
            'base_url': getattr(self.client, '_base_url', None) if self.client else None,
            'account_info': self.get_account_info() if self._connected else None
        }


# Global instance for easy access
alpaca_service = None

def get_alpaca_service() -> AlpacaService:
    """Get global Alpaca service instance"""
    global alpaca_service
    if alpaca_service is None:
        alpaca_service = AlpacaService()
    return alpaca_service