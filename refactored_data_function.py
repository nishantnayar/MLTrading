"""
Refactored version of get_all_stock_data_and_info() using the new modular service architecture.
This demonstrates how to leverage the specialized services for better performance and maintainability.
"""

import pandas as pd
from src.data.storage.database import get_db_manager
from src.dashboard.services.symbol_service import SymbolService
from src.dashboard.services.market_data_service import MarketDataService


def get_all_stock_data_and_info_refactored():
    """
    Get all stock data and stock info in DataFrames using the new modular service architecture.
    
    Returns:
        dict: {
            'market_data': pd.DataFrame,
            'stock_info': pd.DataFrame, 
            'symbols': List[str],
            'success': bool,
            'message': str
        }
    """
    try:
        # Initialize services using the new modular architecture
        symbol_service = SymbolService()
        market_data_service = MarketDataService()
        
        # Get all available symbols with company names
        symbols_data = symbol_service.get_available_symbols()
        symbols = [item['symbol'] for item in symbols_data]
        
        if not symbols:
            return {
                'market_data': pd.DataFrame(),
                'stock_info': pd.DataFrame(), 
                'symbols': [],
                'success': False,
                'message': 'No symbols found with market data'
            }
        
        print(f"Found {len(symbols)} symbols with data")
        
        # Get stock info using batch processing for better performance
        stock_info_list = []
        failed_symbols = []
        
        for symbol in symbols:
            stock_info = symbol_service.get_symbol_info(symbol)
            if stock_info:
                stock_info_list.append(stock_info)
            else:
                failed_symbols.append(symbol)
        
        # Create stock info DataFrame
        stock_info_df = pd.DataFrame(stock_info_list) if stock_info_list else pd.DataFrame()
        
        if failed_symbols:
            print(f"Failed to get stock info for {len(failed_symbols)} symbols: {failed_symbols[:5]}...")
        
        if not stock_info_df.empty:
            print(f"Retrieved stock info for {len(stock_info_df)} symbols")
        
        # Get market data for all symbols with improved error handling
        all_market_data = []
        market_data_errors = []
        
        for symbol in symbols:
            try:
                # Use the new market data service with proper error handling
                df = market_data_service.get_market_data(symbol, days=30)  # Reduced days for efficiency
                
                # Check if df is a DataFrame and not empty
                if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                    # Add symbol column if not present
                    if 'symbol' not in df.columns:
                        df['symbol'] = symbol
                    all_market_data.append(df)
                else:
                    market_data_errors.append(symbol)
                    
            except Exception as e:
                print(f"Error getting market data for {symbol}: {e}")
                market_data_errors.append(symbol)
        
        # Combine all market data with proper error handling
        if all_market_data:
            try:
                stock_data_df = pd.concat(all_market_data, ignore_index=True)
                print(f"Combined market data: {len(stock_data_df)} total records from {len(all_market_data)} symbols")
            except Exception as e:
                print(f"Error combining market data: {e}")
                stock_data_df = pd.DataFrame()
        else:
            stock_data_df = pd.DataFrame()
            print("No market data retrieved")
        
        if market_data_errors:
            print(f"Failed to get market data for {len(market_data_errors)} symbols")
        
        success = not stock_data_df.empty or not stock_info_df.empty
        message = f"Retrieved data for {len(symbols)} symbols" if success else "No data retrieved"
        
        return {
            'market_data': stock_data_df,
            'stock_info': stock_info_df,
            'symbols': symbols,
            'success': success,
            'message': message,
            'stats': {
                'total_symbols': len(symbols),
                'market_data_records': len(stock_data_df),
                'stock_info_records': len(stock_info_df),
                'market_data_errors': len(market_data_errors),
                'stock_info_errors': len(failed_symbols)
            }
        }
        
    except Exception as e:
        print(f"Error in get_all_stock_data_and_info_refactored: {e}")
        return {
            'market_data': pd.DataFrame(),
            'stock_info': pd.DataFrame(),
            'symbols': [],
            'success': False,
            'message': f"Function failed with error: {str(e)}",
            'stats': {
                'total_symbols': 0,
                'market_data_records': 0,
                'stock_info_records': 0,
                'market_data_errors': 0,
                'stock_info_errors': 0
            }
        }


def get_all_stock_data_and_info_streaming():
    """
    Alternative implementation using generator pattern for memory efficiency with large datasets.
    
    Yields:
        dict: Incremental data updates for real-time processing
    """
    try:
        symbol_service = SymbolService()
        market_data_service = MarketDataService()
        
        # Get all symbols
        symbols_data = symbol_service.get_available_symbols()
        symbols = [item['symbol'] for item in symbols_data]
        
        yield {'type': 'symbols', 'data': symbols, 'count': len(symbols)}
        
        # Process symbols in batches for memory efficiency
        batch_size = 50
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            
            # Get stock info for batch
            stock_info_batch = []
            for symbol in batch_symbols:
                stock_info = symbol_service.get_symbol_info(symbol)
                if stock_info:
                    stock_info_batch.append(stock_info)
            
            yield {
                'type': 'stock_info_batch',
                'data': pd.DataFrame(stock_info_batch),
                'batch_number': i // batch_size + 1,
                'symbols_processed': min(i + batch_size, len(symbols))
            }
            
            # Get market data for batch
            market_data_batch = []
            for symbol in batch_symbols:
                try:
                    df = market_data_service.get_market_data(symbol, days=30)
                    if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                        if 'symbol' not in df.columns:
                            df['symbol'] = symbol
                        market_data_batch.append(df)
                except Exception as e:
                    print(f"Error getting market data for {symbol}: {e}")
            
            if market_data_batch:
                combined_batch = pd.concat(market_data_batch, ignore_index=True)
                yield {
                    'type': 'market_data_batch',
                    'data': combined_batch,
                    'batch_number': i // batch_size + 1,
                    'symbols_processed': min(i + batch_size, len(symbols))
                }
        
        yield {'type': 'complete', 'message': 'All data processed successfully'}
        
    except Exception as e:
        yield {'type': 'error', 'message': str(e)}


def get_all_stock_data_and_info():
    """
    Backward compatibility wrapper that returns the old tuple format.
    
    Returns:
        tuple: (stock_data_df, stock_info_df, symbols_list)
    """
    result = get_all_stock_data_and_info_refactored()
    return result['market_data'], result['stock_info'], result['symbols']


# Example usage:
if __name__ == "__main__":
    # Standard refactored version
    result = get_all_stock_data_and_info_refactored()
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Stats: {result['stats']}")
    
    # Streaming version for large datasets
    print("\nStreaming version:")
    for update in get_all_stock_data_and_info_streaming():
        print(f"Update: {update['type']} - {update.get('message', 'Data processed')}")