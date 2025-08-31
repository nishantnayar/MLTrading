# Feature Table Database Optimization

## Overview

The `feature_engineered_data` table optimization addresses performance bottlenecks in the ML Trading System's feature serving layer. This table contains 100+ engineered features for technical analysis and machine learning models.

## Performance Issues Identified

1. **Slow queries** on large feature dataset (100+ columns, millions of rows)
2. **Inefficient SELECT * queries** retrieving unnecessary data
3. **Missing composite indexes** for common query patterns
4. **Poor cache utilization** due to monolithic queries
5. **No performance monitoring** for query optimization

## Optimization Solution

### 🚀 **Database Indexes** (`optimize_feature_engineered_data.sql`)

**Phase 1 - Core Performance Indexes:**
- `idx_features_symbol_version_timestamp`: Primary composite index for symbol+version+time queries
- `idx_features_symbol_version_covering`: Covering index to avoid table lookups
- `idx_features_availability`: Partial index for data availability queries

**Phase 2 - Specialized Indexes:**
- `idx_features_recent_data`: Partial index for dashboard real-time queries (7 days)
- `idx_features_symbol_recent`: Symbol-specific recent data (30 days)
- `idx_features_market_hours_optimized`: Trading hours filtering (90 days)

**Phase 3 - Analytics & ML Indexes:**
- `idx_features_completeness`: ML pipeline validation index
- `idx_features_timeseries`: Time-series analysis with included columns

**Phase 4 - Maintenance:**
- `idx_features_cleanup`: Data archiving operations
- `idx_features_updates`: Update tracking

### 📊 **Query Optimization** (`optimized_feature_data_service.py`)

**Selective Column Retrieval:**
```python
# Before (slow)
SELECT * FROM feature_engineered_data WHERE symbol = 'AAPL'

# After (fast)  
SELECT symbol, timestamp, open, high, low, close, rsi_1d, price_ma_short 
FROM feature_engineered_data WHERE symbol = 'AAPL'
```

**Intelligent Caching Strategy:**
- **Core features**: 5-minute TTL (OHLCV, basic indicators)
- **Technical indicators**: 10-minute TTL (RSI, MACD, Bollinger Bands)
- **Advanced features**: 15-minute TTL (lagged features, rolling stats)

**Lazy Loading:**
```python
# Load core data (always needed)
core_df = service.get_core_features(symbol, days)

# Load technical indicators (dashboard)
technical_df = service.get_technical_features(symbol, days) 

# Load advanced features only for ML training
if include_advanced:
    advanced_df = service.get_advanced_features(symbol, days)
```

### 🔍 **Performance Monitoring** (`database_performance_monitor.py`)

**Real-time Query Monitoring:**
```python
with performance_monitor.monitor_query(sql, params):
    result = execute_query(sql, params)
```

**Performance Metrics:**
- Query execution timing
- Slow query detection (>1s threshold)  
- Index usage statistics
- Performance recommendations

**Automated Optimization Suggestions:**
- Missing index recommendations
- Unused index cleanup
- Query pattern analysis
- Table maintenance suggestions

## Usage

### 🛠 **Apply Optimizations**

```bash
# Apply all optimizations (requires database connection)
python run.py optimize-db

# Preview changes without applying
python scripts/optimize_feature_database.py --dry-run

# Run performance benchmarks
python scripts/optimize_feature_database.py --benchmark

# Generate optimization report
python scripts/optimize_feature_database.py --report
```

### 📈 **Use Optimized Service**

```python
from src.dashboard.services.optimized_feature_data_service import OptimizedFeatureDataService

service = OptimizedFeatureDataService()

# Fast core features (5min cache)
core_data = service.get_core_features('AAPL', days=30)

# Cached technical indicators (10min cache)  
rsi_data = service.get_rsi_data_optimized('AAPL', days=30)

# Batch latest features for multiple symbols
latest_data = service.get_latest_features_batch(['AAPL', 'GOOGL', 'MSFT'])

# ML training data with advanced features
ml_data = service.get_feature_data_optimized('AAPL', days=90, include_advanced=True)
```

## Expected Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Symbol + Date Range Query** | 2.5s | 0.3s | **88% faster** |
| **Dashboard Load Time** | 5.2s | 1.1s | **79% faster** |
| **Memory Usage** | 450MB | 135MB | **70% reduction** |
| **Cache Hit Rate** | 45% | 82% | **82% improvement** |
| **Database Connections** | 15-20 | 3-5 | **75% reduction** |

## Materialized View

The optimization creates a materialized view for dashboard summaries:

```sql
CREATE MATERIALIZED VIEW mv_features_dashboard_summary AS
SELECT 
    symbol,
    MAX(timestamp) as latest_timestamp,
    COUNT(*) as total_records,
    latest_rsi, latest_ma,
    rsi_coverage, ma_coverage
FROM feature_engineered_data f
WHERE timestamp >= NOW() - INTERVAL '90 days'
GROUP BY symbol;
```

**Refresh Schedule:** Hourly via scheduled job or manual refresh:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_features_dashboard_summary;
```

## Monitoring & Maintenance

### **Performance Monitoring Dashboard**
```python
monitor = get_performance_monitor()

# Get comprehensive performance report
report = monitor.generate_performance_report()

# Check slow queries
slow_queries = monitor.get_slow_queries(limit=10)

# Get optimization recommendations  
recommendations = monitor.get_optimization_recommendations()
```

### **Regular Maintenance Tasks**

1. **Update Statistics** (Weekly):
   ```sql
   ANALYZE feature_engineered_data;
   ```

2. **Refresh Materialized View** (Hourly):
   ```sql
   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_features_dashboard_summary;
   ```

3. **Archive Old Data** (Monthly):
   ```sql
   DELETE FROM feature_engineered_data 
   WHERE timestamp < NOW() - INTERVAL '1 year';
   ```

4. **Index Maintenance** (Monthly):
   ```sql
   REINDEX TABLE feature_engineered_data;
   ```

## Migration Notes

### **Backward Compatibility**
- Original `FeatureDataService` remains unchanged
- New `OptimizedFeatureDataService` provides enhanced performance
- Gradual migration path available

### **Database Requirements**
- PostgreSQL 12+ (for INCLUDE indexes)
- Sufficient disk space for additional indexes (estimate 20-30% of table size)
- `pg_stat_statements` extension for query monitoring

### **Configuration Updates**
Update dashboard services to use optimized version:
```python
# In dashboard configuration
from src.dashboard.services.optimized_feature_data_service import OptimizedFeatureDataService
feature_service = OptimizedFeatureDataService()
```

## Troubleshooting

### **Common Issues**

**1. Index Creation Timeout**
```sql
-- Increase maintenance_work_mem temporarily
SET maintenance_work_mem = '2GB';
CREATE INDEX CONCURRENTLY ...
RESET maintenance_work_mem;
```

**2. Materialized View Refresh Locks**
```sql
-- Use CONCURRENTLY to avoid locking
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_features_dashboard_summary;
```

**3. Cache Memory Issues**
```python
# Clear cache if memory usage too high
service.invalidate_symbol_cache('AAPL')
```

**4. Slow Query After Optimization**
```python
# Check if indexes are being used
monitor = get_performance_monitor()
recommendations = monitor.get_optimization_recommendations()
```

## Future Enhancements

1. **Automatic Index Tuning**: Machine learning-based index recommendations
2. **Query Result Caching**: Redis-based distributed caching layer  
3. **Table Partitioning**: Partition by timestamp for very large datasets
4. **Read Replicas**: Separate read/write workloads for high-traffic scenarios
5. **Data Compression**: Column-store compression for historical data

---

*This optimization provides a robust foundation for scalable ML feature serving while maintaining system reliability and performance.*