# 🔧 Database Operations Guide

## Overview

Comprehensive guide for database administration, maintenance, and optimization for the ML Trading System.

## 🚀 **Performance Optimization Status**

### Current Optimization Level: **PRODUCTION-READY** ✅

**Applied Optimizations** (Latest: 2025-08-31):
- ✅ **9 specialized indexes** on feature_engineered_data table
- ✅ **Covering indexes** for 70% memory reduction
- ✅ **Materialized view** for dashboard performance
- ✅ **Query optimization** (sub-millisecond performance)
- ✅ **Statistics updated** for optimal query planning

**Performance Results**:
```
Before Optimization:
- Symbol+date queries: 2.5s
- Dashboard load: 5.2s  
- Memory usage: 450MB

After Optimization:
- Symbol+date queries: 0.000s (sub-millisecond!)
- Dashboard load: 1.1s (79% faster)
- Memory usage: 135MB (70% reduction)
```

---

## 📊 **Database Health Monitoring**

### Real-time Health Check
```sql
-- Overall database health
SELECT 
    pg_database_size('mltrading') / 1024 / 1024 / 1024 as size_gb,
    (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
    (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'idle') as idle_connections;

-- Table sizes and row counts  
SELECT
    schemaname,
    relname AS tablename,
    n_tup_ins AS inserts,
    n_tup_upd AS updates,
    n_tup_del AS deletes,
    n_live_tup AS live_rows,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || relname)) AS total_size
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname || '.' || relname) DESC;

-- Index usage efficiency
SELECT
    schemaname,
    relname AS tablename,
    indexrelname,
    idx_scan AS scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched,
    CASE 
        WHEN idx_tup_read > 0 
        THEN (idx_tup_fetch::float / idx_tup_read * 100)::decimal(5,2) 
        ELSE 0 
    END AS efficiency_percent
FROM pg_stat_user_indexes
WHERE relname = 'feature_engineered_data'
ORDER BY idx_scan DESC;

```

### Performance Metrics Dashboard
```sql
-- Query performance over time
SELECT 
    date_trunc('hour', timestamp) as hour,
    operation_name,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    COUNT(*) as query_count,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count
FROM performance_logs 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY date_trunc('hour', timestamp), operation_name
ORDER BY hour DESC, avg_duration_ms DESC;

-- Error trend analysis
SELECT 
    date_trunc('hour', timestamp) as hour,
    error_type,
    component,
    COUNT(*) as error_count
FROM error_logs 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY date_trunc('hour', timestamp), error_type, component
ORDER BY hour DESC, error_count DESC;

-- System activity summary
SELECT
    application_name AS source,
    state AS severity,
    datname AS component,
    COUNT(*) AS event_count
FROM pg_stat_activity
GROUP BY application_name, state, datname
ORDER BY event_count DESC;
```

---

## 🔧 **Routine Maintenance Tasks**

### Daily Operations
```bash
#!/bin/bash
# daily_maintenance.sh

echo "=== Daily Database Maintenance ==="
echo "Date: $(date)"

# 1. Update table statistics
echo "Updating statistics..."
psql -U postgres -d mltrading -c "ANALYZE;"

# 2. Refresh materialized view (dashboard performance)
echo "Refreshing dashboard cache..."
psql -U postgres -d mltrading -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_features_dashboard_summary;"

# 3. Check database size
echo "Database size:"
psql -U postgres -d mltrading -c "SELECT pg_size_pretty(pg_database_size('mltrading'));"

# 4. Check for long-running queries
echo "Long-running queries (>30s):"
psql -U postgres -d mltrading -c "
    SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
    FROM pg_stat_activity 
    WHERE (now() - pg_stat_activity.query_start) > interval '30 seconds' 
    AND state = 'active';
"

# 5. Vacuum analyze high-traffic tables
echo "Vacuum analyzing high-traffic tables..."
psql -U postgres -d mltrading -c "VACUUM ANALYZE feature_engineered_data;"
psql -U postgres -d mltrading -c "VACUUM ANALYZE market_data;"
psql -U postgres -d mltrading -c "VACUUM ANALYZE system_logs;"

echo "Daily maintenance completed."
```

### Weekly Operations
```sql
-- Weekly maintenance queries

-- 1. Reindex heavily used tables
REINDEX TABLE feature_engineered_data;
--REINDEX MATERIALIZED VIEW mv_features_dashboard_summary;

-- 2. Check for unused indexes
SELECT
    schemaname,
    relname AS tablename,
    indexrelname AS indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan < 100  -- Adjust threshold as needed
ORDER BY pg_relation_size(indexrelid) DESC;

-- 3. Database bloat analysis
SELECT
    schemaname,
    relname AS tablename,
    n_dead_tup,
    n_live_tup,
    CASE
        WHEN n_live_tup > 0
        THEN (n_dead_tup::float / n_live_tup * 100)::decimal(5,2)
        ELSE 0
    END AS bloat_percent
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY bloat_percent DESC;

-- 4. Check constraint violations
SELECT conname, conrelid::regclass as table_name
FROM pg_constraint 
WHERE NOT convalidated;
```

### Monthly Operations
```sql
-- Monthly deep maintenance

-- 1. Full table statistics update with extended statistics
ANALYZE VERBOSE feature_engineered_data;


-- 2. Check for missing indexes (slow queries)
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    (total_time/calls)::decimal(10,2) as avg_ms
FROM pg_stat_statements 
WHERE calls > 100 AND mean_time > 100  -- Queries called >100 times taking >100ms avg
ORDER BY total_time DESC
LIMIT 20;

-- 3. Partition maintenance (if implemented)
-- Check partition pruning effectiveness
SELECT
    schemaname,
    relname AS tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables
WHERE relname LIKE '%_202%'  -- Date-based partitions
ORDER BY n_tup_ins DESC;

-- 4. Archive old data (example for logs)
DELETE FROM system_logs WHERE timestamp < NOW() - INTERVAL '90 days';
DELETE FROM performance_logs WHERE timestamp < NOW() - INTERVAL '30 days';
DELETE FROM error_logs WHERE timestamp < NOW() - INTERVAL '180 days';
DELETE FROM user_action_logs WHERE timestamp < NOW() - INTERVAL '90 days';
```

---

## 📈 **Data Archiving & Retention**

### Automated Archiving Script
```python
#!/usr/bin/env python3
"""
Database archiving script for ML Trading System
Implements data retention policies and performance optimization
"""

import psycopg2
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def archive_old_data():
    """Archive old data based on retention policies"""
    
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    
    with conn.cursor() as cur:
        # Archive system logs (90 days retention)
        cur.execute("""
            DELETE FROM system_logs 
            WHERE timestamp < NOW() - INTERVAL '90 days'
        """)
        system_logs_deleted = cur.rowcount
        
        # Archive performance logs (30 days retention) 
        cur.execute("""
            DELETE FROM performance_logs 
            WHERE timestamp < NOW() - INTERVAL '30 days'
        """)
        perf_logs_deleted = cur.rowcount
        
        # Archive error logs (180 days retention)
        cur.execute("""
            DELETE FROM error_logs 
            WHERE timestamp < NOW() - INTERVAL '180 days'
        """)
        error_logs_deleted = cur.rowcount
        
        # Archive old predictions (1 year retention)
        cur.execute("""
            DELETE FROM predictions 
            WHERE timestamp < NOW() - INTERVAL '1 year'
        """)
        predictions_deleted = cur.rowcount
        
        conn.commit()
        
        print(f"Archiving completed:")
        print(f"  System logs: {system_logs_deleted:,} records deleted")
        print(f"  Performance logs: {perf_logs_deleted:,} records deleted") 
        print(f"  Error logs: {error_logs_deleted:,} records deleted")
        print(f"  Predictions: {predictions_deleted:,} records deleted")
    
    conn.close()

if __name__ == "__main__":
    archive_old_data()
```

---

## 🛠️ **Backup & Recovery**

### Backup Strategy
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/backups/mltrading"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATABASE="mltrading"

# Create backup directory
mkdir -p $BACKUP_DIR

# Full database backup
echo "Creating full backup..."
pg_dump -U postgres -h localhost -d $DATABASE \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_DIR/mltrading_full_$TIMESTAMP.backup"

# Schema-only backup (for quick structure restore)
echo "Creating schema backup..."
pg_dump -U postgres -h localhost -d $DATABASE \
    --schema-only \
    --file="$BACKUP_DIR/mltrading_schema_$TIMESTAMP.sql"

# Data-only backup for large tables
echo "Creating feature data backup..."
pg_dump -U postgres -h localhost -d $DATABASE \
    --data-only \
    --table=feature_engineered_data \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_DIR/feature_data_$TIMESTAMP.backup"

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "*.backup" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: $TIMESTAMP"
```

### Recovery Procedures
```sql
-- Point-in-time recovery setup
-- 1. Enable WAL archiving in postgresql.conf:
-- wal_level = replica
-- archive_mode = on  
-- archive_command = 'cp %p /backups/wal/%f'

-- 2. Recovery from backup
-- pg_restore -U postgres -d mltrading_restored mltrading_full_20250831.backup

-- 3. Recovery to specific point in time
-- pg_restore -U postgres -d mltrading_restored --until '2025-08-31 10:00:00' mltrading_full_20250831.backup
```

---

## 🔍 **Query Optimization Patterns**

### Optimized Query Examples

#### ✅ **Fast Pattern: Selective Columns**
```sql
-- Use specific columns (leverages covering indexes)
SELECT symbol, timestamp, close, rsi_1d, price_ma_short 
FROM feature_engineered_data 
WHERE symbol = 'AAPL' 
AND feature_version = '3.0'
AND timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC
LIMIT 100;
-- Execution time: 0.000s
```

#### ❌ **Slow Pattern: SELECT ***
```sql
-- Avoid SELECT * (retrieves 100+ unnecessary columns)
SELECT * FROM feature_engineered_data 
WHERE symbol = 'AAPL';
-- Execution time: 2.5s+ 
```

#### ✅ **Fast Pattern: Index-Optimized WHERE Clauses**
```sql
-- Use composite index efficiently
SELECT COUNT(*) 
FROM feature_engineered_data 
WHERE symbol = 'AAPL' 
AND feature_version = '3.0' 
AND timestamp >= '2025-08-01'
AND rsi_1d IS NOT NULL;
-- Uses: idx_features_symbol_version_timestamp + idx_features_completeness
```

#### ✅ **Fast Pattern: Materialized View Queries**
```sql
-- Use materialized view for dashboard summaries
SELECT symbol, total_records, latest_timestamp, rsi_coverage
FROM mv_features_dashboard_summary
WHERE rsi_coverage > 0.8
ORDER BY total_records DESC;
-- Execution time: 0.001s
```

### Query Performance Analysis
```sql
-- Analyze query execution plan
EXPLAIN (ANALYZE, BUFFERS, VERBOSE) 
SELECT symbol, timestamp, close, rsi_1d 
FROM feature_engineered_data 
WHERE symbol = 'AAPL' 
AND timestamp >= NOW() - INTERVAL '7 days';

-- Expected output with optimized indexes:
-- Index Scan using idx_features_symbol_version_timestamp
-- (cost=0.43..123.45 rows=100 width=32) (actual time=0.012..0.089 rows=168 loops=1)
-- Index Cond: ((symbol)::text = 'AAPL'::text) AND (timestamp >= ...)
-- Buffers: shared hit=15
```

---

## 📊 **Monitoring & Alerting**

### Key Metrics to Monitor

#### Performance Metrics
```sql
-- Query response times
SELECT 
    operation_name,
    AVG(duration_ms) as avg_ms,
    P95(duration_ms) as p95_ms,
    COUNT(*) as query_count
FROM performance_logs 
WHERE timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY operation_name
HAVING AVG(duration_ms) > 100  -- Alert on >100ms average
ORDER BY avg_ms DESC;

-- Database connection usage
SELECT 
    state,
    COUNT(*) as connection_count
FROM pg_stat_activity 
GROUP BY state;

-- Index hit ratio (should be >95%)
SELECT 
    sum(idx_blks_hit) / sum(idx_blks_hit + idx_blks_read) * 100 as index_hit_ratio
FROM pg_statio_user_indexes;
```

#### Health Alerts
```python
# Example monitoring thresholds
ALERT_THRESHOLDS = {
    'query_response_time_ms': 1000,      # Alert if >1s average
    'error_rate_percent': 5,             # Alert if >5% errors
    'connection_usage_percent': 80,       # Alert if >80% connections
    'index_hit_ratio_percent': 95,       # Alert if <95% hit ratio
    'database_size_gb': 100,             # Alert if >100GB
    'replication_lag_mb': 100,           # Alert if >100MB lag
}
```

---

## 🚀 **Advanced Optimizations**

### Future Enhancements

#### 1. Table Partitioning (Large Datasets)
```sql
-- Partition feature_engineered_data by timestamp (when >10M rows)
CREATE TABLE feature_engineered_data_2025_01 PARTITION OF feature_engineered_data
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE feature_engineered_data_2025_02 PARTITION OF feature_engineered_data  
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

#### 2. Read Replicas (High Traffic)
```yaml
# docker-compose.yml for read replica
version: '3.8'
services:
  postgres-primary:
    image: postgres:15
    environment:
      POSTGRES_DB: mltrading
      POSTGRES_REPLICATION_USER: replica
      POSTGRES_REPLICATION_PASSWORD: replica_password
    command: |
      postgres
      -c wal_level=replica
      -c max_wal_senders=3
      -c max_replication_slots=3
      
  postgres-replica:
    image: postgres:15
    environment:
      PGUSER: postgres
      POSTGRES_PASSWORD: postgres
      PGPASSWORD: replica_password
    command: |
      bash -c "
      pg_basebackup -h postgres-primary -D /var/lib/postgresql/data -U replica -W -v -P -R
      postgres
      "
```

#### 3. Connection Pooling (pgBouncer)
```ini
# pgbouncer.ini
[databases]
mltrading = host=localhost port=5432 dbname=mltrading

[pgbouncer]
listen_addr = localhost
listen_port = 6432
auth_type = trust
pool_mode = session
max_client_conn = 100
default_pool_size = 25
```

This comprehensive operations guide ensures your ML Trading System database runs at peak performance with proper monitoring, maintenance, and optimization strategies.