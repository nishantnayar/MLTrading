-- Create tables for logging system
-- This extends the existing database schema with logging capabilities

-- Main system logs table
CREATE TABLE IF NOT EXISTS system_logs (
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

-- Trading-specific events table
CREATE TABLE IF NOT EXISTS trading_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL, -- 'order_placed', 'order_filled', 'signal_generated', etc.
    symbol VARCHAR(20),
    side VARCHAR(10), -- 'buy', 'sell'
    quantity DECIMAL(15,6),
    price DECIMAL(15,6),
    order_id VARCHAR(100),
    strategy VARCHAR(50),
    correlation_id VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    operation_name VARCHAR(100) NOT NULL,
    duration_ms DECIMAL(10,3) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'success', 'error', 'timeout'
    component VARCHAR(50),
    correlation_id VARCHAR(50),
    memory_usage_mb DECIMAL(10,2),
    cpu_usage_percent DECIMAL(5,2),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Error tracking table
CREATE TABLE IF NOT EXISTS error_logs (
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

-- User actions table (for dashboard/API interactions)
CREATE TABLE IF NOT EXISTS user_action_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    action_type VARCHAR(50) NOT NULL, -- 'page_view', 'button_click', 'api_call', etc.
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

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_logger ON system_logs(logger_name);
CREATE INDEX IF NOT EXISTS idx_system_logs_correlation ON system_logs(correlation_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_trading_events_timestamp ON trading_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_trading_events_symbol ON trading_events(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_events_type ON trading_events(event_type);
CREATE INDEX IF NOT EXISTS idx_trading_events_correlation ON trading_events(correlation_id);

CREATE INDEX IF NOT EXISTS idx_performance_logs_timestamp ON performance_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_logs_operation ON performance_logs(operation_name);
CREATE INDEX IF NOT EXISTS idx_performance_logs_component ON performance_logs(component);
CREATE INDEX IF NOT EXISTS idx_performance_logs_correlation ON performance_logs(correlation_id);

CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_error_logs_type ON error_logs(error_type);
CREATE INDEX IF NOT EXISTS idx_error_logs_component ON error_logs(component);
CREATE INDEX IF NOT EXISTS idx_error_logs_correlation ON error_logs(correlation_id);

CREATE INDEX IF NOT EXISTS idx_user_action_logs_timestamp ON user_action_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_action_logs_action_type ON user_action_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_user_action_logs_user_id ON user_action_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_action_logs_correlation ON user_action_logs(correlation_id);

-- Create a view for recent system activity (last 24 hours)
CREATE OR REPLACE VIEW recent_system_activity AS
SELECT 
    'system_log' as source,
    timestamp,
    level as severity,
    logger_name as component,
    message as description,
    correlation_id,
    metadata
FROM system_logs 
WHERE timestamp >= NOW() - INTERVAL '24 hours'

UNION ALL

SELECT 
    'trading_event' as source,
    timestamp,
    'INFO' as severity,
    'trading' as component,
    event_type || ' - ' || COALESCE(symbol, 'N/A') as description,
    correlation_id,
    metadata
FROM trading_events 
WHERE timestamp >= NOW() - INTERVAL '24 hours'

UNION ALL

SELECT 
    'performance' as source,
    timestamp,
    CASE WHEN status = 'error' THEN 'ERROR' ELSE 'INFO' END as severity,
    component,
    operation_name || ' (' || duration_ms || 'ms)' as description,
    correlation_id,
    metadata
FROM performance_logs 
WHERE timestamp >= NOW() - INTERVAL '24 hours'

UNION ALL

SELECT 
    'error' as source,
    timestamp,
    'ERROR' as severity,
    component,
    error_type || ': ' || error_message as description,
    correlation_id,
    metadata
FROM error_logs 
WHERE timestamp >= NOW() - INTERVAL '24 hours'

ORDER BY timestamp DESC;