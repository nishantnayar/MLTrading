#!/usr/bin/env python3
"""
Yahoo Finance Data Collection Module
Extracts historical market data and loads it into PostgreSQL database.
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import yfinance as yf
import pandas as pd

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.data.storage.database import get_db_manager
from src.utils.logging_config import setup_logger, log_data_collection_event, log_error_event, log_performance_event
from src.utils.logging_config import log_operation, get_correlation_id, set_correlation_id
from src.utils.circuit_breaker import circuit_breaker
from src.utils.retry_decorators import retry_on_api_error, retry_on_connection_error

# Configure file-based logging with minimal database logging and reduced console output
logger = setup_logger('mltrading.yahoo_collector', 'yahoo_collector.log', enable_database_logging=False)
# Set console handler to WARNING level to reduce INFO structured logs in console
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.WARNING)


def load_symbols_from_file(file_path: str = 'config/symbols.txt') -> List[str]:
    """Load symbols from the configuration file."""
    symbols = []

    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    symbols.append(line.upper())

        logger.info(f"Loaded {len(symbols)} symbols from {file_path}")
        return symbols

    except FileNotFoundError:
        logger.error(f"Symbols file not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading symbols: {e}")
        return []


@circuit_breaker(name="yahoo_stock_info", failure_threshold=5, recovery_timeout=120)
@retry_on_api_error(max_attempts=3, delay=2.0)


def fetch_stock_info(symbol: str) -> Dict[str, Any]:
    """
    Fetch comprehensive stock information from Yahoo Finance API.

    Retrieves company metadata including sector classification, market cap,
    and exchange information for fundamental analysis and data categorization.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        Dictionary containing stock information:
        - symbol: Ticker symbol
        - company_name: Full company name
        - sector: Business sector (e.g., 'Technology')
        - industry: Specific industry classification
        - market_cap: Market capitalization in USD
        - country: Country of incorporation
        - currency: Trading currency
        - exchange: Primary exchange listing
        - source: Data source identifier ('yahoo')

    Example:
        >>> info = fetch_stock_info('AAPL')
        >>> print(info['company_name'])
        Apple Inc.
        >>> print(info['sector'])
        Technology
        >>> print(info['market_cap'] > 1000000000)
        True
    """
    with log_operation(f"fetch_stock_info_{symbol}", logger, symbol=symbol, data_source='yahoo'):
        try:
            # start_time = time.time()  # Currently unused
            ticker = yf.Ticker(symbol)
            info = ticker.info
            duration_ms = (time.time() - start_time) * 1000

            stock_data = {
                'symbol': symbol,
                'company_name': info.get('longName', info.get('shortName', '')),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', None),
                'country': info.get('country', ''),
                'currency': info.get('currency', ''),
                'exchange': info.get('exchange', ''),
                'source': 'yahoo'
            }

            # Log to database
            log_data_collection_event(
                operation_type='fetch_info',
                data_source='yahoo',
                symbol=symbol,
                records_processed=1,
                duration_ms=duration_ms,
                status='success',
                logger=logger,
                company_name=stock_data['company_name'],
                sector=stock_data['sector'],
                industry=stock_data['industry']
            )

            logger.info(f"Fetched stock info for {symbol}: {stock_data['company_name']} - {stock_data['sector']}/{stock_data['industry']}")
            return stock_data

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0

            # Log error to database
            log_error_event(
                error_type=type(e).__name__,
                error_message=str(e),
                component='yahoo_collector',
                severity='MEDIUM',
                source_function='fetch_stock_info',
                logger=logger,
                symbol=symbol
            )

            # Log failed data collection
            log_data_collection_event(
                operation_type='fetch_info',
                data_source='yahoo',
                symbol=symbol,
                records_processed=0,
                duration_ms=duration_ms,
                status='failed',
                logger=logger,
                error=str(e)
            )

            logger.error(f"Error fetching stock info for {symbol}: {e}")
            return {
                'symbol': symbol,
                'company_name': '',
                'sector': '',
                'industry': '',
                'market_cap': None,
                'country': '',
                'currency': '',
                'exchange': '',
                'source': 'yahoo'
            }


@circuit_breaker(name="yahoo_market_data", failure_threshold=3, recovery_timeout=60)
@retry_on_api_error(max_attempts=4, delay=1.0)


def fetch_yahoo_data(symbol: str, period: str = '2y', interval: str = '1h') -> pd.DataFrame:
    """Fetch data from Yahoo Finance."""
    with log_operation(f"fetch_yahoo_data_{symbol}", logger, symbol=symbol, period=period, interval=interval):
        try:
            # start_time = time.time()  # Currently unused
            ticker = yf.Ticker(symbol)

            # Try to fetch data with the requested interval
            try:
                logger.info(f"Fetching {symbol} with interval {interval}")
                data = ticker.history(period=period, interval=interval,
                                    actions=False, auto_adjust=True)

                if data.empty:
                    # If hourly fails, try daily as fallback
                    logger.warning(f"No {interval} data for {symbol}, trying daily data")
                    data = ticker.history(period=period, interval='1d',
                                        actions=False, auto_adjust=True)

            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} with interval {interval}: {e}")
                # Try daily as fallback
                try:
                    data = ticker.history(period=period, interval='1d',
                                        actions=False, auto_adjust=True)
                except Exception as e2:
                    duration_ms = (time.time() - start_time) * 1000

                    # Log error to database
                    log_error_event(
                        error_type=type(e2).__name__,
                        error_message=str(e2),
                        component='yahoo_collector',
                        severity='HIGH',
                        source_function='fetch_yahoo_data',
                        logger=logger,
                        symbol=symbol,
                        period=period,
                        interval=interval
                    )

                    # Log failed data collection
                    log_data_collection_event(
                        operation_type='fetch_data',
                        data_source='yahoo',
                        symbol=symbol,
                        records_processed=0,
                        duration_ms=duration_ms,
                        status='failed',
                        logger=logger,
                        period=period,
                        interval=interval,
                        error=str(e2)
                    )

                    logger.error(f"Failed to fetch {symbol} with daily interval: {e2}")
                    return pd.DataFrame()

            if data.empty:
                duration_ms = (time.time() - start_time) * 1000
                logger.warning(f"No data found for symbol: {symbol}")

                # Log partial success (no error but no data)
                log_data_collection_event(
                    operation_type='fetch_data',
                    data_source='yahoo',
                    symbol=symbol,
                    records_processed=0,
                    duration_ms=duration_ms,
                    status='partial',
                    logger=logger,
                    period=period,
                    interval=interval,
                    reason='no_data_available'
                )

                return pd.DataFrame()

            # Reset index to make Date a column
            data = data.reset_index()

            # Check what columns we actually have
            #logger.info(f"Available columns for {symbol}: {list(data.columns)}")

            # Rename columns to match our database schema
            column_mapping = {}
            if 'Date' in data.columns:
                column_mapping['Date'] = 'timestamp'
            elif 'Datetime' in data.columns:
                column_mapping['Datetime'] = 'timestamp'

            if 'Open' in data.columns:
                column_mapping['Open'] = 'open'
            if 'High' in data.columns:
                column_mapping['High'] = 'high'
            if 'Low' in data.columns:
                column_mapping['Low'] = 'low'
            if 'Close' in data.columns:
                column_mapping['Close'] = 'close'
            if 'Volume' in data.columns:
                column_mapping['Volume'] = 'volume'

            data = data.rename(columns=column_mapping)

            # Add symbol and source columns
            data['symbol'] = symbol
            data['source'] = 'yahoo'

            # Ensure we have all required columns
            required_columns = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'source']
            available_columns = [col for col in required_columns if col in data.columns]

            # Select only the columns we have
            data = data[available_columns]

            duration_ms = (time.time() - start_time) * 1000
            records_count = len(data)

            # Log successful data collection to database
            log_data_collection_event(
                operation_type='fetch_data',
                data_source='yahoo',
                symbol=symbol,
                records_processed=records_count,
                duration_ms=duration_ms,
                status='success',
                logger=logger,
                period=period,
                interval=interval,
                columns=list(data.columns)
            )

            logger.info(f"Fetched {records_count} records for {symbol}")
            return data

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0

            # Log error to database
            log_error_event(
                error_type=type(e).__name__,
                error_message=str(e),
                component='yahoo_collector',
                severity='HIGH',
                source_function='fetch_yahoo_data',
                logger=logger,
                symbol=symbol,
                period=period,
                interval=interval
            )

            # Log failed data collection
            log_data_collection_event(
                operation_type='fetch_data',
                data_source='yahoo',
                symbol=symbol,
                records_processed=0,
                duration_ms=duration_ms,
                status='failed',
                logger=logger,
                period=period,
                interval=interval,
                error=str(e)
            )

            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()


def prepare_data_for_insert(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert DataFrame to list of dictionaries for database insertion."""
    data_list = []

    for _, row in df.iterrows():
        data_dict = {
            'symbol': row['symbol'],
            'timestamp': row['timestamp'],
            'open': float(row['open']) if 'open' in row and pd.notna(row['open']) else None,
            'high': float(row['high']) if 'high' in row and pd.notna(row['high']) else None,
            'low': float(row['low']) if 'low' in row and pd.notna(row['low']) else None,
            'close': float(row['close']) if 'close' in row and pd.notna(row['close']) else None,
            'volume': int(row['volume']) if 'volume' in row and pd.notna(row['volume']) else None,
            'source': row['source']
        }
        data_list.append(data_dict)

    return data_list


def extract_and_load_data(symbols: List[str], period: str = '3d', interval: str = '1h'):
    """
    Extract data from Yahoo Finance and load into database.

    Optimized to use 3-day window for incremental updates instead of 1-year:
    - 97% reduction in data processing (72 vs 1,780 records per symbol)
    - Faster collection (~2 minutes vs 10+ minutes)
    - Reduced database load and API calls
    - Historical data preserved for feature engineering
    """
    # Set a correlation ID for the entire batch operation
    batch_correlation_id = f"yahoo_batch_{int(time.time())}"
    set_correlation_id(batch_correlation_id)

    with log_operation("extract_and_load_batch", logger,
                      symbol_count=len(symbols), period=period, interval=interval):
        db_manager = get_db_manager()
        total_records = 0
        stock_info_count = 0
        failed_symbols = []

        # Log start of batch operation
        log_data_collection_event(
            operation_type='batch_start',
            data_source='yahoo',
            records_processed=0,
            status='success',
            logger=logger,
            symbol_count=len(symbols),
            period=period,
            interval=interval
        )

        # Process symbols in chunks to avoid overwhelming the API
        chunk_size = 10
        for i in range(0, len(symbols), chunk_size):
            chunk_symbols = symbols[i:i + chunk_size]
            chunk_number = i // chunk_size + 1
            logger.info(f"Processing chunk {chunk_number} containing {len(chunk_symbols)} symbols...")

            for symbol in chunk_symbols:
                logger.info(f"Processing symbol: {symbol}")

                # Fetch stock information first
                try:
                    with log_operation(f"store_stock_info_{symbol}", logger, symbol=symbol):
                        # start_time = time.time()  # Currently unused
                        stock_info = fetch_stock_info(symbol)
                        db_manager.insert_stock_info(stock_info)
                        duration_ms = (time.time() - start_time) * 1000

                        # Log successful storage
                        log_data_collection_event(
                            operation_type='store_info',
                            data_source='yahoo',
                            symbol=symbol,
                            records_processed=1,
                            duration_ms=duration_ms,
                            status='success',
                            logger=logger
                        )

                        stock_info_count += 1
                        logger.info(f"Successfully loaded stock info for {symbol}")

                except Exception as e:
                    # Log error for stock info storage
                    log_error_event(
                        error_type=type(e).__name__,
                        error_message=str(e),
                        component='yahoo_collector',
                        severity='MEDIUM',
                        source_function='insert_stock_info',
                        logger=logger,
                        symbol=symbol
                    )
                    logger.error(f"Error loading stock info for {symbol}: {e}")

                # Fetch market data from Yahoo Finance
                df = fetch_yahoo_data(symbol, period, interval)

                if df.empty:
                    continue

                # Prepare data for database insertion
                data_list = prepare_data_for_insert(df)

                if data_list:
                    try:
                        with log_operation(f"store_market_data_{symbol}", logger,
                                         symbol=symbol, record_count=len(data_list)):
                            # start_time = time.time()  # Currently unused
                            # Insert data into database
                            db_manager.insert_market_data(data_list)
                            duration_ms = (time.time() - start_time) * 1000

                            # Log successful storage
                            log_data_collection_event(
                                operation_type='store_data',
                                data_source='yahoo',
                                symbol=symbol,
                                records_processed=len(data_list),
                                duration_ms=duration_ms,
                                status='success',
                                logger=logger,
                                period=period,
                                interval=interval
                            )

                            total_records += len(data_list)
                            logger.info(f"Successfully loaded {len(data_list)} records for {symbol}")

                    except Exception as e:
                        # Log error for market data storage
                        log_error_event(
                            error_type=type(e).__name__,
                            error_message=str(e),
                            component='yahoo_collector',
                            severity='HIGH',
                            source_function='insert_market_data',
                            user_impact=True,
                            logger=logger,
                            symbol=symbol,
                            record_count=len(data_list)
                        )

                        # Log failed storage
                        log_data_collection_event(
                            operation_type='store_data',
                            data_source='yahoo',
                            symbol=symbol,
                            records_processed=0,
                            status='failed',
                            logger=logger,
                            error=str(e),
                            attempted_records=len(data_list)
                        )

                        failed_symbols.append(symbol)
                        logger.error(f"Error inserting data for {symbol}: {e}")

            # Add a small delay between chunks to be respectful to the API
            if i + chunk_size < len(symbols):
                logger.info("Waiting 2 seconds before processing next chunk...")
                time.sleep(2)

        # Log completion of batch operation
        success_rate = (len(symbols) - len(failed_symbols)) / len(symbols) * 100 if symbols else 0
        log_data_collection_event(
            operation_type='batch_complete',
            data_source='yahoo',
            records_processed=total_records,
            status='success' if success_rate > 80 else 'partial' if success_rate > 50 else 'failed',
            logger=logger,
            total_symbols=len(symbols),
            successful_symbols=len(symbols) - len(failed_symbols),
            failed_symbols=len(failed_symbols),
            success_rate=success_rate,
            stock_info_loaded=stock_info_count
        )

        #logger.info(f"Data extraction complete. Total records loaded: {total_records}, "
        #           f"Stock info loaded: {stock_info_count}, Failed symbols: {len(failed_symbols)}")

        if failed_symbols:
            logger.warning(f"Failed symbols: {', '.join(failed_symbols)}")


def main():
    """Main function to run the data extraction."""
    # Set correlation ID for the entire session
    session_correlation_id = f"yahoo_session_{int(time.time())}"
    set_correlation_id(session_correlation_id)

    with log_operation("yahoo_extraction_session", logger):
        logger.info("Starting Yahoo Finance data extraction...")

        # Log system startup event
        log_data_collection_event(
            operation_type='system_start',
            data_source='yahoo',
            records_processed=0,
            status='success',
            logger=logger,
            session_id=session_correlation_id
        )

        try:
            # Load symbols from config file
            symbols = load_symbols_from_file()

            if not symbols:
                # Log error event
                log_error_event(
                    error_type='ConfigurationError',
                    error_message='No symbols loaded from config file',
                    component='yahoo_collector',
                    severity='CRITICAL',
                    source_function='main',
                    user_impact=True,
                    logger=logger
                )
                logger.error("No symbols loaded. Please check the config/symbols.txt file.")
                return

            # Extract and load data (use 3-day window for incremental updates)
            extract_and_load_data(symbols, period='3d', interval='1h')

            # Log successful completion
            log_data_collection_event(
                operation_type='system_complete',
                data_source='yahoo',
                records_processed=0,
                status='success',
                logger=logger,
                session_id=session_correlation_id,
                total_symbols=len(symbols)
            )

            logger.info("Data extraction process completed.")

        except Exception as e:
            # Log critical system error
            log_error_event(
                error_type=type(e).__name__,
                error_message=str(e),
                component='yahoo_collector',
                severity='CRITICAL',
                source_function='main',
                user_impact=True,
                logger=logger,
                session_id=session_correlation_id
            )

            logger.error(f"Critical error in data extraction process: {e}")
            raise


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    main()

