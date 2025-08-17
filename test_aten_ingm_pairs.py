#!/usr/bin/env python3
"""
ATEN-INGM Pairs Trading Test
Test the custom pairs trading strategy with ATEN and INGM pair
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.trading.strategies.custom_pairs_trading import CustomPairsTradingStrategy, create_sample_pairs_strategy
from src.trading.strategies.strategy_manager import StrategyManager, StrategyConfig
from src.utils.logging_config import get_combined_logger

logger = get_combined_logger("test.aten_ingm_pairs")

def create_aten_ingm_strategy():
    """
    Create pairs trading strategy specifically for ATEN and INGM
    """
    print("Creating ATEN-INGM pairs trading strategy...")
    
    # Configure ATEN-INGM pair
    pairs_config = [
        {
            'symbol_a': 'ATEN',
            'symbol_b': 'INGM',
            'hedge_ratio': 1.0,  # Start with 1:1 ratio - can be optimized
            'entry_threshold': 2.0,  # Enter when spread is 2 std devs away
            'exit_threshold': 0.5,   # Exit when spread returns to 0.5 std devs
            'stop_loss_threshold': 3.0,  # Stop loss at 3 std devs
            'lookback_period': 20    # Use 20 days for spread calculation
        }
    ]
    
    # Create strategy with specific risk parameters
    strategy = CustomPairsTradingStrategy(
        pairs_config=pairs_config,
        position_size_usd=10000,  # $10k per pair trade
        risk_params={
            'max_position_size': 500,
            'risk_per_trade': 0.03,  # 3% risk per trade
            'stop_loss_pct': 0.05,   # 5% stop loss
            'take_profit_pct': 0.10  # 10% take profit
        }
    )
    
    print(f"Strategy created: {strategy.name}")
    print(f"Trading pairs: {[pair.pair_name for pair in strategy.trading_pairs]}")
    print(f"Position size: ${strategy.position_size_usd:,}")
    
    return strategy

def create_sample_market_data():
    """
    Create sample market data for ATEN and INGM for testing
    """
    print("Creating sample market data for ATEN and INGM...")
    
    # Generate 60 days of sample data
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=60),
        end=datetime.now(),
        freq='D'
    )
    
    np.random.seed(42)  # For reproducible results
    
    # Create correlated price movements
    # Start with base prices
    aten_base = 25.0
    ingm_base = 30.0
    
    # Generate correlated returns
    correlation = 0.75
    returns_independent = np.random.normal(0, 0.02, len(dates))
    aten_specific = np.random.normal(0, 0.015, len(dates))
    
    # Create correlated returns
    aten_returns = correlation * returns_independent + np.sqrt(1 - correlation**2) * aten_specific
    ingm_returns = correlation * returns_independent + np.sqrt(1 - correlation**2) * np.random.normal(0, 0.015, len(dates))
    
    # Add some mean reversion in the spread
    spread_target = 5.0  # Target spread
    current_spread = ingm_base - aten_base
    
    # Calculate prices
    aten_prices = [aten_base]
    ingm_prices = [ingm_base]
    
    for i in range(1, len(dates)):
        # Apply returns
        aten_price = aten_prices[-1] * (1 + aten_returns[i])
        ingm_price = ingm_prices[-1] * (1 + ingm_returns[i])
        
        # Add mean reversion component to spread
        current_spread = ingm_price - aten_price
        spread_deviation = current_spread - spread_target
        
        # Adjust prices to create mean reversion
        mean_reversion_strength = 0.1
        adjustment = spread_deviation * mean_reversion_strength
        
        aten_price += adjustment * 0.5
        ingm_price -= adjustment * 0.5
        
        aten_prices.append(max(aten_price, 1.0))  # Ensure positive prices
        ingm_prices.append(max(ingm_price, 1.0))
    
    # Create OHLCV data
    def create_ohlcv(prices, symbol):
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            # Simple OHLC generation around close price
            high = close * (1 + abs(np.random.normal(0, 0.01)))
            low = close * (1 - abs(np.random.normal(0, 0.01)))
            open_price = close + np.random.normal(0, 0.005) * close
            volume = int(np.random.normal(100000, 20000))
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': max(volume, 1000)
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    market_data = {
        'ATEN': create_ohlcv(aten_prices, 'ATEN'),
        'INGM': create_ohlcv(ingm_prices, 'INGM')
    }
    
    print(f"Generated {len(dates)} days of data")
    print(f"ATEN price range: ${min(aten_prices):.2f} - ${max(aten_prices):.2f}")
    print(f"INGM price range: ${min(ingm_prices):.2f} - ${max(ingm_prices):.2f}")
    print(f"Final spread: ${ingm_prices[-1] - aten_prices[-1]:.2f}")
    
    return market_data

def test_signal_generation(strategy, market_data):
    """Test signal generation for the pairs strategy"""
    print("\n=== Testing Signal Generation ===")
    
    # Initialize and start strategy
    strategy.initialize()
    strategy.start()
    
    # Generate signals
    signals = strategy.generate_signals(market_data)
    
    print(f"Generated {len(signals)} signals:")
    for signal in signals:
        print(f"  {signal.timestamp.strftime('%Y-%m-%d %H:%M'): <16} "
              f"{signal.signal_type.value: <4} {signal.symbol: <6} "
              f"${signal.price:.2f} (strength: {signal.strength:.3f})")
        
        if signal.metadata:
            pair_name = signal.metadata.get('pair_name', '')
            z_score = signal.metadata.get('z_score', 0)
            trade_type = signal.metadata.get('trade_type', '')
            print(f"    {'': <20} Pair: {pair_name}, Z-score: {z_score:.2f}, Type: {trade_type}")
    
    return signals

def test_spread_analysis(strategy, market_data):
    """Analyze the spread characteristics"""
    print("\n=== Spread Analysis ===")
    
    pair = strategy.trading_pairs[0]  # ATEN-INGM pair
    
    # Get price data
    aten_prices = market_data['ATEN']['close']
    ingm_prices = market_data['INGM']['close']
    
    # Calculate spread
    spread = ingm_prices - pair.hedge_ratio * aten_prices
    
    # Calculate spread statistics
    spread_mean = spread.mean()
    spread_std = spread.std()
    current_spread = spread.iloc[-1]
    current_zscore = (current_spread - spread_mean) / spread_std
    
    print(f"Pair: {pair.pair_name}")
    print(f"Hedge ratio: {pair.hedge_ratio}")
    print(f"Spread statistics:")
    print(f"  Mean: ${spread_mean:.3f}")
    print(f"  Std Dev: ${spread_std:.3f}")
    print(f"  Current: ${current_spread:.3f}")
    print(f"  Current Z-score: {current_zscore:.3f}")
    print(f"  Min spread: ${spread.min():.3f}")
    print(f"  Max spread: ${spread.max():.3f}")
    
    # Entry/exit thresholds
    entry_threshold_upper = spread_mean + pair.entry_threshold * spread_std
    entry_threshold_lower = spread_mean - pair.entry_threshold * spread_std
    exit_threshold_upper = spread_mean + pair.exit_threshold * spread_std
    exit_threshold_lower = spread_mean - pair.exit_threshold * spread_std
    
    print(f"\nTrading thresholds:")
    print(f"  Entry upper: ${entry_threshold_upper:.3f} (Z={pair.entry_threshold})")
    print(f"  Entry lower: ${entry_threshold_lower:.3f} (Z={-pair.entry_threshold})")
    print(f"  Exit upper: ${exit_threshold_upper:.3f} (Z={pair.exit_threshold})")
    print(f"  Exit lower: ${exit_threshold_lower:.3f} (Z={-pair.exit_threshold})")
    
    # Trading opportunities in historical data
    opportunities = 0
    for spread_value in spread:
        z_score = (spread_value - spread_mean) / spread_std
        if abs(z_score) >= pair.entry_threshold:
            opportunities += 1
    
    print(f"\nHistorical trading opportunities: {opportunities} out of {len(spread)} days")
    print(f"Opportunity rate: {opportunities/len(spread)*100:.1f}%")

def test_strategy_manager_integration():
    """Test integration with strategy manager"""
    print("\n=== Strategy Manager Integration ===")
    
    # Create strategy configuration
    pairs_config = [
        {
            'symbol_a': 'ATEN',
            'symbol_b': 'INGM',
            'hedge_ratio': 1.0,
            'entry_threshold': 2.0,
            'exit_threshold': 0.5
        }
    ]
    
    config = StrategyConfig(
        strategy_class=CustomPairsTradingStrategy,
        symbols=['ATEN', 'INGM'],
        parameters={
            'pairs_config': pairs_config,
            'position_size_usd': 8000
        },
        risk_params={
            'max_position_size': 300,
            'risk_per_trade': 0.025
        },
        enabled=True,
        max_positions=1
    )
    
    # Create strategy manager
    manager = StrategyManager(
        max_total_positions=3,
        max_daily_orders=10
    )
    
    # Add strategy
    success = manager.add_strategy("ATEN_INGM_Pairs", config)
    print(f"Strategy added to manager: {success}")
    
    # Get status
    status = manager.get_status()
    print(f"Manager status:")
    print(f"  Total strategies: {status['total_strategies']}")
    print(f"  Running strategies: {status['active_strategies']}")
    
    return manager

def customize_pair_selection_example():
    """
    Example of how to customize the pair selection logic
    """
    print("\n=== Custom Pair Selection Example ===")
    
    # This shows how you can override the pair selection method
    class MyCustomPairsStrategy(CustomPairsTradingStrategy):
        
        def implement_custom_pair_selection(self, market_data):
            """
            MY CUSTOM PAIR SELECTION LOGIC
            """
            active_pairs = []
            
            for pair in self.trading_pairs:
                # Your custom logic here
                should_trade = True
                
                # Example 1: Only trade during high volatility periods
                if pair.symbol_a in market_data and pair.symbol_b in market_data:
                    recent_vol_a = market_data[pair.symbol_a]['close'].tail(5).pct_change().std()
                    recent_vol_b = market_data[pair.symbol_b]['close'].tail(5).pct_change().std()
                    
                    # Only trade if both stocks have reasonable volatility
                    if recent_vol_a < 0.01 or recent_vol_b < 0.01:  # Too low volatility
                        should_trade = False
                        self.logger.info(f"Skipping {pair.pair_name} - low volatility")
                    
                    if recent_vol_a > 0.08 or recent_vol_b > 0.08:  # Too high volatility
                        should_trade = False
                        self.logger.info(f"Skipping {pair.pair_name} - high volatility")
                
                # Example 2: Add time-based filters
                current_hour = datetime.now().hour
                if current_hour < 10 or current_hour > 15:  # Only trade during market hours
                    should_trade = False
                
                # Example 3: Add fundamental filters (placeholder)
                # You could add P/E ratio comparisons, earnings dates, etc.
                
                if should_trade:
                    active_pairs.append(pair)
                    self.logger.info(f"Selected {pair.pair_name} for trading")
            
            return active_pairs
    
    print("You can customize pair selection by overriding the")
    print("'implement_custom_pair_selection' method in the strategy class.")
    print("See the example above for ideas on custom logic to implement.")

def main():
    """Main test function"""
    print("ATEN-INGM Pairs Trading Strategy Test")
    print("=" * 50)
    
    try:
        # Create strategy
        strategy = create_aten_ingm_strategy()
        
        # Create sample market data
        market_data = create_sample_market_data()
        
        # Test spread analysis
        test_spread_analysis(strategy, market_data)
        
        # Test signal generation
        signals = test_signal_generation(strategy, market_data)
        
        # Test strategy manager integration
        manager = test_strategy_manager_integration()
        
        # Show customization example
        customize_pair_selection_example()
        
        # Get strategy status
        print("\n=== Strategy Status ===")
        status = strategy.get_custom_pairs_status()
        print(f"Configured pairs: {status['configured_pairs']}")
        print(f"Active trades: {status['active_trades']}")
        print(f"Position size: ${status['position_size_usd']:,}")
        
        print("\n" + "=" * 50)
        print("SUCCESS: ATEN-INGM Pairs Trading Test Complete!")
        print("\nNext steps:")
        print("1. Customize the pair selection logic in implement_custom_pair_selection()")
        print("2. Adjust hedge ratios and thresholds based on your analysis")
        print("3. Integrate with real market data from your data collection system")
        print("4. Add the strategy to your main strategy manager")
        print("5. Monitor performance and optimize parameters")
        
    except Exception as e:
        print(f"Test failed: {e}")
        logger.error(f"ATEN-INGM pairs test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()