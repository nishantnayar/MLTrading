"""
Data generators for test scenarios.

Provides classes to generate various types of test data for different components.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
import random
import string


class MarketDataGenerator:
    """Generate realistic market data for testing"""
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducible tests"""
        np.random.seed(seed)
        random.seed(seed)
    
    @staticmethod
    def generate_ohlcv_data(
        symbol: str = "TEST",
        start_date: str = "2023-01-01",
        periods: int = 100,
        base_price: float = 100.0,
        volatility: float = 0.02
    ) -> pd.DataFrame:
        """Generate realistic OHLCV data with proper relationships"""
        dates = pd.date_range(start=start_date, periods=periods, freq='D')
        
        # Generate price series with trend and noise
        trend = np.linspace(0, 20, periods)  # Slight upward trend
        noise = np.random.normal(0, volatility * base_price, periods)
        closes = base_price + trend + noise
        
        # Generate opens based on closes with gap
        gap = np.random.normal(0, volatility * base_price * 0.5, periods)
        opens = np.maximum(closes + gap, 0.01)  # Ensure positive prices
        
        # Generate highs and lows maintaining proper relationships
        intraday_range = np.random.uniform(0.005, 0.03, periods)  # 0.5% to 3% daily range
        
        highs = np.maximum(opens, closes) * (1 + intraday_range)
        lows = np.minimum(opens, closes) * (1 - intraday_range)
        
        # Generate volume with correlation to price volatility
        price_change = np.abs(closes - opens)
        volume_base = np.random.uniform(1000000, 5000000, periods)
        volume_multiplier = 1 + (price_change / closes) * 2  # Higher volume on big moves
        volumes = (volume_base * volume_multiplier).astype(int)
        
        return pd.DataFrame({
            'symbol': symbol,
            'timestamp': dates,
            'open': np.round(opens, 2),
            'high': np.round(highs, 2),
            'low': np.round(lows, 2),
            'close': np.round(closes, 2),
            'volume': volumes
        })
    
    @staticmethod
    def generate_multiple_symbols(
        symbols: List[str],
        start_date: str = "2023-01-01",
        periods: int = 100,
        correlation: float = 0.3
    ) -> pd.DataFrame:
        """Generate correlated market data for multiple symbols"""
        n_symbols = len(symbols)
        
        # Generate correlated random walks
        base_returns = np.random.multivariate_normal(
            mean=[0.001] * n_symbols,  # 0.1% daily return
            cov=correlation * np.ones((n_symbols, n_symbols)) + 
                (1 - correlation) * np.eye(n_symbols),
            size=periods
        )
        
        all_data = []
        base_prices = np.random.uniform(50, 200, n_symbols)
        
        for i, symbol in enumerate(symbols):
            # Convert returns to prices
            returns = base_returns[:, i]
            prices = [base_prices[i]]
            for ret in returns:
                prices.append(prices[-1] * (1 + ret))
            
            data = MarketDataGenerator.generate_ohlcv_data(
                symbol=symbol,
                start_date=start_date,
                periods=periods,
                base_price=base_prices[i]
            )
            
            # Override closes with correlated prices
            data['close'] = np.round(prices[:periods], 2)
            
            # Adjust OHLC relationships
            data['open'] = data['close'] * np.random.uniform(0.98, 1.02, periods)
            data['high'] = np.maximum(data['open'], data['close']) * np.random.uniform(1.0, 1.03, periods)
            data['low'] = np.minimum(data['open'], data['close']) * np.random.uniform(0.97, 1.0, periods)
            
            all_data.append(data)
        
        return pd.concat(all_data, ignore_index=True)
    
    @staticmethod
    def generate_with_gaps(
        symbol: str = "TEST",
        start_date: str = "2023-01-01",
        periods: int = 100,
        gap_probability: float = 0.1,
        gap_size_range: Tuple[float, float] = (0.05, 0.15)
    ) -> pd.DataFrame:
        """Generate data with price gaps for testing edge cases"""
        data = MarketDataGenerator.generate_ohlcv_data(symbol, start_date, periods)
        
        # Add random gaps
        gap_indices = np.random.choice(
            range(1, periods), 
            size=int(periods * gap_probability), 
            replace=False
        )
        
        for idx in gap_indices:
            gap_size = np.random.uniform(*gap_size_range)
            gap_direction = np.random.choice([-1, 1])
            gap_multiplier = 1 + (gap_direction * gap_size)
            
            # Apply gap to all prices from this point forward
            data.loc[idx:, ['open', 'high', 'low', 'close']] *= gap_multiplier
        
        return data


class TechnicalDataGenerator:
    """Generate data with specific technical patterns for testing indicators"""
    
    @staticmethod
    def generate_trending_data(
        periods: int = 100,
        trend_strength: float = 0.02,
        noise_level: float = 0.01,
        base_price: float = 100.0
    ) -> pd.DataFrame:
        """Generate trending price data"""
        dates = pd.date_range(start='2023-01-01', periods=periods, freq='D')
        
        # Create strong trend with noise
        trend = np.linspace(0, trend_strength * base_price * periods, periods)
        noise = np.random.normal(0, noise_level * base_price, periods)
        prices = base_price + trend + noise
        
        return pd.DataFrame({
            'timestamp': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, periods)
        }).set_index('timestamp')
    
    @staticmethod
    def generate_sideways_data(
        periods: int = 100,
        range_pct: float = 0.1,
        base_price: float = 100.0
    ) -> pd.DataFrame:
        """Generate sideways/ranging price data"""
        dates = pd.date_range(start='2023-01-01', periods=periods, freq='D')
        
        # Create data that oscillates within a range
        range_size = base_price * range_pct
        prices = base_price + np.random.uniform(-range_size/2, range_size/2, periods)
        
        # Add some mean reversion
        for i in range(1, periods):
            if abs(prices[i] - base_price) > range_size * 0.4:
                prices[i] = base_price + np.random.uniform(-range_size/4, range_size/4)
        
        return pd.DataFrame({
            'timestamp': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, periods)
        }).set_index('timestamp')
    
    @staticmethod
    def generate_rsi_test_data(
        periods: int = 30,
        oversold_period: int = 5,
        overbought_period: int = 5
    ) -> pd.DataFrame:
        """Generate data designed to test RSI calculations"""
        dates = pd.date_range(start='2023-01-01', periods=periods, freq='D')
        
        prices = [100.0]  # Starting price
        
        # Create periods of consecutive gains (overbought) and losses (oversold)
        for i in range(1, periods):
            if i <= oversold_period:
                # Consecutive losses
                change = np.random.uniform(-2, -0.5)
            elif i <= oversold_period + 10:
                # Mixed changes
                change = np.random.uniform(-1, 1)
            elif i <= oversold_period + 10 + overbought_period:
                # Consecutive gains
                change = np.random.uniform(0.5, 2)
            else:
                # Mixed changes
                change = np.random.uniform(-1, 1)
            
            prices.append(max(prices[-1] + change, 1.0))  # Ensure positive prices
        
        return pd.DataFrame({
            'timestamp': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, periods)
        }).set_index('timestamp')
    
    @staticmethod
    def generate_bollinger_bands_test_data(periods: int = 50) -> pd.DataFrame:
        """Generate data for testing Bollinger Bands"""
        dates = pd.date_range(start='2023-01-01', periods=periods, freq='D')
        
        # Create data with varying volatility periods
        base_price = 100.0
        prices = [base_price]
        
        for i in range(1, periods):
            # Alternate between low and high volatility periods
            if i < periods // 3:
                # Low volatility
                change = np.random.normal(0.1, 0.5)
            elif i < 2 * periods // 3:
                # High volatility
                change = np.random.normal(0.1, 2.0)
            else:
                # Medium volatility
                change = np.random.normal(0.1, 1.0)
            
            prices.append(prices[-1] + change)
        
        return pd.DataFrame({
            'timestamp': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, periods)
        }).set_index('timestamp')


class ConfigGenerator:
    """Generate configuration data for testing"""
    
    @staticmethod
    def generate_trading_config(
        mode: str = "paper",
        max_position_size: int = 1000,
        emergency_stop: bool = False
    ) -> Dict[str, Any]:
        """Generate trading configuration"""
        return {
            'trading': {
                'mode': mode,
                'default_order_type': 'market',
                'default_time_in_force': 'day'
            },
            'risk': {
                'emergency_stop': emergency_stop,
                'max_position_size': max_position_size,
                'max_daily_orders': 25,
                'max_total_positions': 10
            },
            'alpaca': {
                'paper_trading': {
                    'base_url': 'https://paper-api.alpaca.markets'
                },
                'live_trading': {
                    'base_url': 'https://api.alpaca.markets'
                }
            }
        }
    
    @staticmethod
    def generate_alert_config(
        enabled: bool = True,
        min_severity: str = "MEDIUM",
        rate_limit_per_hour: int = 10
    ) -> Dict[str, Any]:
        """Generate alert system configuration"""
        return {
            'email_alerts': {
                'enabled': enabled,
                'smtp_server': 'smtp.test.com',
                'smtp_port': 587,
                'use_tls': True,
                'timeout': 30
            },
            'alerts': {
                'enabled': enabled,
                'min_severity': min_severity,
                'rate_limiting': {
                    'enabled': True,
                    'max_alerts_per_hour': rate_limit_per_hour,
                    'max_alerts_per_day': rate_limit_per_hour * 5
                }
            }
        }
    
    @staticmethod
    def generate_database_config(
        host: str = "localhost",
        port: int = 5432,
        name: str = "test_mltrading"
    ) -> Dict[str, Any]:
        """Generate database configuration"""
        return {
            'database': {
                'host': host,
                'port': port,
                'name': name,
                'user': 'test_user',
                'min_connections': 1,
                'max_connections': 5,
                'timeout': 10
            }
        }


class EventDataGenerator:
    """Generate event-based data for testing workflows and alerts"""
    
    @staticmethod
    def generate_trading_events(count: int = 10) -> List[Dict[str, Any]]:
        """Generate trading event data"""
        events = []
        event_types = ['order_placed', 'order_filled', 'order_cancelled', 'position_opened', 'position_closed']
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
        
        for i in range(count):
            events.append({
                'id': f"event_{i}",
                'timestamp': datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 1440)),
                'type': random.choice(event_types),
                'symbol': random.choice(symbols),
                'quantity': random.randint(1, 1000),
                'price': round(random.uniform(50, 300), 2),
                'status': random.choice(['success', 'pending', 'failed'])
            })
        
        return events
    
    @staticmethod
    def generate_system_events(count: int = 20) -> List[Dict[str, Any]]:
        """Generate system event data for alert testing"""
        events = []
        event_types = [
            ('database_connection_failed', 'HIGH'),
            ('api_rate_limit_exceeded', 'MEDIUM'),
            ('system_startup', 'INFO'),
            ('memory_usage_high', 'MEDIUM'),
            ('disk_space_low', 'HIGH'),
            ('backup_completed', 'INFO'),
            ('security_login_failed', 'CRITICAL')
        ]
        
        components = ['DatabaseService', 'APIService', 'SystemMonitor', 'BackupService', 'AuthService']
        
        for i in range(count):
            event_type, severity = random.choice(event_types)
            events.append({
                'id': f"sys_event_{i}",
                'timestamp': datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 1440)),
                'type': event_type,
                'severity': severity,
                'component': random.choice(components),
                'message': f"Test {event_type} event #{i}",
                'metadata': {
                    'hostname': f"server-{random.randint(1, 5)}",
                    'process_id': random.randint(1000, 9999)
                }
            })
        
        return events


def generate_random_string(length: int = 10) -> str:
    """Generate random string for testing"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_test_symbols(count: int = 10) -> List[str]:
    """Generate list of test stock symbols"""
    return [f"TEST{i:03d}" for i in range(count)]