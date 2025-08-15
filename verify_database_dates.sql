-- Quick verification of actual dates in your database
-- Run this to confirm what year the data is really stored as

SELECT 
    'ADBE Data Summary' as check_type,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_timestamp,
    MAX(timestamp) as latest_timestamp,
    EXTRACT(YEAR FROM MIN(timestamp)) as earliest_year,
    EXTRACT(YEAR FROM MAX(timestamp)) as latest_year
FROM market_data 
WHERE symbol = 'ADBE';

-- Sample recent records to see actual dates
SELECT 
    timestamp,
    EXTRACT(YEAR FROM timestamp) as year,
    EXTRACT(MONTH FROM timestamp) as month,
    EXTRACT(DAY FROM timestamp) as day,
    close
FROM market_data 
WHERE symbol = 'ADBE' 
ORDER BY timestamp DESC 
LIMIT 5;

-- Sample oldest records to see actual dates  
SELECT 
    timestamp,
    EXTRACT(YEAR FROM timestamp) as year,
    EXTRACT(MONTH FROM timestamp) as month, 
    EXTRACT(DAY FROM timestamp) as day,
    close
FROM market_data 
WHERE symbol = 'ADBE' 
ORDER BY timestamp ASC 
LIMIT 5;