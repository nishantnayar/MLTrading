"""
Simple Moving Average Strategy
A basic trend-following strategy using moving average crossovers
"""

from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from .base_strategy import BaseStrategy, StrategySignal, SignalType


class SimpleMovingAverageStrategy(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy
    
    Generates buy signals when short MA crosses above long MA
    Generates sell signals when short MA crosses below long MA
    """
    
    def __init__(self, 
                 symbols: List[str],
                 short_window: int = 10,
                 long_window: int = 20,
                 min_signal_strength: float = 0.6,
                 **kwargs):
        """
        Initialize SMA strategy
        
        Args:
            symbols: List of symbols to trade
            short_window: Short moving average period
            long_window: Long moving average period
            min_signal_strength: Minimum signal strength to trade
        """
        parameters = {
            'short_window': short_window,
            'long_window': long_window,
            'min_signal_strength': min_signal_strength
        }
        
        super().__init__(
            name="Simple_Moving_Average",
            symbols=symbols,
            parameters=parameters,
            **kwargs
        )
        
        self.short_window = short_window
        self.long_window = long_window
        self.min_signal_strength = min_signal_strength
        
        # Strategy state tracking
        self.previous_signals: Dict[str, SignalType] = {}
    
    def _update_indicators(self, symbol: str, data: pd.DataFrame):
        """Update SMA-specific indicators"""
        super()._update_indicators(symbol, data)
        
        if symbol not in self.indicators:
            self.indicators[symbol] = {}
        
        if len(data) >= self.long_window:
            # Calculate moving averages
            self.indicators[symbol]['sma_short'] = data['close'].rolling(self.short_window).mean()
            self.indicators[symbol]['sma_long'] = data['close'].rolling(self.long_window).mean()
            
            # Calculate crossover signals
            sma_short = self.indicators[symbol]['sma_short']
            sma_long = self.indicators[symbol]['sma_long']
            
            # Crossover detection
            self.indicators[symbol]['crossover'] = np.where(
                (sma_short > sma_long) & (sma_short.shift(1) <= sma_long.shift(1)), 1,
                np.where((sma_short < sma_long) & (sma_short.shift(1) >= sma_long.shift(1)), -1, 0)
            )
            
            # Signal strength based on MA separation
            ma_separation = np.abs(sma_short - sma_long) / sma_long
            self.indicators[symbol]['signal_strength'] = np.clip(ma_separation * 10, 0.1, 1.0)
    
    def generate_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[StrategySignal]:
        """
        Generate trading signals based on moving average crossovers
        
        Args:
            market_data: Dictionary of symbol -> DataFrame with OHLCV data
            
        Returns:
            List of trading signals
        """
        signals = []
        
        try:
            for symbol in self.symbols:
                if symbol not in market_data:
                    continue
                
                data = market_data[symbol]
                if len(data) < self.long_window:
                    self.logger.debug(f"Insufficient data for {symbol}: {len(data)} < {self.long_window}")
                    continue
                
                # Update indicators for this symbol
                self.update_market_data(symbol, data)
                
                # Get latest crossover signal
                if symbol in self.indicators and 'crossover' in self.indicators[symbol]:
                    crossover = self.indicators[symbol]['crossover']
                    signal_strength = self.indicators[symbol]['signal_strength']
                    
                    latest_crossover = crossover.iloc[-1] if len(crossover) > 0 else 0
                    latest_strength = signal_strength.iloc[-1] if len(signal_strength) > 0 else 0
                    
                    # Generate signal based on crossover
                    signal_type = None
                    if latest_crossover > 0:  # Bullish crossover
                        signal_type = SignalType.BUY
                    elif latest_crossover < 0:  # Bearish crossover
                        signal_type = SignalType.SELL
                    
                    # Only generate signal if:
                    # 1. We have a crossover
                    # 2. Signal strength is above threshold
                    # 3. It's different from previous signal
                    if (signal_type and 
                        latest_strength >= self.min_signal_strength and
                        self.previous_signals.get(symbol) != signal_type):
                        
                        signal = StrategySignal(
                            symbol=symbol,
                            signal_type=signal_type,
                            strength=float(latest_strength),
                            timestamp=datetime.now(timezone.utc),
                            price=float(data['close'].iloc[-1]),
                            metadata={
                                'sma_short': float(self.indicators[symbol]['sma_short'].iloc[-1]),
                                'sma_long': float(self.indicators[symbol]['sma_long'].iloc[-1]),
                                'crossover_value': float(latest_crossover),
                                'strategy_type': 'sma_crossover'
                            }
                        )
                        
                        signals.append(signal)
                        self.previous_signals[symbol] = signal_type
                        
                        self.logger.info(
                            f"Generated {signal_type.value} signal for {symbol} "
                            f"(strength: {latest_strength:.3f})"
                        )
        
        except Exception as e:
            self.logger.error(f"Error generating SMA signals: {e}")
        
        return signals
    
    def calculate_position_size(self, signal: StrategySignal, available_capital: float) -> int:
        """
        Calculate position size based on available capital and risk management
        
        Args:
            signal: Trading signal
            available_capital: Available capital for trading
            
        Returns:
            Position size (number of shares)
        """
        try:
            # Risk per trade as percentage of available capital
            risk_per_trade = self.risk_params.get('risk_per_trade', 0.02)  # 2%
            
            # Calculate risk amount
            risk_amount = available_capital * risk_per_trade
            
            # Use signal price or current market price
            price = signal.price if signal.price else 100.0  # Default fallback
            
            # Calculate position size based on risk amount and stop loss
            stop_loss_distance = price * self.stop_loss_pct
            
            if stop_loss_distance > 0:
                position_size = int(risk_amount / stop_loss_distance)
            else:
                # Fallback calculation
                position_size = int(risk_amount / price)
            
            # Apply signal strength weighting
            position_size = int(position_size * signal.strength)
            
            # Ensure position size doesn't exceed limits
            max_position_value = available_capital * 0.1  # Max 10% of capital per position
            max_shares_by_value = int(max_position_value / price)
            
            position_size = min(position_size, max_shares_by_value, self.max_position_size)
            
            # Minimum position size
            min_position_size = self.parameters.get('min_position_size', 1)
            if position_size < min_position_size:
                position_size = 0
            
            self.logger.debug(
                f"Position size calculation for {signal.symbol}: "
                f"risk_amount=${risk_amount:.2f}, price=${price:.2f}, "
                f"position_size={position_size}"
            )
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size for {signal.symbol}: {e}")
            return 0


class MomentumStrategy(BaseStrategy):
    """
    Simple Momentum Strategy
    
    Buys when price is above moving average and RSI indicates momentum
    Sells when price is below moving average or RSI is overbought
    """
    
    def __init__(self, 
                 symbols: List[str],
                 lookback_period: int = 20,
                 rsi_period: int = 14,
                 rsi_oversold: int = 30,
                 rsi_overbought: int = 70,
                 **kwargs):
        """
        Initialize Momentum strategy
        
        Args:
            symbols: List of symbols to trade
            lookback_period: Period for moving average
            rsi_period: Period for RSI calculation
            rsi_oversold: RSI level for oversold condition
            rsi_overbought: RSI level for overbought condition
        """
        parameters = {
            'lookback_period': lookback_period,
            'rsi_period': rsi_period,
            'rsi_oversold': rsi_oversold,
            'rsi_overbought': rsi_overbought
        }
        
        super().__init__(
            name="Momentum_Strategy",
            symbols=symbols,
            parameters=parameters,
            **kwargs
        )
        
        self.lookback_period = lookback_period
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
    
    def generate_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[StrategySignal]:
        """Generate momentum-based trading signals"""
        signals = []
        
        try:
            for symbol in self.symbols:
                if symbol not in market_data:
                    continue
                
                data = market_data[symbol]
                if len(data) < max(self.lookback_period, self.rsi_period):
                    continue
                
                # Update indicators
                self.update_market_data(symbol, data)
                
                if symbol not in self.indicators:
                    continue
                
                # Get latest values
                current_price = data['close'].iloc[-1]
                sma = self.indicators[symbol].get('sma_20')
                rsi = self.indicators[symbol].get('rsi')
                
                if sma is None or rsi is None:
                    continue
                
                latest_sma = sma.iloc[-1]
                latest_rsi = rsi.iloc[-1]
                
                # Generate signals
                signal_type = None
                strength = 0.0
                
                # Buy conditions: price above SMA and RSI oversold
                if (current_price > latest_sma and 
                    latest_rsi < self.rsi_oversold and
                    symbol not in self.positions):
                    
                    signal_type = SignalType.BUY
                    # Strength based on how oversold and price above MA
                    price_momentum = (current_price - latest_sma) / latest_sma
                    rsi_momentum = (self.rsi_oversold - latest_rsi) / self.rsi_oversold
                    strength = np.clip((price_momentum + rsi_momentum) / 2, 0.1, 1.0)
                
                # Sell conditions: price below SMA or RSI overbought
                elif ((current_price < latest_sma or latest_rsi > self.rsi_overbought) and
                      symbol in self.positions):
                    
                    signal_type = SignalType.SELL
                    strength = 0.8  # High confidence for exit signals
                
                if signal_type and strength >= 0.5:
                    signal = StrategySignal(
                        symbol=symbol,
                        signal_type=signal_type,
                        strength=strength,
                        timestamp=datetime.now(timezone.utc),
                        price=current_price,
                        metadata={
                            'sma_value': float(latest_sma),
                            'rsi_value': float(latest_rsi),
                            'price_above_sma': current_price > latest_sma,
                            'strategy_type': 'momentum'
                        }
                    )
                    
                    signals.append(signal)
                    self.logger.info(
                        f"Generated {signal_type.value} signal for {symbol} "
                        f"(RSI: {latest_rsi:.1f}, Price vs SMA: {((current_price/latest_sma-1)*100):+.1f}%)"
                    )
        
        except Exception as e:
            self.logger.error(f"Error generating momentum signals: {e}")
        
        return signals
    
    def calculate_position_size(self, signal: StrategySignal, available_capital: float) -> int:
        """Calculate position size for momentum strategy"""
        # Use similar logic to SMA strategy but with momentum-specific adjustments
        try:
            risk_per_trade = self.risk_params.get('risk_per_trade', 0.015)  # Slightly lower risk
            risk_amount = available_capital * risk_per_trade
            
            price = signal.price if signal.price else 100.0
            stop_loss_distance = price * self.stop_loss_pct
            
            if stop_loss_distance > 0:
                position_size = int(risk_amount / stop_loss_distance)
            else:
                position_size = int(risk_amount / price)
            
            # Apply signal strength and momentum weighting
            momentum_multiplier = min(signal.strength * 1.5, 1.0)
            position_size = int(position_size * momentum_multiplier)
            
            # Apply position limits
            max_position_value = available_capital * 0.08  # Max 8% per position
            max_shares = int(max_position_value / price)
            position_size = min(position_size, max_shares, self.max_position_size)
            
            return max(position_size, 0)
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0