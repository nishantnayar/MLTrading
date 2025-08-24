"""
Yahoo Finance Market Hours Data Collection Workflow
Collects market data every hour during trading hours on weekdays
"""

import os
import sys
from datetime import datetime, time
from pathlib import Path
from typing import List, Dict, Any
import pytz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from prefect import flow, task
from prefect.task_runners import ConcurrentTaskRunner
from prefect.logging import get_run_logger
from prefect.runtime import flow_run

from src.data.collectors.yahoo_collector import fetch_yahoo_data, prepare_data_for_insert
from src.utils.logging_config import get_combined_logger
from src.data.storage.database import get_db_manager
from src.workflows.data_pipeline.feature_engineering_flow import feature_engineering_flow

# Market hours configuration
MARKET_TIMEZONE = pytz.timezone('America/New_York')
MARKET_OPEN = time(9, 30)  # 9:30 AM EST
MARKET_CLOSE = time(16, 0)  # 4:00 PM EST

def generate_flow_run_name() -> str:
    """
    Generate a user-friendly name for the flow run
    
    Returns:
        Formatted run name with timestamp and context
    """
    now = datetime.now(MARKET_TIMEZONE)
    
    # Determine market status
    current_time = now.time()
    is_weekday = now.weekday() < 5
    is_market_hours = MARKET_OPEN <= current_time <= MARKET_CLOSE
    market_open = is_weekday and is_market_hours
    
    # Create descriptive name
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")  # Remove colon and spaces
    
    if market_open:
        status = "market-open"
    elif is_weekday:
        if current_time < MARKET_OPEN:
            status = "pre-market"
        else:
            status = "after-market"
    else:
        status = "weekend"
    
    return f"yahoo-data-{date_str}-{time_str}EST-{status}"

@task(retries=3, retry_delay_seconds=60)
def check_market_hours() -> bool:
    """
    Check if current time is during market hours
    
    Returns:
        bool: True if market is open, False otherwise
    """
    logger = get_run_logger()
    
    now = datetime.now(MARKET_TIMEZONE)
    current_time = now.time()
    
    # Check if it's a weekday (0=Monday, 6=Sunday)
    is_weekday = now.weekday() < 5
    
    # Check if within market hours
    is_market_hours = MARKET_OPEN <= current_time <= MARKET_CLOSE
    
    market_open = is_weekday and is_market_hours
    
    logger.info(f"Market status check: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"Weekday: {is_weekday}, Market hours: {is_market_hours}, Market open: {market_open}")
    
    return market_open

@task(retries=2, retry_delay_seconds=30)
def get_active_symbols() -> List[str]:
    """
    Get list of active symbols from database
    
    Returns:
        List of stock symbols to collect data for
    """
    logger = get_run_logger()
    
    try:
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get active symbols from stock_info table
                cursor.execute("""
                    SELECT DISTINCT symbol 
                    FROM stock_info 
                    WHERE market_cap > 1000000000  -- Only large cap stocks
                    ORDER BY symbol
                    LIMIT 100  -- Limit to avoid rate limiting
                """)
                
                symbols = [row[0] for row in cursor.fetchall()]
                
        logger.info(f"Retrieved {len(symbols)} symbols for data collection")
        return symbols
        
    except Exception as e:
        logger.error(f"Failed to get active symbols: {e}")
        # Fallback to a small set of major symbols
        fallback_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 
            'META', 'NVDA', 'NFLX', 'AMD', 'INTC'
        ]
        logger.info(f"Using fallback symbols: {fallback_symbols}")
        return fallback_symbols

@task(retries=3, retry_delay_seconds=120)
def collect_symbol_data(symbol: str, period: str = "1d") -> Dict[str, Any]:
    """
    Collect data for a single symbol
    
    Args:
        symbol: Stock symbol to collect
        period: Time period for data collection
        
    Returns:
        Dictionary with collection results
    """
    logger = get_run_logger()
    
    try:
        # Fetch data from Yahoo Finance
        logger.info(f"Collecting data for {symbol}")
        df = fetch_yahoo_data(symbol=symbol, period=period, interval='1h')
        
        if df.empty:
            return {
                'symbol': symbol,
                'status': 'error',
                'records_collected': 0,
                'message': f"No data available for {symbol}"
            }
        
        # Prepare data for database insertion
        records = prepare_data_for_insert(df)
        
        # Insert into database
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                for record in records:
                    cursor.execute("""
                        INSERT INTO market_data 
                        (symbol, timestamp, open, high, low, close, volume, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timestamp, source) DO UPDATE SET
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume
                    """, (
                        record['symbol'],
                        record['timestamp'],
                        record['open'],
                        record['high'],
                        record['low'],
                        record['close'],
                        record['volume'],
                        record['source']
                    ))
                conn.commit()
        
        return {
            'symbol': symbol,
            'status': 'success',
            'records_collected': len(records),
            'message': f"Successfully collected {len(records)} records for {symbol}"
        }
        
    except Exception as e:
        logger.error(f"Failed to collect data for {symbol}: {e}")
        return {
            'symbol': symbol,
            'status': 'error',
            'records_collected': 0,
            'message': str(e)
        }

@task
def generate_collection_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary of data collection results
    
    Args:
        results: List of collection results from individual symbols
        
    Returns:
        Summary statistics
    """
    logger = get_run_logger()
    
    total_symbols = len(results)
    successful_collections = len([r for r in results if r['status'] == 'success'])
    failed_collections = total_symbols - successful_collections
    total_records = sum(r['records_collected'] for r in results)
    
    summary = {
        'timestamp': datetime.now(MARKET_TIMEZONE).isoformat(),
        'total_symbols': total_symbols,
        'successful_collections': successful_collections,
        'failed_collections': failed_collections,
        'total_records_collected': total_records,
        'success_rate': (successful_collections / total_symbols * 100) if total_symbols > 0 else 0
    }
    
    # Log failed symbols
    failed_symbols = [r['symbol'] for r in results if r['status'] == 'error']
    if failed_symbols:
        logger.warning(f"Failed to collect data for: {', '.join(failed_symbols)}")
    
    logger.info(f"Collection summary: {summary}")
    return summary

@task
def log_workflow_metrics(summary: Dict[str, Any]) -> None:
    """
    Log workflow execution metrics to database
    
    Args:
        summary: Collection summary data
    """
    logger = get_run_logger()
    
    try:
        # Log to application database using our logging system
        app_logger = get_combined_logger("prefect.yahoo_collector")
        
        app_logger.info(
            f"Yahoo Finance collection completed: "
            f"{summary['successful_collections']}/{summary['total_symbols']} symbols, "
            f"{summary['total_records_collected']} records, "
            f"{summary['success_rate']:.1f}% success rate"
        )
        
        # Store metrics in performance_logs table
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO performance_logs 
                    (operation_name, duration_ms, status, component, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    'yahoo_market_hours_collection',
                    0,  # Duration will be calculated by Prefect
                    'success' if summary['failed_collections'] == 0 else 'partial_success',
                    'prefect_workflow',
                    f'{{"symbols_collected": {summary["successful_collections"]}, "total_records": {summary["total_records_collected"]}}}'
                ))
                conn.commit()
        
        logger.info("Workflow metrics logged successfully")
        
    except Exception as e:
        logger.error(f"Failed to log workflow metrics: {e}")

@flow(
    name="yahoo-market-hours-data-collection-with-features",
    description="Collects Yahoo Finance data during market hours and calculates Phase 1+2 features (36 total)",
    task_runner=ConcurrentTaskRunner(max_workers=5),
    log_prints=True,
    flow_run_name=generate_flow_run_name
)
def yahoo_market_hours_collection_flow() -> Dict[str, Any]:
    """
    Main workflow for collecting Yahoo Finance data during market hours,
    followed by Phase 1+2 feature engineering (36 features total).
    
    Sequential pipeline:
    1. Yahoo Data Collection (5-10 minutes for 100 symbols)
    2. Feature Engineering (2-3 seconds for 100 symbols) 
    3. Dashboard ready with fresh data + features
    
    Returns:
        Workflow execution summary including both data collection and features
    """
    logger = get_run_logger()
    
    # Log run start with friendly name
    logger.info(f"Starting Yahoo Finance data collection: {generate_flow_run_name()}")
    
    # Check if market is open
    market_open = check_market_hours()
    
    if not market_open:
        logger.info("Market is closed. Skipping data collection.")
        return {
            'status': 'skipped',
            'reason': 'market_closed',
            'timestamp': datetime.now(MARKET_TIMEZONE).isoformat()
        }
    
    logger.info("Market is open. Starting data collection...")
    
    # Get symbols to collect
    symbols = get_active_symbols()
    
    if not symbols:
        logger.warning("No symbols found for collection")
        return {
            'status': 'failed',
            'reason': 'no_symbols',
            'timestamp': datetime.now(MARKET_TIMEZONE).isoformat()
        }
    
    # Collect data for all symbols concurrently
    logger.info(f"Starting concurrent collection for {len(symbols)} symbols")
    
    # Use Prefect's mapping for concurrent execution
    collection_results = collect_symbol_data.map(symbols)
    
    # Generate summary
    summary = generate_collection_summary(collection_results)
    
    # Log metrics
    log_workflow_metrics(summary)
    
    logger.info("Yahoo Finance data collection completed successfully")
    
    # Chain feature engineering after successful data collection
    feature_result = None
    if summary['successful_collections'] > 0:
        logger.info("Starting Phase 1+2 feature engineering pipeline...")
        try:
            feature_result = feature_engineering_flow()
            logger.info("Feature engineering completed successfully")
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            feature_result = {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now(MARKET_TIMEZONE).isoformat()
            }
    else:
        logger.warning("Skipping feature engineering - no successful data collections")
        feature_result = {
            'status': 'skipped', 
            'reason': 'no_data_collected',
            'timestamp': datetime.now(MARKET_TIMEZONE).isoformat()
        }
    
    logger.info("Yahoo Finance + Feature Engineering workflow completed")
    
    return {
        'status': 'completed',
        'data_collection': summary,
        'feature_engineering': feature_result,
        'timestamp': datetime.now(MARKET_TIMEZONE).isoformat()
    }

# Standalone execution for testing
if __name__ == "__main__":
    # Run the flow locally for testing
    result = yahoo_market_hours_collection_flow()
    print(f"Workflow result: {result}")