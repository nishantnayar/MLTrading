"""
Backtesting Package
Contains backtesting engine and utilities for testing trading strategies
"""

from .backtest_engine import BacktestEngine, BacktestResult

__all__ = ['BacktestEngine', 'BacktestResult']