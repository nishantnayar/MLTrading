"""
Investigate why database queries return 2025 when database contains 2024 data.
This suggests a timezone conversion or pandas datetime issue.
"""

import sys
from datetime import datetime
import pandas as pd
from src.data.storage.database import get_db_manager

def investigate_date_conversion():
    """Investigate the date conversion issue step by step."""
    print("=" * 70)
    print("INVESTIGATING DATE CONVERSION ISSUE")
    print("=" * 70)
    
    try:
        db = get_db_manager()
        conn = db.get_connection()
        
        # 1. Raw psycopg2 query (no pandas)
        print("\n1. RAW PSYCOPG2 QUERY (No Pandas):")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, EXTRACT(YEAR FROM timestamp) as year
                FROM market_data 
                WHERE symbol = 'ADBE'
                ORDER BY timestamp DESC 
                LIMIT 3
            """)
            
            print("Raw psycopg2 results:")
            for row in cur.fetchall():
                timestamp, year = row
                print(f"  {timestamp} (Year: {int(year)}) Type: {type(timestamp)}")
        
        # 2. Pandas read_sql with same query
        print("\n2. PANDAS READ_SQL (Same Query):")
        df = pd.read_sql_query("""
            SELECT timestamp, EXTRACT(YEAR FROM timestamp) as year
            FROM market_data 
            WHERE symbol = 'ADBE'
            ORDER BY timestamp DESC 
            LIMIT 3
        """, conn)
        
        print("Pandas results:")
        for _, row in df.iterrows():
            timestamp = row['timestamp']
            year = row['year']
            print(f"  {timestamp} (Year: {int(year)}) Type: {type(timestamp)}")
            if hasattr(timestamp, 'tz'):
                print(f"    Timezone: {timestamp.tz}")
        
        # 3. Check database timezone settings
        print("\n3. DATABASE TIMEZONE SETTINGS:")
        with conn.cursor() as cur:
            cur.execute("SHOW timezone;")
            db_tz = cur.fetchone()[0]
            print(f"Database timezone: {db_tz}")
            
            cur.execute("SELECT NOW();")
            db_now = cur.fetchone()[0]
            print(f"Database NOW(): {db_now}")
            
            # Check a specific timestamp
            cur.execute("""
                SELECT timestamp, 
                       timestamp AT TIME ZONE 'UTC' as utc_timestamp,
                       timestamp AT TIME ZONE 'America/Chicago' as chicago_timestamp
                FROM market_data 
                WHERE symbol = 'ADBE'
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            
            result = cur.fetchone()
            if result:
                orig, utc, chicago = result
                print(f"Original: {orig}")
                print(f"As UTC: {utc}")
                print(f"As Chicago: {chicago}")
        
        # 4. Test what happens with different pandas parameters
        print("\n4. PANDAS WITH DIFFERENT PARAMETERS:")
        
        # Try without timezone conversion
        df_no_parse = pd.read_sql_query("""
            SELECT timestamp::text as timestamp_text, timestamp
            FROM market_data 
            WHERE symbol = 'ADBE'
            ORDER BY timestamp DESC 
            LIMIT 2
        """, conn)
        
        print("Pandas with text conversion:")
        for _, row in df_no_parse.iterrows():
            print(f"  Text: {row['timestamp_text']}")
            print(f"  Timestamp: {row['timestamp']} (Type: {type(row['timestamp'])})")
        
        # 5. Check system timezone
        print("\n5. SYSTEM TIMEZONE:")
        import time
        print(f"System timezone: {time.tzname}")
        print(f"Python datetime.now(): {datetime.now()}")
        
        # 6. Test direct database connection vs service
        print("\n6. COMPARE DB MANAGER VS DIRECT:")
        
        # Using db manager (like dashboard)
        direct_df = db.get_market_data('ADBE', datetime(2024, 8, 1), datetime(2024, 8, 15))
        if not direct_df.empty:
            print(f"DB Manager result: {len(direct_df)} records")
            print(f"Date range: {direct_df['timestamp'].min()} to {direct_df['timestamp'].max()}")
        else:
            print("DB Manager returned empty DataFrame")
        
        conn.close()
        
    except Exception as e:
        print(f"Error during investigation: {e}")
        import traceback
        traceback.print_exc()

def test_pandas_timezone_behavior():
    """Test if pandas is doing automatic timezone conversion."""
    print("\n" + "=" * 70)
    print("TESTING PANDAS TIMEZONE BEHAVIOR")
    print("=" * 70)
    
    try:
        # Create a test DataFrame with 2024 dates
        test_dates = [
            '2024-08-02 08:30:00',
            '2024-08-02 09:30:00',
            '2024-08-02 10:30:00'
        ]
        
        print("\n1. TEST DATES:")
        for date_str in test_dates:
            print(f"  {date_str}")
        
        # Test pandas to_datetime with different settings
        print("\n2. PANDAS TO_DATETIME TESTS:")
        
        # Default behavior
        pd_default = pd.to_datetime(test_dates)
        print("Default pd.to_datetime:")
        for ts in pd_default:
            print(f"  {ts} (Type: {type(ts)})")
        
        # With UTC
        pd_utc = pd.to_datetime(test_dates, utc=True)
        print("With UTC=True:")
        for ts in pd_utc:
            print(f"  {ts} (Type: {type(ts)})")
        
        # With specific timezone
        pd_chicago = pd.to_datetime(test_dates).tz_localize('America/Chicago')
        print("Localized to Chicago:")
        for ts in pd_chicago:
            print(f"  {ts}")
        
        # Convert to different timezone
        pd_converted = pd_chicago.tz_convert('UTC')
        print("Converted to UTC:")
        for ts in pd_converted:
            print(f"  {ts}")
        
    except Exception as e:
        print(f"Error in timezone testing: {e}")

if __name__ == "__main__":
    investigate_date_conversion()
    test_pandas_timezone_behavior()