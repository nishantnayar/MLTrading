-- PostgreSQL table creation script for ML Trading System
-- Run this script to create all necessary tables for new installations
-- This script is safe to run on existing databases (uses IF NOT EXISTS)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Market data table
CREATE TABLE IF NOT EXISTS market_data (
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

-- Stock information table for sector and industry data
CREATE TABLE IF NOT EXISTS stock_info (
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

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
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

-- Fills table
CREATE TABLE IF NOT EXISTS fills (
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

-- Models table
CREATE TABLE IF NOT EXISTS models (
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

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
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

-- Create indexes for better performance (IF NOT EXISTS prevents errors on existing databases)
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_stock_info_symbol ON stock_info(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_info_sector ON stock_info(sector);
CREATE INDEX IF NOT EXISTS idx_stock_info_industry ON stock_info(industry);
CREATE INDEX IF NOT EXISTS idx_orders_symbol_status ON orders(symbol, status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_fills_order_id ON fills(order_id);
CREATE INDEX IF NOT EXISTS idx_fills_timestamp ON fills(timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_model_symbol ON predictions(model_id, symbol);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at (IF NOT EXISTS prevents errors)
DO $$
BEGIN
    -- Create trigger for orders table
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_orders_updated_at') THEN
        CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- Create trigger for models table
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_models_updated_at') THEN
        CREATE TRIGGER update_models_updated_at BEFORE UPDATE ON models
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- Create trigger for stock_info table
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_stock_info_updated_at') THEN
        CREATE TRIGGER update_stock_info_updated_at BEFORE UPDATE ON stock_info
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Grant necessary permissions (if running as superuser)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
-- GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO trading_user;

-- Set default privileges for future objects
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO trading_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO trading_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS IN SCHEMA public TO trading_user; 