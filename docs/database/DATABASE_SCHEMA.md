# 📊 ML Trading System Database Schema

## Overview

The ML Trading System uses PostgreSQL as its primary database, designed for high-performance financial data processing, machine learning feature engineering, and comprehensive system monitoring.

### Database Statistics
- **Total Tables**: 11 core tables + 1 materialized view
- **Current Data Volume**: 1.9M+ feature engineering records across 1,057 symbols
- **Optimization Level**: Production-optimized with 9 specialized indexes
- **Extensions**: UUID-OSSP for unique identifiers

## 🏗️ **Core Architecture**

The database schema is organized into four main domains:

```mermaid
graph TB
    subgraph "Market Data Domain"
        MD[market_data]
        SI[stock_info]
        FED[feature_engineered_data]
        MV[mv_features_dashboard_summary]
    end
    
    subgraph "Trading Domain"
        O[orders]
        F[fills]
        M[models]
        P[predictions]
    end
    
    subgraph "Logging Domain"
        SL[system_logs]
        TL[trading_events]
        PL[performance_logs]
        EL[error_logs]
        UAL[user_action_logs]
    end
    
    subgraph "System Domain"
        UV[recent_system_activity]
    end
    
    MD --> FED
    SI --> MD
    O --> F
    M --> P
    FED --> MV
    SL --> UV
    TL --> UV
    PL --> UV
    EL --> UV
```

---

## 📈 **Market Data Domain**

### `market_data` - Core Market Data
**Purpose**: Primary OHLCV data storage for all symbols
```sql
CREATE TABLE market_data (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(10,4),
    high DECIMAL(10,4),
    low DECIMAL(10,4), 
    close DECIMAL(10,4),
    volume BIGINT,
    source VARCHAR(20) DEFAULT 'yahoo',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, timestamp, source)
);
```

**Key Features**:
- **Volume**: High-frequency data ingestion
- **Sources**: Yahoo Finance (primary), Alpaca, Polygon
- **Constraints**: Unique per symbol+timestamp+source
- **Indexes**: Optimized for symbol+timestamp queries

### `stock_info` - Symbol Metadata
**Purpose**: Company information, sector, and industry classification
```sql
CREATE TABLE stock_info (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    country VARCHAR(50),
    currency VARCHAR(10),
    exchange VARCHAR(20),
    source VARCHAR(20) DEFAULT 'yahoo',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Key Features**:
- **Enrichment**: Sector/industry classification for filtering
- **Global Support**: Multi-currency and exchange support
- **Auto-Update**: Triggers maintain updated_at timestamp

### `feature_engineered_data` - ML Features (⭐ Optimized)
**Purpose**: 100+ engineered features for ML models and technical analysis
```sql
CREATE TABLE feature_engineered_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    -- OHLCV base data
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    -- 90+ engineered features including:
    -- - Price features: returns, log_returns, price_acceleration
    -- - Technical indicators: RSI (multiple timeframes), MACD, Bollinger Bands
    -- - Volatility measures: realized volatility, Garman-Klass, ATR
    -- - Volume indicators: VPT, MFI, volume ratios
    -- - Time features: hour, day_of_week, market_open indicators
    -- - Lagged features: 1, 2, 4, 8, 24 period lags
    -- - Rolling statistics: 6h, 12h, 24h windows
    rsi_1d DOUBLE PRECISION,
    price_ma_short DOUBLE PRECISION,
    bb_upper DOUBLE PRECISION,
    macd DOUBLE PRECISION,
    atr DOUBLE PRECISION,
    -- ... (100+ total columns)
    feature_version VARCHAR(20) DEFAULT '3.0',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_symbol_timestamp_features UNIQUE (symbol, timestamp, source)
);
```

**Performance Optimization** (✅ Applied):
- **9 specialized indexes** for different query patterns
- **Covering indexes** reduce table lookups by 70%
- **Partial indexes** for recent data and market hours
- **Composite indexes** for symbol+version+timestamp queries

**Current Stats**:
- **Rows**: 1,911,610 feature records
- **Symbols**: 1,057 unique symbols
- **Query Performance**: Sub-millisecond for optimized queries

### `mv_features_dashboard_summary` - Dashboard Cache
**Purpose**: Materialized view for high-performance dashboard queries
```sql
CREATE MATERIALIZED VIEW mv_features_dashboard_summary AS
SELECT 
    symbol,
    MAX(timestamp) as latest_timestamp,
    COUNT(*) as total_records,
    MAX(feature_version) as latest_version,
    COUNT(CASE WHEN rsi_1d IS NOT NULL THEN 1 END)::float / COUNT(*)::float as rsi_coverage,
    COUNT(CASE WHEN price_ma_short IS NOT NULL THEN 1 END)::float / COUNT(*)::float as ma_coverage
FROM feature_engineered_data
WHERE timestamp >= NOW() - INTERVAL '90 days'
GROUP BY symbol;
```

**Refresh Strategy**: Hourly updates for dashboard performance

---

## 💼 **Trading Domain**

### `orders` - Order Management
**Purpose**: Track all trading orders across strategies
```sql
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity INTEGER NOT NULL,
    order_type VARCHAR(10) NOT NULL DEFAULT 'market',
    price DECIMAL(10,4),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    strategy VARCHAR(50),
    model_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Order Lifecycle**: pending → filled/cancelled/rejected

### `fills` - Execution Records
**Purpose**: Track actual trade executions and commissions
```sql
CREATE TABLE fills (
    id BIGSERIAL PRIMARY KEY,
    fill_id VARCHAR(50) UNIQUE NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,4) NOT NULL,
    commission DECIMAL(10,4) DEFAULT 0,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
```

**Relationship**: Many fills can belong to one order (partial fills)

### `models` - ML Model Registry
**Purpose**: Version control and metadata for ML models
```sql
CREATE TABLE models (
    id BIGSERIAL PRIMARY KEY,
    model_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    parameters JSONB,
    metrics JSONB,
    file_path VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**JSON Fields**:
- **parameters**: Model hyperparameters
- **metrics**: Performance metrics (accuracy, precision, recall, etc.)

### `predictions` - Model Outputs
**Purpose**: Store ML model predictions with confidence scores
```sql
CREATE TABLE predictions (
    id BIGSERIAL PRIMARY KEY,
    prediction_id VARCHAR(50) UNIQUE NOT NULL,
    model_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    prediction_type VARCHAR(20) NOT NULL,
    prediction_value DECIMAL(10,4),
    confidence DECIMAL(5,4),
    features JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (model_id) REFERENCES models(model_id)
);
```

**Prediction Types**: price_direction, volatility, momentum, etc.

---

## 📊 **Logging Domain**

### `system_logs` - Application Logs
**Purpose**: Centralized logging for all system components
```sql
CREATE TABLE system_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    level VARCHAR(20) NOT NULL,
    logger_name VARCHAR(100) NOT NULL,
    correlation_id VARCHAR(50),
    message TEXT NOT NULL,
    module VARCHAR(100),
    function_name VARCHAR(100),
    line_number INTEGER,
    thread_name VARCHAR(100),
    process_id INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### `trading_events` - Trading Activity Log
**Purpose**: Audit trail for all trading-related events
```sql
CREATE TABLE trading_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(20),
    side VARCHAR(10),
    quantity DECIMAL(15,6),
    price DECIMAL(15,6),
    order_id VARCHAR(100),
    strategy VARCHAR(50),
    correlation_id VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Event Types**: order_placed, order_filled, signal_generated, strategy_started, etc.

### `performance_logs` - Performance Monitoring
**Purpose**: Track system performance metrics
```sql
CREATE TABLE performance_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    operation_name VARCHAR(100) NOT NULL,
    duration_ms DECIMAL(10,3) NOT NULL,
    status VARCHAR(20) NOT NULL,
    component VARCHAR(50),
    correlation_id VARCHAR(50),
    memory_usage_mb DECIMAL(10,2),
    cpu_usage_percent DECIMAL(5,2),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Metrics**: Query execution times, memory usage, CPU utilization

### `error_logs` - Error Tracking
**Purpose**: Detailed error tracking with stack traces
```sql
CREATE TABLE error_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    component VARCHAR(50),
    correlation_id VARCHAR(50),
    user_id VARCHAR(50),
    request_path VARCHAR(200),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Error Types**: ConnectionError, ValidationError, ModelError, etc.

### `user_action_logs` - User Activity
**Purpose**: Track dashboard and API interactions
```sql
CREATE TABLE user_action_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    action_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    request_path VARCHAR(200),
    request_method VARCHAR(10),
    response_status INTEGER,
    duration_ms DECIMAL(10,3),
    correlation_id VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Action Types**: page_view, button_click, api_call, export_data, etc.

---

## 🔍 **System Views**

### `recent_system_activity` - Unified Activity View
**Purpose**: Combined view of all system activity from the last 24 hours
```sql
CREATE VIEW recent_system_activity AS
-- Combines data from:
-- - system_logs (application logs)
-- - trading_events (trading activity)
-- - performance_logs (performance metrics)
-- - error_logs (error tracking)
-- Ordered by timestamp DESC for recent-first display
```

**Usage**: Dashboard monitoring, system health checks, debugging

---

## 🚀 **Performance Optimizations**

### Index Strategy
The database uses a comprehensive indexing strategy:

**Core Indexes (Applied ✅)**:
- `idx_features_symbol_version_timestamp` - Primary composite index
- `idx_features_symbol_version_covering` - Covering index with commonly queried columns
- `idx_features_completeness` - ML pipeline validation
- `idx_features_timeseries` - Time-series analysis with included columns

**Performance Results**:
- **Symbol+Date Queries**: 0.000s (sub-millisecond)
- **Dashboard Load**: 79% faster with materialized view
- **Memory Usage**: 70% reduction with covering indexes

### Query Optimization Patterns
```sql
-- Optimized query pattern (FAST)
SELECT symbol, timestamp, close, rsi_1d, price_ma_short 
FROM feature_engineered_data 
WHERE symbol = 'AAPL' 
AND feature_version = '3.0'
AND timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC;

-- Avoid: SELECT * (retrieves 100+ unnecessary columns)
```

---

## 🔧 **Maintenance & Operations**

### Data Retention Policies
- **feature_engineered_data**: Retain 2+ years for ML training
- **market_data**: Permanent retention
- **system_logs**: 90 days retention
- **performance_logs**: 30 days retention
- **error_logs**: 180 days retention

### Backup Strategy
- **Full Backup**: Daily
- **Incremental**: Every 4 hours
- **Transaction Log**: Continuous

### Monitoring Queries
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('mltrading'));

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes WHERE tablename = 'feature_engineered_data' ORDER BY idx_scan DESC;

-- Recent system activity
SELECT COUNT(*), level FROM system_logs WHERE timestamp >= NOW() - INTERVAL '24 hours' GROUP BY level;
```

---

## 🔗 **Entity Relationships**

### Primary Relationships
- `orders` → `fills` (1:Many) via order_id
- `models` → `predictions` (1:Many) via model_id
- `stock_info` → `market_data` (1:Many) via symbol
- `market_data` → `feature_engineered_data` (1:1) via symbol+timestamp

### Data Flow
1. **Market Data Ingestion**: Yahoo Finance → `market_data`
2. **Symbol Enrichment**: Company info → `stock_info`
3. **Feature Engineering**: `market_data` → `feature_engineered_data`
4. **ML Predictions**: `feature_engineered_data` + `models` → `predictions`
5. **Trading Signals**: `predictions` → `orders` → `fills`
6. **System Monitoring**: All operations → logging tables

---

This schema supports high-frequency trading, comprehensive ML feature engineering, and production-grade system monitoring with optimized performance for financial data processing.