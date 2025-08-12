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

from data.storage.database import get_db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/yahoo_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


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


def fetch_stock_info(symbol: str) -> Dict[str, Any]:
    """Fetch stock information including sector and industry from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
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
        
        logger.info(f"Fetched stock info for {symbol}: {stock_data['company_name']} - {stock_data['sector']}/{stock_data['industry']}")
        return stock_data
        
    except Exception as e:
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


def fetch_yahoo_data(symbol: str, period: str = '2y', interval: str = '1h') -> pd.DataFrame:
    """Fetch data from Yahoo Finance."""
    try:
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
                logger.error(f"Failed to fetch {symbol} with daily interval: {e2}")
                return pd.DataFrame()
        
        if data.empty:
            logger.warning(f"No data found for symbol: {symbol}")
            return pd.DataFrame()
        
        # Reset index to make Date a column
        data = data.reset_index()
        
        # Check what columns we actually have
        logger.info(f"Available columns for {symbol}: {list(data.columns)}")
        
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
        
        logger.info(f"Fetched {len(data)} records for {symbol}")
        return data
    
    except Exception as e:
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


def extract_and_load_data(symbols: List[str], period: str = '1y', interval: str = '1h'):
    """Extract data from Yahoo Finance and load into database."""
    db_manager = get_db_manager()
    total_records = 0
    stock_info_count = 0
    
    # Process symbols in chunks to avoid overwhelming the API
    chunk_size = 10
    for i in range(0, len(symbols), chunk_size):
        chunk_symbols = symbols[i:i + chunk_size]
        logger.info(f"Processing chunk {i // chunk_size + 1} containing {len(chunk_symbols)} symbols...")
        
        for symbol in chunk_symbols:
            logger.info(f"Processing symbol: {symbol}")
            
            # Fetch stock information first
            try:
                stock_info = fetch_stock_info(symbol)
                db_manager.insert_stock_info(stock_info)
                stock_info_count += 1
                logger.info(f"Successfully loaded stock info for {symbol}")
            except Exception as e:
                logger.error(f"Error loading stock info for {symbol}: {e}")
            
            # Fetch market data from Yahoo Finance
            df = fetch_yahoo_data(symbol, period, interval)
            
            if df.empty:
                continue
            
            # Prepare data for database insertion
            data_list = prepare_data_for_insert(df)
            
            if data_list:
                try:
                    # Insert data into database
                    db_manager.insert_market_data(data_list)
                    total_records += len(data_list)
                    logger.info(f"Successfully loaded {len(data_list)} records for {symbol}")
                
                except Exception as e:
                    logger.error(f"Error inserting data for {symbol}: {e}")
        
        # Add a small delay between chunks to be respectful to the API
        if i + chunk_size < len(symbols):
            logger.info("Waiting 2 seconds before processing next chunk...")
            time.sleep(2)
    
    logger.info(f"Data extraction complete. Total records loaded: {total_records}, Stock info loaded: {stock_info_count}")


def main():
    """Main function to run the data extraction."""
    logger.info("Starting Yahoo Finance data extraction...")
    
    # Load symbols from config file
    symbols = load_symbols_from_file()
    
    if not symbols:
        logger.error("No symbols loaded. Please check the config/symbols.txt file.")
        return
    
    # Extract and load data (use hourly data by default)
    extract_and_load_data(symbols, period='1y', interval='1h')
    
    logger.info("Data extraction process completed.")


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    main() 