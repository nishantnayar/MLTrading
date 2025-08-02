"""
Example script demonstrating how to use the data extraction APIs.
This shows how the APIs can be reused across different parts of the application.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.services.data_service import get_data_service


def example_market_data_usage():
    """Example of using market data APIs."""
    print("=== Market Data Usage Example ===")
    
    # Initialize data service
    data_service = get_data_service()
    
    # Check API health
    if not data_service.health_check():
        print("❌ API is not healthy. Make sure the FastAPI server is running.")
        return
    
    print("✅ API is healthy")
    
    # Get available symbols
    symbols = data_service.get_symbols()
    print(f"📊 Available symbols: {len(symbols)}")
    if symbols:
        print(f"   Sample symbols: {symbols[:5]}")
    
    # Get market data for a symbol
    if symbols:
        symbol = symbols[0]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"\n📈 Getting market data for {symbol}")
        df = data_service.get_market_data(symbol, start_date, end_date)
        
        if not df.empty:
            print(f"   Retrieved {len(df)} data points")
            print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"   Latest close: ${df['close'].iloc[-1]:.2f}")
        else:
            print("   No data found")
    
    # Get latest market data
    if symbols:
        symbol = symbols[0]
        latest_data = data_service.get_latest_market_data(symbol)
        if latest_data:
            print(f"\n🕒 Latest data for {symbol}:")
            print(f"   Close: ${latest_data['close']:.2f}")
            print(f"   Volume: {latest_data['volume']:,}")
            print(f"   Date: {latest_data['timestamp']}")


def example_stock_info_usage():
    """Example of using stock information APIs."""
    print("\n=== Stock Information Usage Example ===")
    
    data_service = get_data_service()
    
    # Get sectors
    sectors = data_service.get_sectors()
    print(f"🏭 Available sectors: {len(sectors)}")
    if sectors:
        print(f"   Sample sectors: {sectors[:5]}")
    
    # Get industries
    industries = data_service.get_industries()
    print(f"🏢 Available industries: {len(industries)}")
    if industries:
        print(f"   Sample industries: {industries[:5]}")
    
    # Get stocks by sector
    if sectors:
        sector = sectors[0]
        stocks = data_service.get_stocks_by_sector(sector)
        print(f"\n📋 Stocks in {sector}: {len(stocks)}")
        if stocks:
            print(f"   Sample stocks: {stocks[:5]}")
    
    # Get stock info for a specific symbol
    symbols = data_service.get_symbols()
    if symbols:
        symbol = symbols[0]
        stock_info = data_service.get_stock_info(symbol)
        if stock_info:
            print(f"\nℹ️  Stock info for {symbol}:")
            print(f"   Company: {stock_info.get('company_name', 'N/A')}")
            print(f"   Sector: {stock_info.get('sector', 'N/A')}")
            print(f"   Industry: {stock_info.get('industry', 'N/A')}")
            if stock_info.get('market_cap'):
                print(f"   Market Cap: ${stock_info['market_cap']:,.0f}")


def example_data_summary_usage():
    """Example of using data summary APIs."""
    print("\n=== Data Summary Usage Example ===")
    
    data_service = get_data_service()
    
    # Get data summary
    summary = data_service.get_data_summary()
    
    print(f"📊 Data Summary:")
    print(f"   Total symbols: {summary.get('total_symbols', 0)}")
    print(f"   Total sectors: {summary.get('total_sectors', 0)}")
    print(f"   Total industries: {summary.get('total_industries', 0)}")
    
    if summary.get('sectors'):
        print(f"   Sample sectors: {summary['sectors'][:5]}")
    
    if summary.get('sample_symbols'):
        print(f"   Sample symbols: {summary['sample_symbols'][:5]}")


def example_date_range_usage():
    """Example of using date range APIs."""
    print("\n=== Date Range Usage Example ===")
    
    data_service = get_data_service()
    
    symbols = data_service.get_symbols()
    if symbols:
        symbol = symbols[0]
        date_range = data_service.get_date_range(symbol)
        
        print(f"📅 Date range for {symbol}:")
        print(f"   Has data: {date_range.get('has_data', False)}")
        if date_range.get('start_date'):
            print(f"   Start date: {date_range['start_date']}")
        if date_range.get('end_date'):
            print(f"   End date: {date_range['end_date']}")


def example_dashboard_integration():
    """Example of how the data service can be used in a dashboard."""
    print("\n=== Dashboard Integration Example ===")
    
    data_service = get_data_service()
    
    # Simulate dashboard data requirements
    print("🎛️  Dashboard Data Requirements:")
    
    # 1. Get symbols for dropdown
    symbols = data_service.get_symbols()
    print(f"   1. Symbol dropdown: {len(symbols)} symbols available")
    
    # 2. Get sectors for filtering
    sectors = data_service.get_sectors()
    print(f"   2. Sector filter: {len(sectors)} sectors available")
    
    # 3. Get market data for chart
    if symbols:
        symbol = symbols[0]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        df = data_service.get_market_data(symbol, start_date, end_date)
        print(f"   3. Chart data: {len(df)} data points for {symbol}")
        
        if not df.empty:
            # Calculate some basic statistics for dashboard
            latest_close = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-2] if len(df) > 1 else latest_close
            change = latest_close - prev_close
            change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
            
            print(f"      Latest close: ${latest_close:.2f}")
            print(f"      Change: ${change:+.2f} ({change_pct:+.2f}%)")
    
    # 4. Get latest data for real-time updates
    if symbols:
        symbol = symbols[0]
        latest = data_service.get_latest_market_data(symbol)
        if latest:
            print(f"   4. Real-time data: {symbol} at ${latest['close']:.2f}")


def main():
    """Run all examples."""
    print("🚀 ML Trading Data API Usage Examples")
    print("=" * 50)
    
    try:
        example_market_data_usage()
        example_stock_info_usage()
        example_data_summary_usage()
        example_date_range_usage()
        example_dashboard_integration()
        
        print("\n✅ All examples completed successfully!")
        print("\n💡 These APIs can now be used across your application:")
        print("   - Dashboard components")
        print("   - Trading strategies")
        print("   - Data analysis scripts")
        print("   - External integrations")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Make sure the FastAPI server is running on http://localhost:8000")


if __name__ == "__main__":
    main() 