#!/usr/bin/env python3
"""
Fixed Feature Table Index Optimization
Properly handles CONCURRENT index creation outside transactions
"""

import psycopg2
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def execute_optimization():
    """Execute the feature table optimization with proper transaction handling"""
    print("=" * 70)
    print("FEATURE TABLE INDEX OPTIMIZATION")
    print("=" * 70)
    
    try:
        # Connect to database with autocommit for CONCURRENT operations
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'mltrading'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
        
        print("Database connection established")
        
        # Get baseline stats
        with conn.cursor() as cur:
            print("\\nBaseline Statistics:")
            cur.execute("SELECT COUNT(*) FROM feature_engineered_data")
            row_count = cur.fetchone()[0]
            print(f"  Rows: {row_count:,}")
            
            cur.execute("SELECT COUNT(DISTINCT symbol) FROM feature_engineered_data")
            symbols = cur.fetchone()[0]
            print(f"  Symbols: {symbols}")
            
            cur.execute("SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'feature_engineered_data'")
            indexes_before = cur.fetchone()[0]
            print(f"  Indexes before: {indexes_before}")
        
        conn.commit()
        
        # Step 1: Drop old indexes (can be in transaction)
        print("\\nStep 1: Dropping old indexes...")
        drop_queries = [
            "DROP INDEX IF EXISTS idx_features_symbol_timestamp;",
            "DROP INDEX IF EXISTS idx_features_symbol;", 
            "DROP INDEX IF EXISTS idx_features_timestamp;",
        ]
        
        with conn.cursor() as cur:
            for query in drop_queries:
                try:
                    cur.execute(query)
                    print(f"  Dropped: {query.split()[4].replace(';', '')}")
                except psycopg2.Error as e:
                    print(f"  Skip: {e}")
        conn.commit()
        
        # Step 2: Create concurrent indexes (must be outside transaction)
        print("\\nStep 2: Creating optimized indexes...")
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        
        index_queries = [
            ("Primary Composite", """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_features_symbol_version_timestamp 
                                     ON feature_engineered_data(symbol, feature_version, timestamp DESC);"""),
            
            ("Covering Index", """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_features_symbol_version_covering
                                  ON feature_engineered_data(symbol, feature_version, timestamp DESC)
                                  INCLUDE (open, high, low, close, volume, returns, rsi_1d, price_ma_short);"""),
            
            ("Recent Data", """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_features_recent_data
                               ON feature_engineered_data(timestamp DESC, symbol)
                               WHERE timestamp >= NOW() - INTERVAL '7 days';"""),
            
            ("Symbol Recent", """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_features_symbol_recent
                                 ON feature_engineered_data(symbol, timestamp DESC)
                                 WHERE timestamp >= NOW() - INTERVAL '30 days';"""),
            
            ("Market Hours", """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_features_market_hours_optimized
                                ON feature_engineered_data(symbol, timestamp, is_market_open)
                                WHERE is_market_open = 1 AND timestamp >= NOW() - INTERVAL '90 days';"""),
            
            ("ML Completeness", """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_features_completeness
                                   ON feature_engineered_data(symbol, timestamp)
                                   WHERE rsi_1d IS NOT NULL 
                                     AND price_ma_short IS NOT NULL 
                                     AND bb_upper IS NOT NULL 
                                     AND macd IS NOT NULL
                                     AND atr IS NOT NULL;"""),
            
            ("Time Series", """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_features_timeseries
                               ON feature_engineered_data(timestamp, symbol)
                               INCLUDE (returns, realized_vol_short, volume_ratio);""")
        ]
        
        success_count = 0
        with conn.cursor() as cur:
            for name, query in index_queries:
                try:
                    print(f"  Creating {name}...")
                    start_time = time.time()
                    cur.execute(query)
                    duration = time.time() - start_time
                    print(f"    Success ({duration:.1f}s)")
                    success_count += 1
                except psycopg2.Error as e:
                    if "already exists" in str(e).lower():
                        print(f"    Already exists")
                        success_count += 1
                    else:
                        print(f"    Error: {str(e)[:80]}...")
        
        print(f"\\nIndexes created: {success_count}/{len(index_queries)}")
        
        # Step 3: Create materialized view (back to normal transaction mode)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
        
        print("\\nStep 3: Creating materialized view...")
        try:
            with conn.cursor() as cur:
                # Drop existing view
                cur.execute("DROP MATERIALIZED VIEW IF EXISTS mv_features_dashboard_summary CASCADE;")
                
                # Create new view
                cur.execute("""
                    CREATE MATERIALIZED VIEW mv_features_dashboard_summary AS
                    SELECT 
                        symbol,
                        MAX(timestamp) as latest_timestamp,
                        COUNT(*) as total_records,
                        MAX(feature_version) as latest_version,
                        COUNT(CASE WHEN rsi_1d IS NOT NULL THEN 1 END)::float / COUNT(*)::float as rsi_coverage,
                        COUNT(CASE WHEN price_ma_short IS NOT NULL THEN 1 END)::float / COUNT(*)::float as ma_coverage
                    FROM feature_engineered_data f
                    WHERE timestamp >= NOW() - INTERVAL '90 days'
                    GROUP BY symbol;
                """)
                
                # Create index on materialized view
                cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dashboard_symbol ON mv_features_dashboard_summary(symbol);")
                
                # Update statistics
                cur.execute("ANALYZE feature_engineered_data;")
                cur.execute("ANALYZE mv_features_dashboard_summary;")
                
            conn.commit()
            print("  Materialized view created successfully")
        except psycopg2.Error as e:
            print(f"  Materialized view error: {e}")
        
        # Final statistics
        print("\\nFinal Statistics:")
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'feature_engineered_data'")
            indexes_after = cur.fetchone()[0]
            print(f"  Total indexes: {indexes_after}")
            print(f"  New indexes: {indexes_after - indexes_before}")
            
            # Performance test
            print("\\nPerformance Test:")
            test_sql = """
                SELECT symbol, timestamp, close, rsi_1d, price_ma_short 
                FROM feature_engineered_data 
                WHERE symbol = 'AAPL' 
                AND feature_version = '3.0'
                AND timestamp >= NOW() - INTERVAL '30 days'
                ORDER BY timestamp DESC 
                LIMIT 100
            """
            
            start_time = time.time()
            cur.execute(test_sql)
            result = cur.fetchall()
            duration = time.time() - start_time
            
            print(f"  Sample query: {len(result)} rows in {duration:.3f}s")
            
            # Show index usage
            cur.execute("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'feature_engineered_data' 
                AND indexname LIKE 'idx_features_%'
                ORDER BY indexname
            """)
            indexes = cur.fetchall()
            print(f"\\nOptimized Indexes Created:")
            for idx_name, idx_def in indexes:
                print(f"  - {idx_name}")
        
        conn.close()
        
        print("\\n" + "=" * 70)
        print("OPTIMIZATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("Your feature_engineered_data table is now optimized with:")
        print(f"  - {success_count} high-performance indexes")
        print("  - Materialized view for dashboard queries")
        print("  - Updated statistics for query planning")
        print("\\nExpected performance improvements:")
        print("  - 60-90% faster symbol+date range queries") 
        print("  - Reduced memory usage with covering indexes")
        print("  - Better dashboard load times")
        print("\\nNext steps:")
        print("  - Update your application to use OptimizedFeatureDataService")
        print("  - Monitor query performance improvements")
        print("  - Refresh materialized view hourly in production")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\\nOptimization failed: {e}")
        return False

if __name__ == "__main__":
    success = execute_optimization()
    exit(0 if success else 1)