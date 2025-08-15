-- Analysis and fix for mixed year data in market_data table
-- ADBE has data from 2024-08-02 to 2025-08-14 which is clearly wrong

-- 1. ANALYZE THE PROBLEM
SELECT 
    'Data Distribution by Year' as analysis_type,
    EXTRACT(YEAR FROM timestamp) as year,
    COUNT(*) as record_count,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest
FROM market_data 
WHERE symbol = 'ADBE'
GROUP BY EXTRACT(YEAR FROM timestamp)
ORDER BY year;

-- 2. CHECK HOW MANY SYMBOLS ARE AFFECTED
SELECT 
    'Symbols with 2025 Data' as analysis_type,
    COUNT(DISTINCT symbol) as affected_symbols
FROM market_data 
WHERE EXTRACT(YEAR FROM timestamp) = 2025;

-- 3. SAMPLE OF PROBLEMATIC RECORDS
SELECT 
    'Sample 2025 Records' as analysis_type,
    symbol,
    timestamp,
    close,
    source
FROM market_data 
WHERE EXTRACT(YEAR FROM timestamp) = 2025
AND symbol = 'ADBE'
ORDER BY timestamp 
LIMIT 10;

-- 4. PROPOSED FIX - Convert 2025 dates to 2024
-- This assumes the 2025 data should actually be 2024 data
-- UNCOMMENT AND RUN ONLY AFTER CONFIRMING THIS IS CORRECT

/*
-- BACKUP FIRST (optional but recommended)
CREATE TABLE market_data_backup_before_year_fix AS 
SELECT * FROM market_data WHERE EXTRACT(YEAR FROM timestamp) = 2025;

-- FIX: Convert 2025 timestamps to 2024
UPDATE market_data 
SET timestamp = timestamp - INTERVAL '1 year'
WHERE EXTRACT(YEAR FROM timestamp) = 2025;

-- VERIFY THE FIX
SELECT 
    'After Fix - Data Distribution' as analysis_type,
    EXTRACT(YEAR FROM timestamp) as year,
    COUNT(*) as record_count,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest
FROM market_data 
WHERE symbol = 'ADBE'
GROUP BY EXTRACT(YEAR FROM timestamp)
ORDER BY year;
*/

-- 5. ALTERNATIVE: DELETE DUPLICATE/OVERLAPPING DATA
-- If you prefer to remove the problematic 2025 data instead
/*
-- Check for overlapping dates that might be duplicates
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as records_per_day,
    COUNT(DISTINCT EXTRACT(YEAR FROM timestamp)) as years_on_same_date
FROM market_data 
WHERE symbol = 'ADBE'
GROUP BY DATE(timestamp)
HAVING COUNT(DISTINCT EXTRACT(YEAR FROM timestamp)) > 1
ORDER BY date;

-- If there are overlapping dates, you might want to delete 2025 data instead
-- DELETE FROM market_data WHERE EXTRACT(YEAR FROM timestamp) = 2025;
*/