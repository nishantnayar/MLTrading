"""
Strategy Manager
Manages multiple trading strategies, executes signals, and coordinates with broker
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
import threading
import time
from dataclasses import dataclass

from .base_strategy import BaseStrategy, StrategySignal, StrategyState
from ..brokers.alpaca_service import AlpacaService
from ...utils.logging_config import get_combined_logger, log_operation
from ...utils.database_logging import get_trading_logger, get_performance_logger

logger = get_combined_logger("mltrading.strategy_manager")
trading_logger = get_trading_logger()
performance_logger = get_performance_logger()


@dataclass


class StrategyConfig:
    """Configuration for a strategy"""
    strategy_class: type
    symbols: List[str]
    parameters: Dict[str, Any]
    risk_params: Dict[str, Any]
    enabled: bool = True
    max_positions: int = 5


class StrategyManager:
    """
    Manages multiple trading strategies

    Responsibilities:
    - Strategy lifecycle management
    - Signal processing and order execution
    - Risk management coordination
    - Performance monitoring
    """


    def __init__(self,
                 broker_service: AlpacaService = None,
                 max_total_positions: int = 10,
                 max_daily_orders: int = 20):
        """
        Initialize strategy manager

        Args:
            broker_service: Broker service for order execution
            max_total_positions: Maximum total positions across all strategies
            max_daily_orders: Maximum orders per day
        """
        self.broker_service = broker_service
        self.max_total_positions = max_total_positions
        self.max_daily_orders = max_daily_orders

        # Strategy management
        self.strategies: Dict[str, BaseStrategy] = {}
        self.strategy_configs: Dict[str, StrategyConfig] = {}

        # Execution state
        self.is_running = False
        self.execution_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Performance tracking
        self.daily_orders_count = 0
        self.total_positions = 0
        self.last_reset_date = datetime.now(timezone.utc).date()

        # Callbacks
        self.order_callbacks: List[Callable] = []
        self.signal_callbacks: List[Callable] = []

        logger.info("Strategy Manager initialized")


    def add_strategy(self,
                    strategy_name: str,
                    strategy_config: StrategyConfig) -> bool:
        """
        Add a strategy to the manager

        Args:
            strategy_name: Unique name for the strategy
            strategy_config: Strategy configuration

        Returns:
            True if strategy was added successfully
        """
        try:
            if strategy_name in self.strategies:
                logger.warning(f"Strategy {strategy_name} already exists")
                return False

            # Create strategy instance
            # Remove symbols from parameters to avoid duplicate
            params = dict(strategy_config.parameters)
            params['risk_params'] = strategy_config.risk_params

            strategy = strategy_config.strategy_class(**params)

            # Initialize strategy
            strategy.initialize()

            # Store strategy and config
            self.strategies[strategy_name] = strategy
            self.strategy_configs[strategy_name] = strategy_config

            logger.info(f"Added strategy '{strategy_name}' with {len(strategy_config.symbols)} symbols")

            # Log to database
            trading_logger.log_trading_event(
                event_type="strategy_added",
                strategy=strategy_name,
                symbols=",".join(strategy_config.symbols),
                parameters=strategy_config.parameters
            )

            return True

        except Exception as e:
            logger.error(f"Failed to add strategy {strategy_name}: {e}")
            return False


    def remove_strategy(self, strategy_name: str) -> bool:
        """
        Remove a strategy from the manager

        Args:
            strategy_name: Name of strategy to remove

        Returns:
            True if strategy was removed successfully
        """
        try:
            if strategy_name not in self.strategies:
                logger.warning(f"Strategy {strategy_name} not found")
                return False

            strategy = self.strategies[strategy_name]

            # Stop strategy if running
            if strategy.state == StrategyState.RUNNING:
                strategy.stop()

            # Close any open positions
            for symbol in strategy.positions:
                close_signal = strategy.close_position(symbol)
                if close_signal:
                    self._execute_signal(close_signal, strategy_name)

            # Remove from manager
            del self.strategies[strategy_name]
            del self.strategy_configs[strategy_name]

            logger.info(f"Removed strategy '{strategy_name}'")

            trading_logger.log_trading_event(
                event_type="strategy_removed",
                strategy=strategy_name
            )

            return True

        except Exception as e:
            logger.error(f"Failed to remove strategy {strategy_name}: {e}")
            return False


    def start_strategy(self, strategy_name: str) -> bool:
        """Start a specific strategy"""
        try:
            if strategy_name not in self.strategies:
                logger.error(f"Strategy {strategy_name} not found")
                return False

            strategy = self.strategies[strategy_name]
            if strategy.state != StrategyState.INITIALIZED:
                logger.error(f"Strategy {strategy_name} must be initialized first")
                return False

            strategy.start()
            logger.info(f"Started strategy '{strategy_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to start strategy {strategy_name}: {e}")
            return False


    def stop_strategy(self, strategy_name: str) -> bool:
        """Stop a specific strategy"""
        try:
            if strategy_name not in self.strategies:
                logger.error(f"Strategy {strategy_name} not found")
                return False

            strategy = self.strategies[strategy_name]
            strategy.stop()
            logger.info(f"Stopped strategy '{strategy_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to stop strategy {strategy_name}: {e}")
            return False


    def start_all_strategies(self):
        """Start all enabled strategies"""
        for strategy_name, config in self.strategy_configs.items():
            if config.enabled:
                self.start_strategy(strategy_name)


    def stop_all_strategies(self):
        """Stop all running strategies"""
        for strategy_name in self.strategies:
            self.stop_strategy(strategy_name)


    def start_execution(self):
        """Start the strategy execution loop"""
        if self.is_running:
            logger.warning("Strategy manager already running")
            return

        self.is_running = True
        self.stop_event.clear()

        # Start execution thread
        self.execution_thread = threading.Thread(target=self._execution_loop, daemon=True)
        self.execution_thread.start()

        logger.info("Strategy execution started")

        trading_logger.log_trading_event(
            event_type="strategy_manager_started",
            strategy="ALL",
            active_strategies=list(self.strategies.keys())
        )


    def stop_execution(self):
        """Stop the strategy execution loop"""
        if not self.is_running:
            logger.warning("Strategy manager not running")
            return

        self.is_running = False
        self.stop_event.set()

        # Wait for execution thread to finish
        if self.execution_thread and self.execution_thread.is_alive():
            self.execution_thread.join(timeout=10)

        # Stop all strategies
        self.stop_all_strategies()

        logger.info("Strategy execution stopped")

        trading_logger.log_trading_event(
            event_type="strategy_manager_stopped",
            strategy="ALL"
        )


    def _execution_loop(self):
        """Main execution loop for strategy manager"""
        logger.info("Strategy execution loop started")

        while self.is_running and not self.stop_event.is_set():
            try:
                # Reset daily counters if needed
                self._reset_daily_counters()

                # Get market data for all symbols
                market_data = self._get_market_data()

                # Process each strategy
                for strategy_name, strategy in self.strategies.items():
                    if strategy.state != StrategyState.RUNNING:
                        continue

                    config = self.strategy_configs[strategy_name]
                    if not config.enabled:
                        continue

                    try:
                        # Generate signals
                        signals = strategy.generate_signals(market_data)

                        # Process each signal
                        for signal in signals:
                            self._process_signal(signal, strategy_name)

                    except Exception as e:
                        logger.error(f"Error processing strategy {strategy_name}: {e}")
                        strategy.state = StrategyState.ERROR

                # Sleep before next iteration
                time.sleep(30)  # Check every 30 seconds (configurable)

            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                time.sleep(60)  # Longer sleep on error

        logger.info("Strategy execution loop ended")


    def _get_market_data(self) -> Dict[str, Any]:
        """
        Get market data for all symbols used by strategies

        Returns:
            Dictionary of symbol -> market data
        """
        # Collect all symbols from all strategies
        all_symbols = set()
        for config in self.strategy_configs.values():
            all_symbols.update(config.symbols)

        market_data = {}

        # For now, return empty dict - in real implementation,
        # this would fetch live market data from your data service
        # or use the existing data extraction system

        # TODO: Integrate with your existing data collection system
        # This could use the Yahoo collector or Alpaca market data

        return market_data


    def _process_signal(self, signal: StrategySignal, strategy_name: str):
        """
        Process a trading signal

        Args:
            signal: Trading signal to process
            strategy_name: Name of strategy that generated the signal
        """
        try:
            # Check global risk limits
            if not self._check_global_risk_limits():
                logger.warning("Global risk limits exceeded, skipping signal")
                return

            strategy = self.strategies[strategy_name]

            # Get available capital (placeholder - integrate with account info)
            available_capital = 10000.0  # TODO: Get from broker service

            # Process signal through strategy
            order_instructions = strategy.process_signal(signal, available_capital)

            if order_instructions:
                self._execute_signal(signal, strategy_name, order_instructions)

                # Notify callbacks
                for callback in self.signal_callbacks:
                    try:
                        callback(signal, strategy_name, order_instructions)
                    except Exception as e:
                        logger.error(f"Error in signal callback: {e}")

        except Exception as e:
            logger.error(f"Error processing signal from {strategy_name}: {e}")


    def _execute_signal(self,
                       signal: StrategySignal,
                       strategy_name: str,
                       order_instructions: Dict[str, Any] = None):
        """
        Execute a trading signal by placing orders

        Args:
            signal: Trading signal
            strategy_name: Strategy name
            order_instructions: Order instructions from strategy
        """
        try:
            if not self.broker_service or not self.broker_service.is_connected():
                logger.warning("Broker service not available, cannot execute signal")
                return

            # TODO: Implement order placement through broker service
            # This would integrate with your Alpaca service

            logger.info(f"Would execute {signal.signal_type.value} order for {signal.symbol} "
                       f"from strategy {strategy_name}")

            # Log the signal execution
            trading_logger.log_trading_event(
                event_type="signal_executed",
                symbol=signal.symbol,
                side=signal.signal_type.value,
                strategy=strategy_name,
                signal_strength=signal.strength,
                order_instructions=order_instructions
            )

            # Update counters
            self.daily_orders_count += 1

            # Notify callbacks
            for callback in self.order_callbacks:
                try:
                    callback(signal, strategy_name, order_instructions)
                except Exception as e:
                    logger.error(f"Error in order callback: {e}")

        except Exception as e:
            logger.error(f"Error executing signal: {e}")


    def _check_global_risk_limits(self) -> bool:
        """Check global risk management limits"""
        # Check daily order limit
        if self.daily_orders_count >= self.max_daily_orders:
            logger.warning(f"Daily order limit reached: {self.daily_orders_count}")
            return False

        # Check total positions limit
        total_positions = sum(len(strategy.positions) for strategy in self.strategies.values())
        if total_positions >= self.max_total_positions:
            logger.warning(f"Total position limit reached: {total_positions}")
            return False

        return True


    def _reset_daily_counters(self):
        """Reset daily counters if new day"""
        current_date = datetime.now(timezone.utc).date()
        if current_date > self.last_reset_date:
            self.daily_orders_count = 0
            self.last_reset_date = current_date
            logger.info("Reset daily counters for new trading day")


    def add_order_callback(self, callback: Callable):
        """Add callback for order events"""
        self.order_callbacks.append(callback)


    def add_signal_callback(self, callback: Callable):
        """Add callback for signal events"""
        self.signal_callbacks.append(callback)


    def get_status(self) -> Dict[str, Any]:
        """Get current manager status"""
        strategy_statuses = {}
        for name, strategy in self.strategies.items():
            strategy_statuses[name] = strategy.get_status()

        return {
            'is_running': self.is_running,
            'total_strategies': len(self.strategies),
            'active_strategies': len([s for s in self.strategies.values()
                                    if s.state == StrategyState.RUNNING]),
            'daily_orders': self.daily_orders_count,
            'total_positions': sum(len(s.positions) for s in self.strategies.values()),
            'strategies': strategy_statuses
        }


    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all strategies"""
        total_pnl = 0.0
        total_trades = 0

        strategy_performance = {}
        for name, strategy in self.strategies.items():
            perf = strategy._get_performance_summary()
            strategy_performance[name] = perf
            total_pnl += perf.get('total_pnl', 0.0)
            total_trades += perf.get('total_trades', 0)

        return {
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'strategy_performance': strategy_performance
        }

