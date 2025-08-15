"""
Script to fix the mixed year data in market_data table.
Converts 2025 timestamps back to 2024 where they should be.
"""

import sys
from datetime import datetime
from src.data.storage.database import get_db_manager

def analyze_mixed_year_data():
    """Analyze the extent of the mixed year problem."""
    print("=" * 60)
    print("ANALYZING MIXED YEAR DATA")
    print("=" * 60)
    
    try:
        db = get_db_manager()
        conn = db.get_connection()
        
        with conn.cursor() as cur:
            # Check data distribution by year
            print("\n1. DATA DISTRIBUTION BY YEAR (ADBE):")
            cur.execute("""
                SELECT 
                    EXTRACT(YEAR FROM timestamp) as year,
                    COUNT(*) as record_count,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM market_data 
                WHERE symbol = 'ADBE'
                GROUP BY EXTRACT(YEAR FROM timestamp)
                ORDER BY year
            """)
            
            results = cur.fetchall()
            for year, count, earliest, latest in results:
                print(f"  Year {int(year)}: {count:,} records from {earliest} to {latest}")
            
            # Check how many symbols affected
            print("\n2. HOW MANY SYMBOLS HAVE 2025 DATA:")
            cur.execute("""
                SELECT COUNT(DISTINCT symbol) as affected_symbols
                FROM market_data 
                WHERE EXTRACT(YEAR FROM timestamp) = 2025
            """)
            
            affected_count = cur.fetchone()[0]
            print(f"  {affected_count} symbols have 2025 data")
            
            # Show sample of affected symbols
            cur.execute("""
                SELECT DISTINCT symbol 
                FROM market_data 
                WHERE EXTRACT(YEAR FROM timestamp) = 2025
                ORDER BY symbol
                LIMIT 10
            """)
            
            affected_symbols = [row[0] for row in cur.fetchall()]
            print(f"  Sample affected symbols: {', '.join(affected_symbols)}")
            
            # Check for overlapping dates (potential duplicates)
            print("\n3. CHECKING FOR OVERLAPPING DATES:")
            cur.execute("""
                SELECT 
                    symbol,
                    DATE(timestamp) as date,
                    COUNT(*) as records_per_day,
                    COUNT(DISTINCT EXTRACT(YEAR FROM timestamp)) as years_on_same_date
                FROM market_data 
                WHERE symbol = 'ADBE'
                GROUP BY symbol, DATE(timestamp)
                HAVING COUNT(DISTINCT EXTRACT(YEAR FROM timestamp)) > 1
                ORDER BY date
                LIMIT 5
            """)
            
            overlapping = cur.fetchall()
            if overlapping:
                print("  Found overlapping dates (same day in both 2024 and 2025):")
                for symbol, date, records, years in overlapping:
                    print(f"    {symbol} on {date}: {records} records across {years} years")
            else:
                print("  No overlapping dates found - safe to convert years")
        
        conn.close()
        return affected_count > 0
        
    except Exception as e:
        print(f"Error analyzing data: {e}")
        return False

def fix_year_data():
    """Fix the 2025 timestamps by converting them to 2024."""
    print("\n" + "=" * 60)
    print("FIXING YEAR DATA")
    print("=" * 60)
    
    try:
        db = get_db_manager()
        conn = db.get_connection()
        
        with conn.cursor() as cur:
            # First, count how many records will be affected
            cur.execute("""
                SELECT COUNT(*) FROM market_data 
                WHERE EXTRACT(YEAR FROM timestamp) = 2025
            """)
            
            records_to_fix = cur.fetchone()[0]
            
            if records_to_fix == 0:
                print("No 2025 records found to fix.")
                return True
            
            print(f"About to fix {records_to_fix:,} records with 2025 timestamps")
            
            # Get user confirmation
            response = input("Do you want to proceed? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Operation cancelled.")
                return False
            
            # Create backup table first
            print("\nCreating backup...")
            cur.execute("""
                DROP TABLE IF EXISTS market_data_backup_year_fix
            """)
            
            cur.execute("""
                CREATE TABLE market_data_backup_year_fix AS 
                SELECT * FROM market_data 
                WHERE EXTRACT(YEAR FROM timestamp) = 2025
            """)
            
            backup_count = cur.rowcount
            print(f"Backup created with {backup_count:,} records")
            
            # Apply the fix
            print("\nApplying year fix...")
            cur.execute("""
                UPDATE market_data 
                SET timestamp = timestamp - INTERVAL '1 year'
                WHERE EXTRACT(YEAR FROM timestamp) = 2025
            """)
            
            updated_count = cur.rowcount
            print(f"Updated {updated_count:,} records")
            
            # Commit the changes
            conn.commit()
            
            # Verify the fix
            print("\nVerifying fix...")
            cur.execute("""
                SELECT COUNT(*) FROM market_data 
                WHERE EXTRACT(YEAR FROM timestamp) = 2025
            """)
            
            remaining_2025 = cur.fetchone()[0]
            
            if remaining_2025 == 0:
                print("✅ SUCCESS: All 2025 timestamps have been converted to 2024")
                
                # Show new date range for ADBE
                cur.execute("""
                    SELECT MIN(timestamp), MAX(timestamp), COUNT(*)
                    FROM market_data 
                    WHERE symbol = 'ADBE'
                """)
                
                min_ts, max_ts, total_count = cur.fetchone()
                print(f"✅ ADBE now has {total_count:,} records from {min_ts} to {max_ts}")
                
            else:
                print(f"⚠️  WARNING: {remaining_2025} records still have 2025 timestamps")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error fixing data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to analyze and optionally fix year data."""
    
    # Analyze first
    has_issues = analyze_mixed_year_data()
    
    if not has_issues:
        print("\n✅ No year issues found in the database!")
        return
    
    # Ask if user wants to fix
    print("\n" + "=" * 60)
    fix_response = input("Do you want to fix the year data? (yes/no): ").strip().lower()
    
    if fix_response in ['yes', 'y']:
        success = fix_year_data()
        if success:
            print("\n🎉 Year data has been fixed! Restart your dashboard to see correct dates.")
        else:
            print("\n❌ Fix failed. Check the errors above.")
    else:
        print("\nNo changes made. The dashboard will continue showing 2025 dates.")

if __name__ == "__main__":
    main()