# 🗄️ Database Documentation

Welcome to the ML Trading System database documentation. This section provides comprehensive information about the database architecture, schema design, and operational procedures.

## 📊 **Current Database Status**

**Database**: PostgreSQL 17.0  
**Total Records**: 1,911,610+ feature engineering records  
**Symbols Tracked**: 1,057 unique symbols  
**Optimization Level**: **Production-optimized** with 9 specialized indexes  
**Query Performance**: Sub-millisecond for optimized queries ⚡

## 📚 **Documentation Sections**

### 🏗️ **[Database Schema](DATABASE_SCHEMA.md)**
Complete overview of all database tables, columns, and data types
- **11 core tables** + materialized views
- **4 main domains**: Market Data, Trading, Logging, System
- **100+ feature engineering columns** with detailed descriptions
- **Performance optimization** status and statistics

### 🔗 **[Entity Relationships](ENTITY_RELATIONSHIPS.md)**
Visual diagrams and relationship mappings between all database entities
- **Entity Relationship Diagrams** using Mermaid
- **Data flow patterns** and sequences
- **Foreign key relationships** and constraints
- **Growth patterns** and scaling considerations

### 🔧 **[Operations Guide](DATABASE_OPERATIONS.md)**
Comprehensive database administration and maintenance procedures
- **Performance monitoring** with real-time health checks
- **Routine maintenance** scripts (daily, weekly, monthly)
- **Backup and recovery** procedures
- **Query optimization** patterns and examples

### ⚡ **[Performance Optimization](FEATURE_TABLE_OPTIMIZATION.md)**
Detailed documentation of database performance improvements
- **88% faster** symbol+date range queries
- **79% faster** dashboard load times
- **70% reduction** in memory usage
- **9 specialized indexes** for different query patterns

### 🛠️ **[Troubleshooting Guide](DATABASE_TROUBLESHOOTING.md)**
Solutions for common database issues and problems
- **Connection problems** and authentication fixes
- **Performance issues** and slow query optimization
- **Error debugging** with diagnostic commands
- **Quick fixes** for common scenarios

## 🚀 **Quick Start**

### Check Database Health
```sql
-- Connect to database
psql -U postgres -d mltrading

-- Check basic stats
SELECT COUNT(*) FROM feature_engineered_data;
SELECT COUNT(DISTINCT symbol) FROM feature_engineered_data;
SELECT pg_size_pretty(pg_database_size('mltrading'));
```

### Apply Performance Optimizations
```bash
# Run optimization (if not already applied)
python run.py optimize-db

# Check optimization status
python scripts/optimize_feature_indexes_fixed.py
```

### Monitor Performance
```sql
-- Check index usage
SELECT indexname, idx_scan, idx_tup_read 
FROM pg_stat_user_indexes 
WHERE tablename = 'feature_engineered_data' 
ORDER BY idx_scan DESC;

-- Query performance test
EXPLAIN ANALYZE 
SELECT symbol, timestamp, close, rsi_1d 
FROM feature_engineered_data 
WHERE symbol = 'AAPL' 
AND timestamp >= NOW() - INTERVAL '7 days';
```

## 📈 **Key Performance Metrics**

| Metric | Before Optimization | After Optimization | Improvement |
|--------|--------------------|--------------------|-------------|
| **Symbol+Date Queries** | 2.5s | 0.000s | **88% faster** |
| **Dashboard Load** | 5.2s | 1.1s | **79% faster** |
| **Memory Usage** | 450MB | 135MB | **70% reduction** |
| **Cache Hit Rate** | 45% | 82% | **82% improvement** |
| **Database Connections** | 15-20 | 3-5 | **75% reduction** |

## 🔍 **Database Architecture Overview**

```mermaid
graph TB
    subgraph "Market Data Domain"
        MD[market_data<br/>📈 OHLCV Data]
        SI[stock_info<br/>📊 Symbol Info]
        FED[feature_engineered_data<br/>🧠 ML Features<br/>1.9M+ records]
        MV[mv_features_dashboard_summary<br/>⚡ Dashboard Cache]
    end
    
    subgraph "Trading Domain"
        O[orders<br/>📋 Trade Orders]
        F[fills<br/>✅ Executions]
        M[models<br/>🤖 ML Models]
        P[predictions<br/>🎯 Outputs]
    end
    
    subgraph "Logging Domain"
        SL[system_logs<br/>📝 App Logs]
        TL[trading_events<br/>💰 Events]
        PL[performance_logs<br/>⚡ Metrics]
        EL[error_logs<br/>❌ Errors]
    end
    
    MD --> FED
    SI --> MD
    FED --> MV
    M --> P
    O --> F
    
    classDef optimized fill:#e8f5e8,stroke:#4caf50,stroke-width:3px
    classDef highVolume fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    classDef monitoring fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    
    class FED,MV optimized
    class MD,SI highVolume
    class SL,TL,PL,EL monitoring
```

## 🎯 **Next Steps**

1. **Explore Schema**: Start with [Database Schema](DATABASE_SCHEMA.md) for table structure
2. **Understand Relationships**: Review [Entity Relationships](ENTITY_RELATIONSHIPS.md) for data flow
3. **Check Performance**: Use [Operations Guide](DATABASE_OPERATIONS.md) for monitoring
4. **Optimize Queries**: Apply patterns from [Performance Optimization](FEATURE_TABLE_OPTIMIZATION.md)
5. **Troubleshoot Issues**: Reference [Troubleshooting Guide](DATABASE_TROUBLESHOOTING.md) as needed

## 📊 **Database Statistics**

**Current Data Distribution**:
- **Market Data**: High-frequency OHLCV ingestion
- **Feature Engineering**: 100+ technical indicators per record
- **Trading Records**: Orders, fills, and executions
- **System Logs**: Comprehensive monitoring and error tracking
- **ML Models**: Predictions with confidence scores

**Growth Rate**:
- **~2M feature records/year** (1K symbols × 2K hours/year)
- **~500K market records/year** (base OHLCV data)
- **~10M log records/year** (system monitoring)

The database is designed for high-performance financial data processing with comprehensive monitoring and optimization for production trading scenarios.