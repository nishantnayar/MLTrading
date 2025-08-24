-- Create feature_engineered_data table with EXACT schema matching Analysis-v4.ipynb
-- Total: 100 columns matching notebook exactly (97 numeric + 3 base columns)

CREATE TABLE feature_engineered_data (
    id SERIAL PRIMARY KEY,
    
    -- Base columns (exact match to notebook)
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    
    -- Basic price features
    returns DOUBLE PRECISION,
    log_returns DOUBLE PRECISION,
    high_low_pct DOUBLE PRECISION,
    open_close_pct DOUBLE PRECISION,
    price_acceleration DOUBLE PRECISION,
    returns_sign DOUBLE PRECISION,
    returns_squared DOUBLE PRECISION,
    
    -- Volatility features
    realized_vol_short DOUBLE PRECISION,
    realized_vol_med DOUBLE PRECISION,
    realized_vol_long DOUBLE PRECISION,
    gk_volatility DOUBLE PRECISION,
    vol_of_vol DOUBLE PRECISION,
    
    -- Moving average features
    price_ma_short DOUBLE PRECISION,
    price_ma_med DOUBLE PRECISION,
    price_ma_long DOUBLE PRECISION,
    price_to_ma_short DOUBLE PRECISION,
    price_to_ma_med DOUBLE PRECISION,
    price_to_ma_long DOUBLE PRECISION,
    ma_short_to_med DOUBLE PRECISION,
    ma_med_to_long DOUBLE PRECISION,
    
    -- Volume features
    volume_ma DOUBLE PRECISION,
    volume_ratio DOUBLE PRECISION,
    log_volume DOUBLE PRECISION,
    vpt DOUBLE PRECISION,
    vpt_ma DOUBLE PRECISION,
    vpt_normalized DOUBLE PRECISION,
    mfi DOUBLE PRECISION,
    
    -- RSI features
    rsi_1d DOUBLE PRECISION,
    rsi_3d DOUBLE PRECISION,
    rsi_1w DOUBLE PRECISION,
    rsi_2w DOUBLE PRECISION,
    rsi_ema DOUBLE PRECISION,
    
    -- Time features (exact match including int types)
    hour INTEGER,
    day_of_week INTEGER,
    date VARCHAR(20),
    hour_sin DOUBLE PRECISION,
    hour_cos DOUBLE PRECISION,
    dow_sin DOUBLE PRECISION,
    dow_cos DOUBLE PRECISION,
    is_market_open INTEGER,
    is_morning INTEGER,
    is_afternoon INTEGER,
    hours_since_open DOUBLE PRECISION,
    hours_to_close DOUBLE PRECISION,
    
    -- Intraday features
    returns_from_daily_open DOUBLE PRECISION,
    intraday_high DOUBLE PRECISION,
    intraday_low DOUBLE PRECISION,
    intraday_range_pct DOUBLE PRECISION,
    position_in_range DOUBLE PRECISION,
    overnight_gap DOUBLE PRECISION,
    dist_from_intraday_high DOUBLE PRECISION,
    dist_from_intraday_low DOUBLE PRECISION,
    
    -- Lagged features (exact order from notebook)
    returns_lag_1 DOUBLE PRECISION,
    vol_lag_1 DOUBLE PRECISION,
    volume_ratio_lag_1 DOUBLE PRECISION,
    returns_lag_2 DOUBLE PRECISION,
    vol_lag_2 DOUBLE PRECISION,
    volume_ratio_lag_2 DOUBLE PRECISION,
    returns_lag_4 DOUBLE PRECISION,
    vol_lag_4 DOUBLE PRECISION,
    volume_ratio_lag_4 DOUBLE PRECISION,
    returns_lag_8 DOUBLE PRECISION,
    vol_lag_8 DOUBLE PRECISION,
    volume_ratio_lag_8 DOUBLE PRECISION,
    returns_lag_24 DOUBLE PRECISION,
    vol_lag_24 DOUBLE PRECISION,
    volume_ratio_lag_24 DOUBLE PRECISION,
    
    -- Rolling statistics features (exact order)
    returns_mean_6h DOUBLE PRECISION,
    returns_std_6h DOUBLE PRECISION,
    returns_skew_6h DOUBLE PRECISION,
    returns_kurt_6h DOUBLE PRECISION,
    price_momentum_6h DOUBLE PRECISION,
    returns_mean_12h DOUBLE PRECISION,
    returns_std_12h DOUBLE PRECISION,
    returns_skew_12h DOUBLE PRECISION,
    returns_kurt_12h DOUBLE PRECISION,
    price_momentum_12h DOUBLE PRECISION,
    returns_mean_24h DOUBLE PRECISION,
    returns_std_24h DOUBLE PRECISION,
    returns_skew_24h DOUBLE PRECISION,
    returns_kurt_24h DOUBLE PRECISION,
    price_momentum_24h DOUBLE PRECISION,
    
    -- Technical indicators (final features)
    bb_upper DOUBLE PRECISION,
    bb_lower DOUBLE PRECISION,
    bb_position DOUBLE PRECISION,
    bb_squeeze DOUBLE PRECISION,
    macd DOUBLE PRECISION,
    macd_signal DOUBLE PRECISION,
    macd_histogram DOUBLE PRECISION,
    macd_normalized DOUBLE PRECISION,
    atr DOUBLE PRECISION,
    atr_normalized DOUBLE PRECISION,
    williams_r DOUBLE PRECISION,
    
    -- Metadata (not in notebook but needed for database)
    source VARCHAR(20) DEFAULT 'yahoo',
    feature_version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_symbol_timestamp_features UNIQUE (symbol, timestamp, source)
);

-- Performance Indexes
CREATE INDEX idx_features_symbol_timestamp ON feature_engineered_data(symbol, timestamp);
CREATE INDEX idx_features_symbol ON feature_engineered_data(symbol);
CREATE INDEX idx_features_timestamp ON feature_engineered_data(timestamp);
CREATE INDEX idx_features_recent ON feature_engineered_data(symbol, timestamp DESC);
CREATE INDEX idx_features_created_at ON feature_engineered_data(created_at);

-- Partial index for market hours
CREATE INDEX idx_features_market_hours ON feature_engineered_data(symbol, timestamp)
    WHERE is_market_open = 1;

-- Comments for documentation
COMMENT ON TABLE feature_engineered_data IS 'Feature engineering table with EXACT 100-column schema matching Analysis-v4.ipynb notebook';
COMMENT ON COLUMN feature_engineered_data.symbol IS 'Stock ticker symbol';
COMMENT ON COLUMN feature_engineered_data.timestamp IS 'Timestamp of the data point (hourly frequency)';
COMMENT ON COLUMN feature_engineered_data.feature_version IS 'Version of feature calculation logic';
COMMENT ON COLUMN feature_engineered_data.date IS 'Date column from notebook (string format)';