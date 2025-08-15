"""
Test script to see what dates yfinance is actually returning.
This will help us understand if the issue is in data source or processing.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

def test_yfinance_dates():
    print("=" * 60)
    print("YFINANCE DATE TESTING")
    print("=" * 60)
    
    try:
        # Test with ADBE
        ticker = yf.Ticker('ADBE')
        
        # Get recent data
        print("\n1. RECENT 1-WEEK DATA:")
        data_1w = ticker.history(period='1w', interval='1h')
        
        if not data_1w.empty:
            data_1w_reset = data_1w.reset_index()
            print(f"Shape: {data_1w_reset.shape}")
            print(f"Columns: {list(data_1w_reset.columns)}")
            print("\nFirst 3 timestamps:")
            for i, ts in enumerate(data_1w_reset.iloc[:3].index if 'Date' not in data_1w_reset.columns else data_1w_reset['Date'].head(3)):
                print(f"  {i+1}: {ts} (Type: {type(ts)})")
                
            print("\nLast 3 timestamps:")
            last_timestamps = data_1w_reset.iloc[-3:].index if 'Date' not in data_1w_reset.columns else data_1w_reset['Date'].tail(3)
            for i, ts in enumerate(last_timestamps):
                print(f"  {i+1}: {ts} (Type: {type(ts)})")
        
        # Test with 2 years of data (like your collector)
        print("\n2. 2-YEAR DATA (like your collector):")
        data_2y = ticker.history(period='2y', interval='1h')
        
        if not data_2y.empty:
            data_2y_reset = data_2y.reset_index()
            print(f"Shape: {data_2y_reset.shape}")
            
            # Check date column
            date_col = 'Date' if 'Date' in data_2y_reset.columns else 'Datetime'
            if date_col in data_2y_reset.columns:
                print(f"Date column: {date_col}")
                min_date = data_2y_reset[date_col].min()
                max_date = data_2y_reset[date_col].max()
                print(f"Date range: {min_date} to {max_date}")
                
                # Extract years
                years = data_2y_reset[date_col].dt.year.unique()
                print(f"Years present: {sorted(years)}")
                
                # Sample recent data
                print("\nMost recent 5 records:")
                recent = data_2y_reset.tail(5)
                for _, row in recent.iterrows():
                    print(f"  {row[date_col]} - Close: ${row['Close']:.2f}")
            else:
                print("Using index as date")
                min_date = data_2y_reset.index.min()
                max_date = data_2y_reset.index.max()
                print(f"Index date range: {min_date} to {max_date}")
        
        # Test what your current database might have been created from
        print("\n3. SPECIFIC DATE RANGE TEST:")
        # Test Aug 2024 data
        try:
            start_date = '2024-08-01'
            end_date = '2024-08-15'
            data_specific = ticker.history(start=start_date, end=end_date, interval='1h')
            
            if not data_specific.empty:
                data_specific_reset = data_specific.reset_index()
                print(f"Aug 2024 data shape: {data_specific_reset.shape}")
                
                date_col = 'Date' if 'Date' in data_specific_reset.columns else 'Datetime'
                if date_col in data_specific_reset.columns:
                    sample_dates = data_specific_reset[date_col].head(3)
                    print("Sample Aug 2024 dates from yfinance:")
                    for date in sample_dates:
                        print(f"  {date} (Year: {date.year})")
            else:
                print("No data for Aug 2024 date range")
                
        except Exception as e:
            print(f"Error testing specific date range: {e}")
        
        # Check system timezone
        print(f"\n4. SYSTEM INFO:")
        print(f"Current system time: {datetime.now()}")
        
        # Check if yfinance has timezone issues
        print(f"\n5. TIMEZONE CHECK:")
        sample_ticker = yf.Ticker('AAPL')
        sample_data = sample_ticker.history(period='1d', interval='1h')
        if not sample_data.empty:
            sample_reset = sample_data.reset_index()
            if 'Date' in sample_reset.columns:
                sample_ts = sample_reset['Date'].iloc[0]
                print(f"Sample timestamp: {sample_ts}")
                print(f"Timezone info: {sample_ts.tz if hasattr(sample_ts, 'tz') else 'No timezone'}")
        
    except Exception as e:
        print(f"Error in yfinance testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yfinance_dates()