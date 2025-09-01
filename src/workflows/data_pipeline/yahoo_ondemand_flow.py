"""
Yahoo Finance On-Demand Data Collection Workflow
Can be run anytime regardless of market hours - useful for testing and manual data collection
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import pytz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from prefect import flow, task
from prefect.task_runners import ConcurrentTaskRunner
from prefect.logging import get_run_logger

from src.data.collectors.yahoo_collector import fetch_yahoo_data, prepare_data_for_insert
from src.utils.logging_config import get_combined_logger
from src.data.storage.database import get_db_manager

# Market hours configuration for reference
MARKET_TIMEZONE = pytz.timezone('America/New_York')


def generate_ondemand_run_name() -> str:
    """
    Generate a user-friendly name for the on-demand flow run

    Returns:
        Formatted run name with timestamp
    """
    now = datetime.now(MARKET_TIMEZONE)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")  # Remove colon and spaces

    return f"yahoo-ondemand-{date_str}-{time_str}EST"


@task(retries=2, retry_delay_seconds=30)
def get_symbols_for_collection(limit: int = 20) -> List[str]:
    """
    Get list of symbols for data collection

    Args:
        limit: Maximum number of symbols to collect

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
                    LIMIT %s
                """, (limit,))

                symbols = [row[0] for row in cursor.fetchall()]

        logger.info(f"Retrieved {len(symbols)} symbols for data collection")
        return symbols

    except Exception as e:
        logger.error(f"Failed to get symbols from database: {e}")
        # Fallback to a set of major symbols
        fallback_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
            'META', 'NVDA', 'NFLX', 'AMD', 'INTC',
            'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'BAC', 'ADBE'
        ][:limit]
        logger.info(f"Using fallback symbols: {fallback_symbols}")
        return fallback_symbols


@task(retries=3, retry_delay_seconds=60)
def collect_symbol_data_ondemand(symbol: str, period: str = "1d") -> Dict[str, Any]:
    """
    Collect data for a single symbol - on-demand version

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
def generate_ondemand_summary(results: List[Dict[str, Any]], run_type: str = "manual") -> Dict[str, Any]:
    """
    Generate summary of on-demand data collection results

    Args:
        results: List of collection results from individual symbols
        run_type: Type of run (manual, test, etc.)

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
        'run_type': run_type,
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

    logger.info(f"On-demand collection summary: {summary}")
    return summary


@flow(
    name="yahoo-ondemand-data-collection",
    description="On-demand Yahoo Finance data collection with sequential processing (default) to prevent connection "
                "exhaustion",
    log_prints=True,
    flow_run_name=generate_ondemand_run_name
)
def yahoo_ondemand_collection_flow(
    symbols_limit: int = 20,
    period: str = "1d",
    run_type: str = "manual"
) -> Dict[str, Any]:
    """
    On-demand workflow for collecting Yahoo Finance data

    Args:
        symbols_limit: Maximum number of symbols to collect (default: 20)
        period: Time period for data collection (default: "1d")
        run_type: Type of run for tracking (default: "manual")

    Returns:
        Workflow execution summary
    """
    logger = get_run_logger()

    logger.info(f"Starting on-demand Yahoo Finance data collection (limit: {symbols_limit}, period: {period})")

    # Get symbols to collect
    symbols = get_symbols_for_collection(limit=symbols_limit)

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
    collection_results = collect_symbol_data_ondemand.map(symbols, period=[period] * len(symbols))

    # Generate summary
    summary = generate_ondemand_summary(collection_results, run_type=run_type)

    logger.info("On-demand Yahoo Finance data collection workflow completed")

    return {
        'status': 'completed',
        'summary': summary,
        'timestamp': datetime.now(MARKET_TIMEZONE).isoformat()
    }


# Standalone execution for testing
if __name__ == "__main__":
    # Run the flow locally for testing
    result = yahoo_ondemand_collection_flow(symbols_limit=5, run_type="test")
    print(f"On-demand workflow result: {result}")
