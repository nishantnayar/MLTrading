-- Debug query to check ADBE data integrity and identify null issues
-- Run this to understand what data is available and where nulls occur

-- 1. Overall data summary
SELECT 
    'Overall Summary' as check_type,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_date,
    MAX(timestamp) as latest_date,
    COUNT(DISTINCT symbol) as symbols_count
FROM market_data 
WHERE symbol = 'ADBE';

-- 2. Check for null values in each column
SELECT 
    'Null Value Analysis' as check_type,
    SUM(CASE WHEN timestamp IS NULL THEN 1 ELSE 0 END) as null_timestamps,
    SUM(CASE WHEN open IS NULL THEN 1 ELSE 0 END) as null_opens,
    SUM(CASE WHEN high IS NULL THEN 1 ELSE 0 END) as null_highs,
    SUM(CASE WHEN low IS NULL THEN 1 ELSE 0 END) as null_lows,
    SUM(CASE WHEN close IS NULL THEN 1 ELSE 0 END) as null_closes,
    SUM(CASE WHEN volume IS NULL THEN 1 ELSE 0 END) as null_volumes
FROM market_data 
WHERE symbol = 'ADBE';

-- 3. Check for rows with ANY null values in essential columns
SELECT 
    'Rows with Essential Nulls' as check_type,
    COUNT(*) as rows_with_essential_nulls
FROM market_data 
WHERE symbol = 'ADBE' 
AND (timestamp IS NULL OR open IS NULL OR high IS NULL OR low IS NULL OR close IS NULL);

-- 4. Check for rows with ONLY volume nulls (these should be preserved)
SELECT 
    'Rows with Only Volume Nulls' as check_type,
    COUNT(*) as rows_with_only_volume_nulls
FROM market_data 
WHERE symbol = 'ADBE' 
AND volume IS NULL 
AND timestamp IS NOT NULL 
AND open IS NOT NULL 
AND high IS NOT NULL 
AND low IS NOT NULL 
AND close IS NOT NULL;

-- 5. Sample of recent data to check values
SELECT 
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    CASE 
        WHEN open IS NULL OR high IS NULL OR low IS NULL OR close IS NULL OR timestamp IS NULL 
        THEN 'WOULD BE DROPPED' 
        ELSE 'WOULD BE KEPT' 
    END as row_status
FROM market_data 
WHERE symbol = 'ADBE' 
ORDER BY timestamp DESC 
LIMIT 10;

-- 6. Date range check - what months have data
SELECT 
    DATE_FORMAT(timestamp, '%Y-%m') as year_month,
    COUNT(*) as records_count,
    MIN(timestamp) as month_start,
    MAX(timestamp) as month_end
FROM market_data 
WHERE symbol = 'ADBE'
GROUP BY DATE_FORMAT(timestamp, '%Y-%m')
ORDER BY year_month DESC
LIMIT 12;