"""
Pairs Trading Strategy
A market-neutral strategy that trades the spread between two correlated assets
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from scipy import stats
from sklearn.linear_model import LinearRegression

from .base_strategy import BaseStrategy, StrategySignal, SignalType
from ...utils.logging_config import get_combined_logger, log_operation
from ...utils.database_logging import get_trading_logger

logger = get_combined_logger("mltrading.pairs_trading")
trading_logger = get_trading_logger()


@dataclass
class TradingPair:
    """Represents a trading pair with its statistical properties"""
    symbol_a: str
    symbol_b: str
    correlation: float
    cointegration_pvalue: float
    hedge_ratio: float
    spread_mean: float
    spread_std: float
    half_life: float  # Mean reversion half-life in days
    last_updated: datetime
    
    @property
    def pair_name(self) -> str:
        return f"{self.symbol_a}_{self.symbol_b}"
    
    def is_valid(self, min_correlation: float = 0.7, max_pvalue: float = 0.05) -> bool:
        """Check if pair meets statistical criteria"""
        return (abs(self.correlation) >= min_correlation and 
                self.cointegration_pvalue <= max_pvalue and
                self.half_life > 0 and self.half_life < 252)  # Less than 1 year


@dataclass
class PairPosition:
    """Represents an active pairs trade position"""
    pair: TradingPair
    entry_time: datetime
    entry_spread: float
    position_type: str  # 'long_spread' or 'short_spread'
    quantity_a: int  # Positive for long, negative for short
    quantity_b: int  # Positive for long, negative for short
    entry_price_a: float
    entry_price_b: float
    current_spread: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    target_spread: Optional[float] = None  # Target for mean reversion
    stop_loss_spread: Optional[float] = None


class PairsTradingStrategy(BaseStrategy):
    """
    Pairs Trading Strategy Implementation
    
    Key Features:
    - Automatic pair selection based on correlation and cointegration
    - Statistical arbitrage using spread mean reversion
    - Market-neutral positions (long one asset, short another)
    - Dynamic hedge ratio calculation
    - Risk management with stop losses and position limits
    """
    
    def __init__(self,
                 symbols: List[str],
                 lookback_period: int = 252,  # 1 year for correlation
                 min_correlation: float = 0.75,
                 max_cointegration_pvalue: float = 0.05,
                 entry_threshold: float = 2.0,  # Z-score for entry
                 exit_threshold: float = 0.5,   # Z-score for exit
                 stop_loss_threshold: float = 3.0,  # Z-score for stop loss
                 max_pairs: int = 5,
                 rebalance_frequency_days: int = 30,
                 **kwargs):
        """
        Initialize pairs trading strategy
        
        Args:
            symbols: List of symbols to consider for pairs
            lookback_period: Days of historical data for analysis
            min_correlation: Minimum correlation for pair selection
            max_cointegration_pvalue: Maximum p-value for cointegration test
            entry_threshold: Z-score threshold for entering trades
            exit_threshold: Z-score threshold for exiting trades
            stop_loss_threshold: Z-score threshold for stop loss
            max_pairs: Maximum number of active pairs
            rebalance_frequency_days: Days between pair selection updates
        """
        parameters = {
            'lookback_period': lookback_period,
            'min_correlation': min_correlation,
            'max_cointegration_pvalue': max_cointegration_pvalue,
            'entry_threshold': entry_threshold,
            'exit_threshold': exit_threshold,
            'stop_loss_threshold': stop_loss_threshold,
            'max_pairs': max_pairs,
            'rebalance_frequency_days': rebalance_frequency_days
        }
        
        super().__init__(
            name="Pairs_Trading",
            symbols=symbols,
            parameters=parameters,
            **kwargs
        )
        
        # Strategy-specific parameters
        self.lookback_period = lookback_period
        self.min_correlation = min_correlation
        self.max_cointegration_pvalue = max_cointegration_pvalue
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.stop_loss_threshold = stop_loss_threshold
        self.max_pairs = max_pairs
        self.rebalance_frequency_days = rebalance_frequency_days
        
        # Pairs management
        self.available_pairs: List[TradingPair] = []
        self.active_pairs: Dict[str, PairPosition] = {}
        self.last_pair_selection_date: Optional[datetime] = None
        
        # Data storage for pairs analysis
        self.price_data: Dict[str, pd.Series] = {}
        self.spread_data: Dict[str, pd.Series] = {}
        
        logger.info(f"Pairs trading strategy initialized with {len(symbols)} symbols")
    
    def initialize(self, **kwargs):
        """Initialize the pairs trading strategy"""
        super().initialize(**kwargs)
        
        # Initial pair selection will happen on first signal generation
        self.logger.info("Pairs trading strategy ready for pair selection")
    
    def _calculate_correlation_matrix(self, price_data: Dict[str, pd.Series]) -> pd.DataFrame:
        """Calculate correlation matrix for all symbols"""
        try:
            # Align all price series to common dates
            price_df = pd.DataFrame(price_data)
            price_df = price_df.dropna()
            
            if len(price_df) < self.lookback_period // 2:
                self.logger.warning(f"Insufficient data for correlation calculation: {len(price_df)} days")
                return pd.DataFrame()
            
            # Calculate returns for correlation
            returns_df = price_df.pct_change().dropna()
            
            # Calculate correlation matrix
            correlation_matrix = returns_df.corr()
            
            return correlation_matrix
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()
    
    def _test_cointegration(self, series_a: pd.Series, series_b: pd.Series) -> Tuple[float, float, float]:
        """
        Test for cointegration between two price series using Engle-Granger test
        
        Returns:
            Tuple of (p_value, hedge_ratio, half_life)
        """
        try:
            # Ensure series are aligned
            aligned_data = pd.DataFrame({'a': series_a, 'b': series_b}).dropna()
            
            if len(aligned_data) < 30:
                return 1.0, 1.0, float('inf')
            
            prices_a = aligned_data['a'].values.reshape(-1, 1)
            prices_b = aligned_data['b'].values
            
            # Calculate hedge ratio using linear regression
            model = LinearRegression()
            model.fit(prices_a, prices_b)
            hedge_ratio = model.coef_[0]
            
            # Calculate spread
            spread = aligned_data['b'] - hedge_ratio * aligned_data['a']
            
            # Augmented Dickey-Fuller test for stationarity
            from statsmodels.tsa.stattools import adfuller
            adf_result = adfuller(spread.dropna(), maxlag=1)
            p_value = adf_result[1]
            
            # Calculate half-life of mean reversion
            half_life = self._calculate_half_life(spread)
            
            return p_value, hedge_ratio, half_life
            
        except Exception as e:
            self.logger.error(f"Error in cointegration test: {e}")
            return 1.0, 1.0, float('inf')
    
    def _calculate_half_life(self, spread: pd.Series) -> float:
        """Calculate the half-life of mean reversion for a spread"""
        try:
            spread_lag = spread.shift(1)
            spread_diff = spread.diff()
            
            # Remove NaN values
            data = pd.DataFrame({
                'spread': spread,
                'spread_lag': spread_lag,
                'spread_diff': spread_diff
            }).dropna()
            
            if len(data) < 10:
                return float('inf')
            
            # Fit regression: spread_diff = a + b * spread_lag
            X = data['spread_lag'].values.reshape(-1, 1)
            y = data['spread_diff'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            beta = model.coef_[0]
            
            if beta >= 0:
                return float('inf')
            
            # Half-life = -ln(2) / ln(1 + beta)
            half_life = -np.log(2) / np.log(1 + beta)
            
            return max(1, half_life)  # At least 1 day
            
        except Exception as e:
            self.logger.error(f"Error calculating half-life: {e}")
            return float('inf')
    
    def _select_trading_pairs(self, market_data: Dict[str, pd.DataFrame]) -> List[TradingPair]:
        """
        Select the best trading pairs based on statistical criteria
        
        Args:
            market_data: Dictionary of symbol -> DataFrame with OHLCV data
            
        Returns:
            List of valid trading pairs
        """
        try:
            with log_operation("select_trading_pairs", self.logger):
                # Extract price data
                price_data = {}
                for symbol, df in market_data.items():
                    if len(df) >= self.lookback_period // 2:
                        price_data[symbol] = df['close']
                
                if len(price_data) < 2:
                    self.logger.warning("Insufficient symbols with adequate data for pair selection")
                    return []
                
                # Calculate correlation matrix
                correlation_matrix = self._calculate_correlation_matrix(price_data)
                
                if correlation_matrix.empty:
                    return []
                
                # Find potential pairs
                potential_pairs = []
                symbols = list(price_data.keys())
                
                for i, symbol_a in enumerate(symbols):
                    for j, symbol_b in enumerate(symbols[i+1:], i+1):
                        correlation = correlation_matrix.loc[symbol_a, symbol_b]
                        
                        # Skip if correlation is too low
                        if abs(correlation) < self.min_correlation:
                            continue
                        
                        # Test cointegration
                        p_value, hedge_ratio, half_life = self._test_cointegration(
                            price_data[symbol_a], price_data[symbol_b]
                        )
                        
                        if p_value <= self.max_cointegration_pvalue and half_life < 252:
                            # Calculate spread statistics
                            spread = price_data[symbol_b] - hedge_ratio * price_data[symbol_a]
                            spread_mean = spread.mean()
                            spread_std = spread.std()
                            
                            pair = TradingPair(
                                symbol_a=symbol_a,
                                symbol_b=symbol_b,
                                correlation=correlation,
                                cointegration_pvalue=p_value,
                                hedge_ratio=hedge_ratio,
                                spread_mean=spread_mean,
                                spread_std=spread_std,
                                half_life=half_life,
                                last_updated=datetime.now(timezone.utc)
                            )
                            
                            potential_pairs.append(pair)
                            
                            self.logger.info(
                                f"Found valid pair: {pair.pair_name} "
                                f"(corr: {correlation:.3f}, p-val: {p_value:.4f}, "
                                f"half-life: {half_life:.1f} days)"
                            )
                
                # Sort pairs by quality (low p-value, high correlation, reasonable half-life)
                potential_pairs.sort(key=lambda p: (
                    p.cointegration_pvalue,
                    -abs(p.correlation),
                    p.half_life
                ))
                
                # Select top pairs
                selected_pairs = potential_pairs[:self.max_pairs]
                
                self.logger.info(f"Selected {len(selected_pairs)} pairs out of {len(potential_pairs)} candidates")
                
                # Log pair selection to database
                trading_logger.log_trading_event(
                    event_type="pairs_selected",
                    strategy=self.name,
                    pairs_count=len(selected_pairs),
                    selected_pairs=[p.pair_name for p in selected_pairs]
                )
                
                return selected_pairs
                
        except Exception as e:
            self.logger.error(f"Error selecting trading pairs: {e}")
            return []
    
    def _calculate_spread_zscore(self, pair: TradingPair, current_price_a: float, current_price_b: float) -> float:
        """Calculate the current Z-score of the spread"""
        try:
            current_spread = current_price_b - pair.hedge_ratio * current_price_a
            z_score = (current_spread - pair.spread_mean) / pair.spread_std
            return z_score
        except Exception as e:
            self.logger.error(f"Error calculating spread Z-score for {pair.pair_name}: {e}")
            return 0.0
    
    def generate_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[StrategySignal]:
        """
        Generate pairs trading signals
        
        Args:
            market_data: Dictionary of symbol -> DataFrame with OHLCV data
            
        Returns:
            List of trading signals
        """
        signals = []
        
        try:
            # Check if we need to update pair selection
            current_date = datetime.now(timezone.utc)
            if (self.last_pair_selection_date is None or 
                (current_date - self.last_pair_selection_date).days >= self.rebalance_frequency_days):
                
                self.logger.info("Updating pair selection")
                self.available_pairs = self._select_trading_pairs(market_data)
                self.last_pair_selection_date = current_date
            
            if not self.available_pairs:
                self.logger.warning("No valid pairs available for trading")
                return signals
            
            # Check each available pair for trading opportunities
            for pair in self.available_pairs:
                if pair.symbol_a not in market_data or pair.symbol_b not in market_data:
                    continue
                
                data_a = market_data[pair.symbol_a]
                data_b = market_data[pair.symbol_b]
                
                if data_a.empty or data_b.empty:
                    continue
                
                current_price_a = data_a['close'].iloc[-1]
                current_price_b = data_b['close'].iloc[-1]
                
                # Calculate current spread Z-score
                z_score = self._calculate_spread_zscore(pair, current_price_a, current_price_b)
                
                # Check if we have an active position in this pair
                pair_position = self.active_pairs.get(pair.pair_name)
                
                if pair_position is None:
                    # No active position - check for entry signals
                    entry_signals = self._check_entry_signals(pair, z_score, current_price_a, current_price_b)
                    signals.extend(entry_signals)
                else:
                    # Active position - check for exit signals
                    exit_signals = self._check_exit_signals(pair_position, z_score, current_price_a, current_price_b)
                    signals.extend(exit_signals)
        
        except Exception as e:
            self.logger.error(f"Error generating pairs trading signals: {e}")
        
        return signals
    
    def _check_entry_signals(self, pair: TradingPair, z_score: float, 
                           price_a: float, price_b: float) -> List[StrategySignal]:
        """Check for entry signals on a pair"""
        signals = []
        
        try:
            # Entry conditions based on Z-score thresholds
            if z_score > self.entry_threshold:
                # Spread is high -> short the spread (short B, long A)
                signals.extend([
                    StrategySignal(
                        symbol=pair.symbol_a,
                        signal_type=SignalType.BUY,
                        strength=min(abs(z_score) / self.entry_threshold, 1.0),
                        timestamp=datetime.now(timezone.utc),
                        price=price_a,
                        metadata={
                            'pair_name': pair.pair_name,
                            'pair_trade': 'long_a_short_b',
                            'z_score': z_score,
                            'hedge_ratio': pair.hedge_ratio,
                            'strategy_type': 'pairs_trading'
                        }
                    ),
                    StrategySignal(
                        symbol=pair.symbol_b,
                        signal_type=SignalType.SELL,
                        strength=min(abs(z_score) / self.entry_threshold, 1.0),
                        timestamp=datetime.now(timezone.utc),
                        price=price_b,
                        metadata={
                            'pair_name': pair.pair_name,
                            'pair_trade': 'long_a_short_b',
                            'z_score': z_score,
                            'hedge_ratio': pair.hedge_ratio,
                            'strategy_type': 'pairs_trading'
                        }
                    )
                ])
                
                self.logger.info(f"Entry signal: Short spread {pair.pair_name} (Z-score: {z_score:.2f})")
            
            elif z_score < -self.entry_threshold:
                # Spread is low -> long the spread (long B, short A)
                signals.extend([
                    StrategySignal(
                        symbol=pair.symbol_a,
                        signal_type=SignalType.SELL,
                        strength=min(abs(z_score) / self.entry_threshold, 1.0),
                        timestamp=datetime.now(timezone.utc),
                        price=price_a,
                        metadata={
                            'pair_name': pair.pair_name,
                            'pair_trade': 'short_a_long_b',
                            'z_score': z_score,
                            'hedge_ratio': pair.hedge_ratio,
                            'strategy_type': 'pairs_trading'
                        }
                    ),
                    StrategySignal(
                        symbol=pair.symbol_b,
                        signal_type=SignalType.BUY,
                        strength=min(abs(z_score) / self.entry_threshold, 1.0),
                        timestamp=datetime.now(timezone.utc),
                        price=price_b,
                        metadata={
                            'pair_name': pair.pair_name,
                            'pair_trade': 'short_a_long_b',
                            'z_score': z_score,
                            'hedge_ratio': pair.hedge_ratio,
                            'strategy_type': 'pairs_trading'
                        }
                    )
                ])
                
                self.logger.info(f"Entry signal: Long spread {pair.pair_name} (Z-score: {z_score:.2f})")
        
        except Exception as e:
            self.logger.error(f"Error checking entry signals for {pair.pair_name}: {e}")
        
        return signals
    
    def _check_exit_signals(self, position: PairPosition, z_score: float,
                          price_a: float, price_b: float) -> List[StrategySignal]:
        """Check for exit signals on an active position"""
        signals = []
        
        try:
            # Update position with current spread
            position.current_spread = price_b - position.pair.hedge_ratio * price_a
            
            # Exit conditions
            should_exit = False
            exit_reason = ""
            
            # Mean reversion exit
            if abs(z_score) <= self.exit_threshold:
                should_exit = True
                exit_reason = "mean_reversion"
            
            # Stop loss exit
            elif abs(z_score) >= self.stop_loss_threshold:
                should_exit = True
                exit_reason = "stop_loss"
            
            # Time-based exit (if position is old)
            days_in_position = (datetime.now(timezone.utc) - position.entry_time).days
            max_position_days = min(position.pair.half_life * 3, 60)  # Max 60 days
            
            if days_in_position >= max_position_days:
                should_exit = True
                exit_reason = "time_limit"
            
            if should_exit:
                # Generate exit signals (reverse the original positions)
                if position.quantity_a > 0:  # Long A
                    signals.append(StrategySignal(
                        symbol=position.pair.symbol_a,
                        signal_type=SignalType.SELL,
                        strength=0.9,  # High confidence for exits
                        timestamp=datetime.now(timezone.utc),
                        price=price_a,
                        quantity=abs(position.quantity_a),
                        metadata={
                            'pair_name': position.pair.pair_name,
                            'exit_reason': exit_reason,
                            'z_score': z_score,
                            'days_in_position': days_in_position,
                            'strategy_type': 'pairs_trading'
                        }
                    ))
                else:  # Short A
                    signals.append(StrategySignal(
                        symbol=position.pair.symbol_a,
                        signal_type=SignalType.BUY,
                        strength=0.9,
                        timestamp=datetime.now(timezone.utc),
                        price=price_a,
                        quantity=abs(position.quantity_a),
                        metadata={
                            'pair_name': position.pair.pair_name,
                            'exit_reason': exit_reason,
                            'z_score': z_score,
                            'days_in_position': days_in_position,
                            'strategy_type': 'pairs_trading'
                        }
                    ))
                
                if position.quantity_b > 0:  # Long B
                    signals.append(StrategySignal(
                        symbol=position.pair.symbol_b,
                        signal_type=SignalType.SELL,
                        strength=0.9,
                        timestamp=datetime.now(timezone.utc),
                        price=price_b,
                        quantity=abs(position.quantity_b),
                        metadata={
                            'pair_name': position.pair.pair_name,
                            'exit_reason': exit_reason,
                            'z_score': z_score,
                            'days_in_position': days_in_position,
                            'strategy_type': 'pairs_trading'
                        }
                    ))
                else:  # Short B
                    signals.append(StrategySignal(
                        symbol=position.pair.symbol_b,
                        signal_type=SignalType.BUY,
                        strength=0.9,
                        timestamp=datetime.now(timezone.utc),
                        price=price_b,
                        quantity=abs(position.quantity_b),
                        metadata={
                            'pair_name': position.pair.pair_name,
                            'exit_reason': exit_reason,
                            'z_score': z_score,
                            'days_in_position': days_in_position,
                            'strategy_type': 'pairs_trading'
                        }
                    ))
                
                self.logger.info(f"Exit signal: Close {position.pair.pair_name} position "
                               f"(reason: {exit_reason}, Z-score: {z_score:.2f})")
        
        except Exception as e:
            self.logger.error(f"Error checking exit signals for position: {e}")
        
        return signals
    
    def calculate_position_size(self, signal: StrategySignal, available_capital: float) -> int:
        """
        Calculate position size for pairs trading
        
        For pairs trading, position sizes must be carefully calculated to maintain
        the hedge ratio and ensure market neutrality
        """
        try:
            if not signal.metadata or 'pair_name' not in signal.metadata:
                self.logger.error("Signal missing pair metadata")
                return 0
            
            pair_name = signal.metadata['pair_name']
            hedge_ratio = signal.metadata.get('hedge_ratio', 1.0)
            
            # Risk per pair trade (both legs combined)
            risk_per_trade = self.risk_params.get('risk_per_trade', 0.02)
            
            # Allocate capital for this pair
            pair_capital = available_capital * risk_per_trade
            
            # For pairs trading, we need to calculate position sizes to maintain hedge ratio
            if signal.symbol.endswith('_A') or 'long_a' in signal.metadata.get('pair_trade', ''):
                # This is symbol A in the pair
                # Position size based on available capital and price
                price = signal.price if signal.price else 100.0
                base_quantity = int(pair_capital * 0.5 / price)  # Use half capital for each leg
                
                return max(base_quantity, 1)
            
            else:
                # This is symbol B in the pair
                # Position size should maintain hedge ratio with symbol A
                price = signal.price if signal.price else 100.0
                base_quantity = int(pair_capital * 0.5 / price)
                
                # Adjust for hedge ratio
                hedge_adjusted_quantity = int(base_quantity * hedge_ratio)
                
                return max(hedge_adjusted_quantity, 1)
        
        except Exception as e:
            self.logger.error(f"Error calculating position size for pairs trade: {e}")
            return 0
    
    def update_position(self, symbol: str, fill_data: Dict[str, Any]):
        """Update pairs position after order fill"""
        try:
            super().update_position(symbol, fill_data)
            
            # Check if this fill completes a pairs trade entry
            pair_trade = fill_data.get('pair_trade')
            pair_name = fill_data.get('pair_name')
            
            if pair_trade and pair_name:
                # Find the corresponding pair
                pair = next((p for p in self.available_pairs if p.pair_name == pair_name), None)
                
                if pair and pair_name not in self.active_pairs:
                    # This might be the first leg of a pairs trade
                    # Wait for both legs to be filled before creating position
                    # (In practice, you'd implement more sophisticated order management)
                    pass
            
        except Exception as e:
            self.logger.error(f"Error updating pairs position: {e}")
    
    def get_pairs_status(self) -> Dict[str, Any]:
        """Get detailed status of pairs trading strategy"""
        return {
            'available_pairs': len(self.available_pairs),
            'active_positions': len(self.active_pairs),
            'last_pair_selection': self.last_pair_selection_date.isoformat() if self.last_pair_selection_date else None,
            'pairs_details': [
                {
                    'pair_name': pair.pair_name,
                    'correlation': pair.correlation,
                    'cointegration_pvalue': pair.cointegration_pvalue,
                    'hedge_ratio': pair.hedge_ratio,
                    'half_life': pair.half_life
                }
                for pair in self.available_pairs
            ],
            'active_positions_details': [
                {
                    'pair_name': pos.pair.pair_name,
                    'entry_time': pos.entry_time.isoformat(),
                    'position_type': pos.position_type,
                    'entry_spread': pos.entry_spread,
                    'current_spread': pos.current_spread,
                    'unrealized_pnl': pos.unrealized_pnl
                }
                for pos in self.active_pairs.values()
            ]
        }