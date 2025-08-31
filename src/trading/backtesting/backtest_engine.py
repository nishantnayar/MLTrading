"""
Backtesting Engine
Simulates strategy performance on historical data
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

from ..strategies.base_strategy import BaseStrategy, StrategySignal, SignalType
from ...utils.logging_config import get_combined_logger, log_operation
from ...data.storage.database import DatabaseManager

logger = get_combined_logger("mltrading.backtesting")


@dataclass


class Trade:
    """Represents a completed trade"""
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    return_pct: float
    duration_hours: float
    strategy: str


@dataclass


class BacktestResult:
    """Results from a backtest run"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float

    # Risk metrics
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    volatility: float

    # Position statistics
    max_positions: int
    avg_position_size: float

    # Trade details
    trades: List[Trade]
    equity_curve: pd.Series
    drawdown_curve: pd.Series


    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'strategy_name': self.strategy_name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': self.total_return,
            'total_return_pct': self.total_return_pct,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown_pct,
            'sharpe_ratio': self.sharpe_ratio,
            'volatility': self.volatility,
            'max_positions': self.max_positions,
            'avg_position_size': self.avg_position_size
        }


class BacktestEngine:
    """
    Backtesting engine for trading strategies

    Simulates strategy execution on historical data and provides
    comprehensive performance metrics
    """


    def __init__(self,
                 initial_capital: float = 100000.0,
                 commission: float = 1.0,
                 slippage: float = 0.001):
        """
        Initialize backtest engine

        Args:
            initial_capital: Starting capital
            commission: Commission per trade
            slippage: Slippage as percentage of price
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        # Database for historical data
        self.db_manager = DatabaseManager()

        logger.info(f"BacktestEngine initialized with ${initial_capital:,.2f} capital")


    def load_historical_data(self,
                           symbols: List[str],
                           start_date: datetime,
                           end_date: datetime) -> Dict[str, pd.DataFrame]:
        """
        Load historical data for backtesting

        Args:
            symbols: List of symbols to load
            start_date: Start date for data
            end_date: End date for data

        Returns:
            Dictionary of symbol -> DataFrame with OHLCV data
        """
        try:
            with log_operation("load_historical_data", logger):
                historical_data = {}

                with self.db_manager.get_connection() as conn:
                    for symbol in symbols:
                        query = """
                        SELECT timestamp, open, high, low, close, volume
                        FROM stock_data
                        WHERE symbol = %s
                        AND timestamp BETWEEN %s AND %s
                        ORDER BY timestamp ASC
                        """

                        df = pd.read_sql_query(
                            query,
                            conn,
                            params=[symbol, start_date, end_date],
                            parse_dates=['timestamp']
                        )

                        if not df.empty:
                            df.set_index('timestamp', inplace=True)
                            historical_data[symbol] = df
                            logger.info(f"Loaded {len(df)} records for {symbol}")
                        else:
                            logger.warning(f"No data found for {symbol}")

                return historical_data

        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return {}


    def run_backtest(self,
                    strategy: BaseStrategy,
                    start_date: datetime,
                    end_date: datetime,
                    data: Dict[str, pd.DataFrame] = None) -> BacktestResult:
        """
        Run backtest for a strategy

        Args:
            strategy: Strategy to backtest
            start_date: Backtest start date
            end_date: Backtest end date
            data: Historical data (if None, will load from database)

        Returns:
            Backtest results
        """
        try:
            with log_operation(f"backtest_{strategy.name}", logger):
                # Load data if not provided
                if data is None:
                    data = self.load_historical_data(strategy.symbols, start_date, end_date)

                if not data:
                    raise ValueError("No historical data available for backtesting")

                # Initialize backtest state
                capital = self.initial_capital
                positions = {}
                trades = []
                equity_curve = []
                portfolio_values = []

                # Get all timestamps across all symbols
                all_timestamps = set()
                for df in data.values():
                    all_timestamps.update(df.index)

                timestamps = sorted(all_timestamps)

                logger.info(f"Running backtest for {strategy.name} from {start_date} to {end_date}")
                logger.info(f"Processing {len(timestamps)} timestamps")

                # Initialize strategy
                strategy.initialize()
                strategy.start()

                # Process each timestamp
                for i, timestamp in enumerate(timestamps):
                    # Get current market data slice
                    current_data = {}
                    for symbol, df in data.items():
                        if timestamp in df.index:
                            # Get data up to current timestamp
                            current_slice = df.loc[:timestamp]
                            if len(current_slice) > 0:
                                current_data[symbol] = current_slice

                    if not current_data:
                        continue

                    # Generate signals
                    signals = strategy.generate_signals(current_data)

                    # Process each signal
                    for signal in signals:
                        trade_result = self._execute_signal(
                            signal, capital, positions, current_data, timestamp
                        )

                        if trade_result:
                            if 'trade' in trade_result:
                                trades.append(trade_result['trade'])
                            capital = trade_result['new_capital']
                            positions = trade_result['positions']

                    # Calculate portfolio value
                    portfolio_value = self._calculate_portfolio_value(
                        capital, positions, current_data, timestamp
                    )
                    portfolio_values.append(portfolio_value)
                    equity_curve.append((timestamp, portfolio_value))

                    # Update strategy positions
                    for symbol, pos in positions.items():
                        if symbol in current_data and not current_data[symbol].empty:
                            current_price = current_data[symbol]['close'].iloc[-1]
                            strategy.positions[symbol].current_price = current_price

                # Calculate final results
                result = self._calculate_results(
                    strategy, start_date, end_date, trades,
                    equity_curve, portfolio_values
                )

                logger.info(f"Backtest completed: {result.total_trades} trades, "
                           f"{result.total_return_pct:.2f}% return")

                return result

        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            raise


    def _execute_signal(self,
                       signal: StrategySignal,
                       capital: float,
                       positions: Dict[str, Any],
                       market_data: Dict[str, pd.DataFrame],
                       timestamp: datetime) -> Optional[Dict[str, Any]]:
        """
        Execute a trading signal in the backtest

        Args:
            signal: Trading signal
            capital: Available capital
            positions: Current positions
            market_data: Current market data
            timestamp: Current timestamp

        Returns:
            Trade result with updated capital and positions
        """
        try:
            symbol = signal.symbol

            if symbol not in market_data or market_data[symbol].empty:
                return None

            current_price = market_data[symbol]['close'].iloc[-1]

            # Apply slippage
            if signal.signal_type in [SignalType.BUY]:
                execution_price = current_price * (1 + self.slippage)
            else:
                execution_price = current_price * (1 - self.slippage)

            new_capital = capital
            new_positions = positions.copy()
            trade = None

            if signal.signal_type == SignalType.BUY:
                # Calculate position size (simplified)
                if signal.quantity:
                    quantity = signal.quantity
                else:
                    # Use 10% of capital for position
                    position_value = capital * 0.1
                    quantity = int(position_value / execution_price)

                if quantity > 0:
                    cost = quantity * execution_price + self.commission

                    if cost <= capital:
                        new_capital -= cost
                        new_positions[symbol] = {
                            'quantity': quantity,
                            'entry_price': execution_price,
                            'entry_time': timestamp,
                            'cost': cost
                        }
                        logger.debug(f"Bought {quantity} {symbol} at ${execution_price:.2f}")

            elif signal.signal_type in [SignalType.SELL, SignalType.CLOSE_LONG]:
                if symbol in positions:
                    pos = positions[symbol]
                    quantity = pos['quantity']
                    entry_price = pos['entry_price']
                    entry_time = pos['entry_time']

                    proceeds = quantity * execution_price - self.commission
                    new_capital += proceeds

                    # Calculate PnL
                    pnl = proceeds - pos['cost']
                    return_pct = pnl / pos['cost'] * 100
                    duration = (timestamp - entry_time).total_seconds() / 3600  # hours

                    trade = Trade(
                        symbol=symbol,
                        entry_time=entry_time,
                        exit_time=timestamp,
                        entry_price=entry_price,
                        exit_price=execution_price,
                        quantity=quantity,
                        pnl=pnl,
                        return_pct=return_pct,
                        duration_hours=duration,
                        strategy=signal.metadata.get('strategy', 'unknown') if signal.metadata else 'unknown'
                    )

                    del new_positions[symbol]
                    logger.debug(f"Sold {quantity} {symbol} at ${execution_price:.2f}, PnL: ${pnl:.2f}")

            return {
                'new_capital': new_capital,
                'positions': new_positions,
                'trade': trade
            }

        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return None


    def _calculate_portfolio_value(self,
                                 capital: float,
                                 positions: Dict[str, Any],
                                 market_data: Dict[str, pd.DataFrame],
                                 timestamp: datetime) -> float:
        """Calculate total portfolio value"""
        total_value = capital

        for symbol, pos in positions.items():
            if symbol in market_data and not market_data[symbol].empty:
                current_price = market_data[symbol]['close'].iloc[-1]
                position_value = pos['quantity'] * current_price
                total_value += position_value

        return total_value


    def _calculate_results(self,
                          strategy: BaseStrategy,
                          start_date: datetime,
                          end_date: datetime,
                          trades: List[Trade],
                          equity_curve: List[Tuple[datetime, float]],
                          portfolio_values: List[float]) -> BacktestResult:
        """Calculate comprehensive backtest results"""

        # Convert equity curve to pandas Series
        if equity_curve:
            equity_series = pd.Series(
                [val for _, val in equity_curve],
                index=[ts for ts, _ in equity_curve]
            )
        else:
            equity_series = pd.Series([self.initial_capital])

        # Basic metrics
        final_capital = equity_series.iloc[-1] if not equity_series.empty else self.initial_capital
        total_return = final_capital - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100

        # Trade statistics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        wins = [t.pnl for t in trades if t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl < 0]

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0

        profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf')

        # Risk metrics
        returns = equity_series.pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility

        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() != 0 else 0

        # Drawdown calculation
        rolling_max = equity_series.expanding().max()
        drawdown = equity_series - rolling_max
        max_drawdown = drawdown.min()
        max_drawdown_pct = (max_drawdown / rolling_max[drawdown.idxmin()]) * 100 if not rolling_max.empty else 0

        # Position statistics
        max_positions = 1  # Simplified for now
        avg_position_size = np.mean([abs(t.quantity * t.entry_price) for t in trades]) if trades else 0

        return BacktestResult(
            strategy_name=strategy.name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            max_positions=max_positions,
            avg_position_size=avg_position_size,
            trades=trades,
            equity_curve=equity_series,
            drawdown_curve=drawdown
        )

