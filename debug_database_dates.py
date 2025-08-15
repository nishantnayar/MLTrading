"""
Debug script to investigate the database date issue.
Run this to see exactly where the year conversion is happening.
"""

import pandas as pd
from datetime import datetime, timedelta
from src.data.storage.database import get_db_manager

def debug_database_dates():
    """Debug function to investigate date issues."""
    
    print("=" * 60)
    print("DATABASE DATE DEBUGGING")
    print("=" * 60)
    
    try:
        db = get_db_manager()
        
        # 1. Direct SQL query to see raw database content
        print("\n1. DIRECT SQL QUERY (Raw Database Content):")
        conn = db.get_connection()
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, EXTRACT(YEAR FROM timestamp) as year, close 
                FROM market_data 
                WHERE symbol = 'ADBE' 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            results = cur.fetchall()
            
            print("Raw SQL Results (Recent 5 records):")
            for row in results:
                timestamp, year, close = row
                print(f"  {timestamp} (Year: {year}) - Close: ${close}")
        
        conn.close()
        
        # 2. Using pandas read_sql (same as dashboard)
        print("\n2. PANDAS READ_SQL (Same as Dashboard):")
        conn = db.get_connection()
        
        df_pandas = pd.read_sql_query("""
            SELECT symbol, timestamp, close 
            FROM market_data 
            WHERE symbol = 'ADBE' 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, conn)
        
        conn.close()
        
        print("Pandas Results:")
        for _, row in df_pandas.iterrows():
            timestamp = row['timestamp']
            print(f"  {timestamp} (Type: {type(timestamp)}) - Close: ${row['close']}")
        
        # 3. Using get_market_data method with date range
        print("\n3. GET_MARKET_DATA METHOD (Dashboard Service):")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"Requesting date range: {start_date} to {end_date}")
        
        df_method = db.get_market_data('ADBE', start_date, end_date)
        
        if not df_method.empty:
            actual_start = df_method['timestamp'].min()
            actual_end = df_method['timestamp'].max()
            print(f"Received {len(df_method)} records")
            print(f"Actual date range: {actual_start} to {actual_end}")
            print(f"Sample timestamps:")
            for i, timestamp in enumerate(df_method['timestamp'].head(3)):
                print(f"  {timestamp} (Type: {type(timestamp)})")
        else:
            print("No data returned from get_market_data method")
        
        # 4. Check if there's timezone issue
        print("\n4. TIMEZONE INVESTIGATION:")
        conn = db.get_connection()
        
        with conn.cursor() as cur:
            cur.execute("SELECT current_setting('timezone');")
            tz_result = cur.fetchone()
            print(f"Database timezone: {tz_result[0] if tz_result else 'Unknown'}")
            
            cur.execute("SELECT NOW();")
            now_result = cur.fetchone()
            print(f"Database current time: {now_result[0] if now_result else 'Unknown'}")
        
        conn.close()
        
        # 5. Summary
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print("If raw SQL shows 2024 but pandas shows 2025:")
        print("  -> There's a pandas/Python datetime conversion issue")
        print("If raw SQL shows 2025:")
        print("  -> The data is actually stored as 2025 in database")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_database_dates()