-- Database Optimization for feature_engineered_data table
-- Addresses performance issues with large feature dataset queries

-- Drop existing suboptimal indexes if they exist
DROP INDEX IF EXISTS idx_features_symbol_timestamp;
DROP INDEX IF EXISTS idx_features_symbol;
DROP INDEX IF EXISTS idx_features_timestamp;

-- ============================================================================
-- PHASE 1: CORE PERFORMANCE INDEXES
-- ============================================================================

-- Primary composite index for most common query pattern
-- Covers: WHERE symbol = ? AND feature_version = ? AND timestamp >= ?
CREATE INDEX idx_features_symbol_version_timestamp 
ON feature_engineered_data(symbol, feature_version, timestamp DESC);

-- Cover index for symbol + version queries (includes commonly selected columns)
CREATE INDEX idx_features_symbol_version_covering
ON feature_engineered_data(symbol, feature_version, timestamp DESC)
INCLUDE (open, high, low, close, volume, returns, rsi_1d, price_ma_short);

-- Index for data availability queries
CREATE INDEX idx_features_availability
ON feature_engineered_data(symbol, feature_version, timestamp, rsi_1d, price_ma_short, bb_upper)
WHERE rsi_1d IS NOT NULL OR price_ma_short IS NOT NULL OR bb_upper IS NOT NULL;

-- ============================================================================
-- PHASE 2: SPECIALIZED INDEXES
-- ============================================================================

-- Recent data queries (dashboard real-time updates)
CREATE INDEX idx_features_recent_data
ON feature_engineered_data(timestamp DESC, symbol)
WHERE timestamp >= NOW() - INTERVAL '7 days';

-- Symbol-specific recent data
CREATE INDEX idx_features_symbol_recent
ON feature_engineered_data(symbol, timestamp DESC)
WHERE timestamp >= NOW() - INTERVAL '30 days';

-- Market hours filtering (for trading strategies)
CREATE INDEX idx_features_market_hours_optimized
ON feature_engineered_data(symbol, timestamp, is_market_open)
WHERE is_market_open = 1 AND timestamp >= NOW() - INTERVAL '90 days';

-- ============================================================================
-- PHASE 3: ANALYTICS & ML INDEXES  
-- ============================================================================

-- Feature completeness index (for ML pipeline validation)
CREATE INDEX idx_features_completeness
ON feature_engineered_data(symbol, timestamp)
WHERE rsi_1d IS NOT NULL 
  AND price_ma_short IS NOT NULL 
  AND bb_upper IS NOT NULL 
  AND macd IS NOT NULL
  AND atr IS NOT NULL;

-- Time-series analysis index
CREATE INDEX idx_features_timeseries
ON feature_engineered_data(timestamp, symbol)
INCLUDE (returns, realized_vol_short, volume_ratio);

-- ============================================================================
-- PHASE 4: MAINTENANCE INDEXES
-- ============================================================================

-- Index for cleanup/archiving operations
CREATE INDEX idx_features_cleanup
ON feature_engineered_data(created_at, symbol, timestamp);

-- Update tracking
CREATE INDEX idx_features_updates
ON feature_engineered_data(updated_at)
WHERE updated_at != created_at;

-- ============================================================================
-- PERFORMANCE STATISTICS UPDATE
-- ============================================================================

-- Update table statistics for better query planning
ANALYZE feature_engineered_data;

-- ============================================================================
-- QUERY OPTIMIZATION VIEWS
-- ============================================================================

-- Create materialized view for dashboard overview (updated hourly)
CREATE MATERIALIZED VIEW mv_features_dashboard_summary AS
SELECT 
    symbol,
    MAX(timestamp) as latest_timestamp,
    COUNT(*) as total_records,
    MAX(feature_version) as latest_version,
    -- Latest values for key indicators
    (SELECT rsi_1d FROM feature_engineered_data f1 
     WHERE f1.symbol = f.symbol 
     ORDER BY timestamp DESC LIMIT 1) as latest_rsi,
    (SELECT price_ma_short FROM feature_engineered_data f2 
     WHERE f2.symbol = f.symbol 
     ORDER BY timestamp DESC LIMIT 1) as latest_ma,
    -- Data quality metrics
    COUNT(CASE WHEN rsi_1d IS NOT NULL THEN 1 END)::float / COUNT(*)::float as rsi_coverage,
    COUNT(CASE WHEN price_ma_short IS NOT NULL THEN 1 END)::float / COUNT(*)::float as ma_coverage
FROM feature_engineered_data f
WHERE timestamp >= NOW() - INTERVAL '90 days'
GROUP BY symbol;

-- Index on materialized view
CREATE UNIQUE INDEX idx_mv_dashboard_symbol ON mv_features_dashboard_summary(symbol);

-- ============================================================================
-- COMMENTS & DOCUMENTATION
-- ============================================================================

COMMENT ON INDEX idx_features_symbol_version_timestamp IS 'Primary index for symbol+version+time range queries';
COMMENT ON INDEX idx_features_symbol_version_covering IS 'Covering index to avoid table lookups for common columns';
COMMENT ON INDEX idx_features_recent_data IS 'Partial index for dashboard real-time queries';
COMMENT ON INDEX idx_features_market_hours_optimized IS 'Trading hours data for strategy backtesting';
COMMENT ON MATERIALIZED VIEW mv_features_dashboard_summary IS 'Pre-aggregated dashboard metrics updated hourly';

-- Set up automatic refresh of materialized view
-- (This would typically be done via a scheduled job)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_features_dashboard_summary;