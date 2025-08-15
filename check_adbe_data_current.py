"""
Check current ADBE data status to see what changes have been made.
"""

from src.data.storage.database import get_db_manager

def check_adbe_data():
    """Check current state of ADBE data."""
    print("=" * 60)
    print("CHECKING CURRENT ADBE DATA")
    print("=" * 60)
    
    try:
        db = get_db_manager()
        conn = db.get_connection()
        
        with conn.cursor() as cur:
            # Overall count and date range
            print("\n1. OVERALL ADBE DATA:")
            cur.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM market_data 
                WHERE symbol = 'ADBE'
            """)
            
            result = cur.fetchone()
            if result:
                count, earliest, latest = result
                print(f"  Total records: {count:,}")
                print(f"  Date range: {earliest} to {latest}")
            else:
                print("  No ADBE data found")
                return
            
            # Year distribution
            print("\n2. YEAR DISTRIBUTION:")
            cur.execute("""
                SELECT 
                    EXTRACT(YEAR FROM timestamp) as year,
                    COUNT(*) as count,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM market_data 
                WHERE symbol = 'ADBE'
                GROUP BY EXTRACT(YEAR FROM timestamp)
                ORDER BY year
            """)
            
            year_results = cur.fetchall()
            for year, count, earliest, latest in year_results:
                print(f"  Year {int(year)}: {count:,} records from {earliest} to {latest}")
            
            # Recent 10 records
            print("\n3. MOST RECENT 10 RECORDS:")
            cur.execute("""
                SELECT timestamp, close
                FROM market_data 
                WHERE symbol = 'ADBE'
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            recent_results = cur.fetchall()
            for i, (timestamp, close) in enumerate(recent_results, 1):
                print(f"  {i:2d}. {timestamp} - ${close:.2f}")
            
            # Oldest 5 records  
            print("\n4. OLDEST 5 RECORDS:")
            cur.execute("""
                SELECT timestamp, close
                FROM market_data 
                WHERE symbol = 'ADBE'
                ORDER BY timestamp ASC
                LIMIT 5
            """)
            
            oldest_results = cur.fetchall()
            for i, (timestamp, close) in enumerate(oldest_results, 1):
                print(f"  {i}. {timestamp} - ${close:.2f}")
            
            # Check for any remaining 2025 data
            print("\n5. CHECK FOR 2025 DATA:")
            cur.execute("""
                SELECT COUNT(*) 
                FROM market_data 
                WHERE symbol = 'ADBE' 
                AND EXTRACT(YEAR FROM timestamp) = 2025
            """)
            
            count_2025 = cur.fetchone()[0]
            if count_2025 > 0:
                print(f"  ⚠️  Still has {count_2025:,} records with 2025 timestamps")
            else:
                print("  ✅ No 2025 data found - all timestamps are in correct year")
            
            # Sample of any 2025 data if it exists
            if count_2025 > 0:
                print("\n6. SAMPLE 2025 DATA:")
                cur.execute("""
                    SELECT timestamp, close
                    FROM market_data 
                    WHERE symbol = 'ADBE' 
                    AND EXTRACT(YEAR FROM timestamp) = 2025
                    ORDER BY timestamp
                    LIMIT 5
                """)
                
                sample_2025 = cur.fetchall()
                for timestamp, close in sample_2025:
                    print(f"    {timestamp} - ${close:.2f}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking ADBE data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_adbe_data()