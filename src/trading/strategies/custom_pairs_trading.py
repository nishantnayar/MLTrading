"""
Custom Pairs Trading Strategy
Simplified implementation for user-defined pairs with custom selection logic
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from .base_strategy import BaseStrategy, StrategySignal, SignalType
from ...utils.logging_config import get_combined_logger, log_operation
from ...utils.database_logging import get_trading_logger

logger = get_combined_logger("mltrading.custom_pairs")
trading_logger = get_trading_logger()


@dataclass


class CustomPair:
    """Simple pair definition with basic parameters"""
    symbol_a: str
    symbol_b: str
    hedge_ratio: float = 1.0  # How many shares of B per share of A
    entry_threshold: float = 2.0  # Z-score for entry
    exit_threshold: float = 0.5   # Z-score for exit
    stop_loss_threshold: float = 3.0  # Z-score for stop loss
    lookback_period: int = 20  # Days for spread calculation

    @property


    def pair_name(self) -> str:
        return f"{self.symbol_a}_{self.symbol_b}"


@dataclass


class PairTrade:
    """Active pair trade position"""
    pair: CustomPair
    entry_time: datetime
    entry_spread: float
    entry_zscore: float
    position_type: str  # 'long_spread' or 'short_spread'
    quantity_a: int
    quantity_b: int
    entry_price_a: float
    entry_price_b: float
    target_profit: Optional[float] = None
    max_loss: Optional[float] = None


class CustomPairsTradingStrategy(BaseStrategy):
    """
    Custom Pairs Trading Strategy

    Allows you to define your own pairs and implement custom selection logic
    while handling the trading mechanics automatically
    """


    def __init__(self,
                 pairs_config: List[Dict[str, Any]],
                 position_size_usd: float = 10000,  # Dollar amount per pair
                 **kwargs):
        """
        Initialize custom pairs trading strategy

        Args:
            pairs_config: List of pair configurations
            position_size_usd: Dollar amount to allocate per pair trade

        Example pairs_config:
        [
            {
                'symbol_a': 'AAPL',
                'symbol_b': 'MSFT',
                'hedge_ratio': 0.8,
                'entry_threshold': 2.0,
                'exit_threshold': 0.5
            },
            {
                'symbol_a': 'KO',
                'symbol_b': 'PEP',
                'hedge_ratio': 1.2,
                'entry_threshold': 1.8,
                'exit_threshold': 0.3
            }
        ]
        """
        # Extract all symbols from pairs
        all_symbols = set()
        for pair_config in pairs_config:
            all_symbols.add(pair_config['symbol_a'])
            all_symbols.add(pair_config['symbol_b'])

        parameters = {
            'position_size_usd': position_size_usd,
            'num_pairs': len(pairs_config)
        }

        super().__init__(
            name="Custom_Pairs_Trading",
            symbols=list(all_symbols),
            parameters=parameters,
            **kwargs
        )

        # Create pair objects
        self.trading_pairs = []
        for config in pairs_config:
            pair = CustomPair(
                symbol_a=config['symbol_a'],
                symbol_b=config['symbol_b'],
                hedge_ratio=config.get('hedge_ratio', 1.0),
                entry_threshold=config.get('entry_threshold', 2.0),
                exit_threshold=config.get('exit_threshold', 0.5),
                stop_loss_threshold=config.get('stop_loss_threshold', 3.0),
                lookback_period=config.get('lookback_period', 20)
            )
            self.trading_pairs.append(pair)

        self.position_size_usd = position_size_usd

        # Trading state
        self.active_trades: Dict[str, PairTrade] = {}
        self.spread_history: Dict[str, List[float]] = {}
        self.spread_stats: Dict[str, Dict[str, float]] = {}

        logger.info(f"Custom pairs strategy initialized with {len(self.trading_pairs)} pairs")
        for pair in self.trading_pairs:
            logger.info(f"  {pair.pair_name}: hedge_ratio={pair.hedge_ratio}")


    def implement_custom_pair_selection(self, market_data: Dict[str, pd.DataFrame]) -> List[CustomPair]:
        """
        IMPLEMENT YOUR CUSTOM PAIR SELECTION LOGIC HERE

        This method is called periodically to update which pairs should be traded.
        You can implement any logic you want here.

        Args:
            market_data: Current market data for all symbols

        Returns:
            List of pairs that should be actively traded
        """
        # DEFAULT IMPLEMENTATION - OVERRIDE THIS METHOD
        # For now, return all configured pairs
        active_pairs = []

        for pair in self.trading_pairs:
            # Example custom logic - you can implement your own criteria
            if self._is_pair_tradeable(pair, market_data):
                active_pairs.append(pair)

        return active_pairs


    def _is_pair_tradeable(self, pair: CustomPair, market_data: Dict[str, pd.DataFrame]) -> bool:
        """
        Example method to determine if a pair should be traded
        CUSTOMIZE THIS METHOD WITH YOUR OWN LOGIC
        """
        # Check if we have sufficient data for both symbols
        if pair.symbol_a not in market_data or pair.symbol_b not in market_data:
            return False

        data_a = market_data[pair.symbol_a]
        data_b = market_data[pair.symbol_b]

        # Ensure we have enough historical data
        if len(data_a) < pair.lookback_period or len(data_b) < pair.lookback_period:
            return False

        # Example: Check recent volatility
        recent_days = 5
        if len(data_a) >= recent_days:
            recent_vol_a = data_a['close'].tail(recent_days).pct_change().std()
            recent_vol_b = data_b['close'].tail(recent_days).pct_change().std()

            # Don't trade if either stock is too volatile (customize threshold)
            if recent_vol_a > 0.05 or recent_vol_b > 0.05:  # 5% daily volatility
                return False

        # Example: Check correlation over recent period
        if len(data_a) >= pair.lookback_period:
            returns_a = data_a['close'].tail(pair.lookback_period).pct_change().dropna()
            returns_b = data_b['close'].tail(pair.lookback_period).pct_change().dropna()

            # Ensure we have aligned data
            aligned_data = pd.DataFrame({'a': returns_a, 'b': returns_b}).dropna()

            if len(aligned_data) >= 10:
                correlation = aligned_data['a'].corr(aligned_data['b'])

                # Only trade if correlation is strong enough (customize threshold)
                if abs(correlation) < 0.6:
                    return False

        # ADD YOUR CUSTOM SELECTION CRITERIA HERE
        # Examples:
        # - Fundamental analysis ratios
        # - Technical indicators
        # - Market regime detection
        # - Sector relationships
        # - News sentiment
        # - Economic indicators

        return True


    def _calculate_spread_zscore(self, pair: CustomPair, market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate the current Z-score of the spread"""
        try:
            data_a = market_data[pair.symbol_a]
            data_b = market_data[pair.symbol_b]

            # Get recent prices for spread calculation
            lookback_data_a = data_a['close'].tail(pair.lookback_period)
            lookback_data_b = data_b['close'].tail(pair.lookback_period)

            # Calculate historical spread
            spread_series = lookback_data_b - pair.hedge_ratio * lookback_data_a

            # Calculate spread statistics
            spread_mean = spread_series.mean()
            spread_std = spread_series.std()

            # Store spread stats for this pair
            self.spread_stats[pair.pair_name] = {
                'mean': spread_mean,
                'std': spread_std,
                'current': spread_series.iloc[-1]
            }

            # Calculate Z-score
            current_spread = spread_series.iloc[-1]
            z_score = (current_spread - spread_mean) / spread_std if spread_std > 0 else 0

            return z_score

        except Exception as e:
            self.logger.error(f"Error calculating spread Z-score for {pair.pair_name}: {e}")
            return 0.0


    def generate_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[StrategySignal]:
        """Generate trading signals for pairs"""
        signals = []

        try:
            # Get active pairs from your custom selection logic
            active_pairs = self.implement_custom_pair_selection(market_data)

            if not active_pairs:
                self.logger.info("No pairs selected for trading by custom logic")
                return signals

            # Check each active pair for signals
            for pair in active_pairs:
                if pair.symbol_a not in market_data or pair.symbol_b not in market_data:
                    continue

                # Calculate current spread Z-score
                z_score = self._calculate_spread_zscore(pair, market_data)

                # Get current prices
                current_price_a = market_data[pair.symbol_a]['close'].iloc[-1]
                current_price_b = market_data[pair.symbol_b]['close'].iloc[-1]

                # Check if we have an active trade for this pair
                if pair.pair_name not in self.active_trades:
                    # Look for entry signals
                    entry_signals = self._check_entry_signals(pair, z_score, current_price_a, current_price_b)
                    signals.extend(entry_signals)
                else:
                    # Look for exit signals
                    exit_signals = self._check_exit_signals(pair, z_score, current_price_a, current_price_b)
                    signals.extend(exit_signals)

        except Exception as e:
            self.logger.error(f"Error generating custom pairs signals: {e}")

        return signals


    def _check_entry_signals(self, pair: CustomPair, z_score: float,
                           price_a: float, price_b: float) -> List[StrategySignal]:
        """Check for entry signals on a pair"""
        signals = []

        try:
            # Entry signal when spread diverges beyond threshold
            if abs(z_score) >= pair.entry_threshold:

                if z_score > pair.entry_threshold:
                    # Spread is high -> short the spread (buy A, sell B)
                    signals.extend([
                        StrategySignal(
                            symbol=pair.symbol_a,
                            signal_type=SignalType.BUY,
                            strength=min(abs(z_score) / pair.entry_threshold, 1.0),
                            timestamp=datetime.now(timezone.utc),
                            price=price_a,
                            metadata={
                                'pair_name': pair.pair_name,
                                'trade_type': 'short_spread',
                                'z_score': z_score,
                                'hedge_ratio': pair.hedge_ratio,
                                'strategy': 'custom_pairs'
                            }
                        ),
                        StrategySignal(
                            symbol=pair.symbol_b,
                            signal_type=SignalType.SELL,
                            strength=min(abs(z_score) / pair.entry_threshold, 1.0),
                            timestamp=datetime.now(timezone.utc),
                            price=price_b,
                            metadata={
                                'pair_name': pair.pair_name,
                                'trade_type': 'short_spread',
                                'z_score': z_score,
                                'hedge_ratio': pair.hedge_ratio,
                                'strategy': 'custom_pairs'
                            }
                        )
                    ])

                    self.logger.info(f"Entry: Short spread {pair.pair_name} (Z={z_score:.2f})")

                elif z_score < -pair.entry_threshold:
                    # Spread is low -> long the spread (sell A, buy B)
                    signals.extend([
                        StrategySignal(
                            symbol=pair.symbol_a,
                            signal_type=SignalType.SELL,
                            strength=min(abs(z_score) / pair.entry_threshold, 1.0),
                            timestamp=datetime.now(timezone.utc),
                            price=price_a,
                            metadata={
                                'pair_name': pair.pair_name,
                                'trade_type': 'long_spread',
                                'z_score': z_score,
                                'hedge_ratio': pair.hedge_ratio,
                                'strategy': 'custom_pairs'
                            }
                        ),
                        StrategySignal(
                            symbol=pair.symbol_b,
                            signal_type=SignalType.BUY,
                            strength=min(abs(z_score) / pair.entry_threshold, 1.0),
                            timestamp=datetime.now(timezone.utc),
                            price=price_b,
                            metadata={
                                'pair_name': pair.pair_name,
                                'trade_type': 'long_spread',
                                'z_score': z_score,
                                'hedge_ratio': pair.hedge_ratio,
                                'strategy': 'custom_pairs'
                            }
                        )
                    ])

                    self.logger.info(f"Entry: Long spread {pair.pair_name} (Z={z_score:.2f})")

        except Exception as e:
            self.logger.error(f"Error checking entry signals for {pair.pair_name}: {e}")

        return signals


    def _check_exit_signals(self, pair: CustomPair, z_score: float,
                          price_a: float, price_b: float) -> List[StrategySignal]:
        """Check for exit signals on active trades"""
        signals = []

        try:
            if pair.pair_name not in self.active_trades:
                return signals

            trade = self.active_trades[pair.pair_name]

            # Exit conditions
            should_exit = False
            exit_reason = ""

            # Mean reversion exit
            if abs(z_score) <= pair.exit_threshold:
                should_exit = True
                exit_reason = "mean_reversion"

            # Stop loss exit
            elif abs(z_score) >= pair.stop_loss_threshold:
                should_exit = True
                exit_reason = "stop_loss"

            # Time-based exit (optional)
            days_in_trade = (datetime.now(timezone.utc) - trade.entry_time).days
            if days_in_trade >= 30:  # Max 30 days per trade
                should_exit = True
                exit_reason = "time_limit"

            if should_exit:
                # Generate exit signals (reverse the positions)
                if trade.quantity_a > 0:  # Long A position
                    signals.append(StrategySignal(
                        symbol=pair.symbol_a,
                        signal_type=SignalType.SELL,
                        strength=0.9,
                        timestamp=datetime.now(timezone.utc),
                        price=price_a,
                        quantity=abs(trade.quantity_a),
                        metadata={
                            'pair_name': pair.pair_name,
                            'exit_reason': exit_reason,
                            'z_score': z_score,
                            'strategy': 'custom_pairs'
                        }
                    ))
                else:  # Short A position
                    signals.append(StrategySignal(
                        symbol=pair.symbol_a,
                        signal_type=SignalType.BUY,
                        strength=0.9,
                        timestamp=datetime.now(timezone.utc),
                        price=price_a,
                        quantity=abs(trade.quantity_a),
                        metadata={
                            'pair_name': pair.pair_name,
                            'exit_reason': exit_reason,
                            'z_score': z_score,
                            'strategy': 'custom_pairs'
                        }
                    ))

                if trade.quantity_b > 0:  # Long B position
                    signals.append(StrategySignal(
                        symbol=pair.symbol_b,
                        signal_type=SignalType.SELL,
                        strength=0.9,
                        timestamp=datetime.now(timezone.utc),
                        price=price_b,
                        quantity=abs(trade.quantity_b),
                        metadata={
                            'pair_name': pair.pair_name,
                            'exit_reason': exit_reason,
                            'z_score': z_score,
                            'strategy': 'custom_pairs'
                        }
                    ))
                else:  # Short B position
                    signals.append(StrategySignal(
                        symbol=pair.symbol_b,
                        signal_type=SignalType.BUY,
                        strength=0.9,
                        timestamp=datetime.now(timezone.utc),
                        price=price_b,
                        quantity=abs(trade.quantity_b),
                        metadata={
                            'pair_name': pair.pair_name,
                            'exit_reason': exit_reason,
                            'z_score': z_score,
                            'strategy': 'custom_pairs'
                        }
                    ))

                self.logger.info(f"Exit: {pair.pair_name} ({exit_reason}, Z={z_score:.2f})")

                # Remove from active trades
                del self.active_trades[pair.pair_name]

        except Exception as e:
            self.logger.error(f"Error checking exit signals for {pair.pair_name}: {e}")

        return signals


    def calculate_position_size(self, signal: StrategySignal, available_capital: float) -> int:
        """Calculate position size for pairs trading"""
        try:
            if not signal.metadata or 'pair_name' not in signal.metadata:
                return 0

            # pair_name = signal.metadata['pair_name']  # Currently unused
            hedge_ratio = signal.metadata.get('hedge_ratio', 1.0)

            # Find the pair configuration
            pair = next((p for p in self.trading_pairs if p.pair_name == pair_name), None)
            if not pair:
                return 0

            # Use fixed dollar amount per pair
            allocation = min(self.position_size_usd, available_capital * 0.1)  # Max 10% per pair

            price = signal.price if signal.price else 100.0

            if signal.symbol == pair.symbol_a:
                # Position size for symbol A
                quantity = int(allocation * 0.5 / price)  # Use half allocation for each leg
            else:
                # Position size for symbol B (adjusted for hedge ratio)
                quantity = int(allocation * 0.5 / price)
                quantity = int(quantity * hedge_ratio)

            return max(quantity, 1)

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0


    def update_position(self, symbol: str, fill_data: Dict[str, Any]):
        """Update position after fill and track pair trades"""
        try:
            super().update_position(symbol, fill_data)

            # Check if this is part of a pair trade
            # pair_name = fill_data.get('pair_name')  # Currently unused
            if pair_name and pair_name not in self.active_trades:
                # This could be the first leg of a pair trade
                # In practice, you'd want more sophisticated order management
                # to ensure both legs are filled before considering the trade active
                pass

        except Exception as e:
            self.logger.error(f"Error updating pairs position: {e}")


    def get_custom_pairs_status(self) -> Dict[str, Any]:
        """Get status of custom pairs trading"""
        status = {
            'configured_pairs': len(self.trading_pairs),
            'active_trades': len(self.active_trades),
            'position_size_usd': self.position_size_usd,
            'pairs_config': [
                {
                    'pair_name': pair.pair_name,
                    'hedge_ratio': pair.hedge_ratio,
                    'entry_threshold': pair.entry_threshold,
                    'exit_threshold': pair.exit_threshold
                }
                for pair in self.trading_pairs
            ],
            'spread_stats': self.spread_stats,
            'active_trades_detail': [
                {
                    'pair_name': trade.pair.pair_name,
                    'entry_time': trade.entry_time.isoformat(),
                    'entry_zscore': trade.entry_zscore,
                    'position_type': trade.position_type,
                    'quantity_a': trade.quantity_a,
                    'quantity_b': trade.quantity_b
                }
                for trade in self.active_trades.values()
            ]
        }

        return status


# EXAMPLE USAGE AND CONFIGURATION


def create_sample_pairs_strategy():
    """
    Example of how to create a custom pairs trading strategy
    """
    # Define your pairs with custom parameters
    pairs_config = [
        {
            'symbol_a': 'AAPL',
            'symbol_b': 'MSFT',
            'hedge_ratio': 0.85,  # 0.85 shares of MSFT per share of AAPL
            'entry_threshold': 2.0,
            'exit_threshold': 0.5,
            'stop_loss_threshold': 3.0,
            'lookback_period': 30
        },
        {
            'symbol_a': 'KO',
            'symbol_b': 'PEP',
            'hedge_ratio': 1.2,  # 1.2 shares of PEP per share of KO
            'entry_threshold': 1.8,
            'exit_threshold': 0.3,
            'stop_loss_threshold': 2.5,
            'lookback_period': 25
        }
    ]

    # Create strategy
    strategy = CustomPairsTradingStrategy(
        pairs_config=pairs_config,
        position_size_usd=15000,  # $15k per pair trade
        risk_params={
            'max_position_size': 1000,
            'risk_per_trade': 0.02
        }
    )

    return strategy

