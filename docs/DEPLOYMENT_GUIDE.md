# MLTrading System Deployment Guide

## Overview

This guide provides comprehensive deployment instructions for the MLTrading system, including configuration management, production setup, and operational procedures. The system uses a three-tier deployment strategy optimized for reliability and performance.

## Deployment Architecture

### Production Deployment Strategy

The MLTrading system employs three distinct deployment components that work together to provide complete data processing and feature engineering capabilities:

```
Complete Setup → Production Data → Production Features → Dashboard
(Manual)         (Hourly)          (Hourly + 5min)     (Real-time)
```

## Core Deployments

### 1. Complete Data and Features Setup

**Purpose**: Initial system setup with full historical data and feature backfill

**File**: `deployments/complete_data_and_features_ondemand.py`

**Configuration**:
```yaml
Name: complete-data-and-features-ondemand
Schedule: Manual trigger only
Data Period: 1 year historical data
Features: All 36 technical indicators
Runtime: 25-45 minutes
Priority: 1 (Primary deployment)
```

**Deployment Command**:
```bash
cd D:\PythonProjects\MLTrading
python deployments/complete_data_and_features_ondemand.py
```

**Use Cases**:
- Initial system setup
- Complete data refresh after extended downtime
- Historical data backfill for new symbols
- System validation after major updates

### 2. Production Data Collection

**Purpose**: Regular incremental data collection during market hours

**File**: `deployments/yahoo_production_deployment.py`

**Configuration**:
```yaml
Name: yahoo-production-data-collection
Schedule: "0 9-16 * * 1-5" (hourly, market hours)
Data Period: 3-day rolling window
Runtime: 5-10 minutes
Priority: 3 (Supporting production)
```

**Deployment Command**:
```bash
python deployments/yahoo_production_deployment.py
```

**Schedule Details**:
- **Frequency**: Every hour during market hours
- **Time Range**: 9:00 AM - 4:00 PM EST
- **Days**: Monday through Friday
- **Data Window**: 3-day optimized period for incremental updates

### 3. Production Feature Engineering

**Purpose**: Real-time technical indicator calculation with subprocess isolation

**File**: `deployments/feature_engineering_production_deployment.py`

**Configuration**:
```yaml
Name: feature-engineering-production-subprocess
Schedule: "5 9-16 * * 1-5" (5 minutes after data collection)
Features: 36 technical indicators
Runtime: <3 seconds for 100+ symbols
Priority: 2 (Critical production)
Architecture: Subprocess isolation
```

**Deployment Command**:
```bash
python deployments/feature_engineering_production_deployment.py
```

**Technical Specifications**:
- **Processing Speed**: ~2 seconds per symbol
- **Success Rate**: 100% reliability through subprocess isolation
- **Memory Management**: Automatic cleanup per symbol
- **Connection Handling**: No connection pool exhaustion

## Configuration Management

### Prefect Configuration

**File**: `deployments/prefect.yaml`

The master configuration file defines all deployment specifications:

```yaml
name: ml-trading-deployments
description: ML Trading System with Yahoo Finance data collection and feature engineering

deployments:
  # Yahoo Data Collection
  - name: yahoo-production-data-collection
    schedule:
      cron: "0 9-16 * * 1-5"
      timezone: America/New_York
    entrypoint: deployments/yahoo_production_deployment.py:production_data_flow
    parameters:
      data_period: "3d"

  # Feature Engineering  
  - name: feature-engineering-production-subprocess
    schedule:
      cron: "5 9-16 * * 1-5"
      timezone: America/New_York
    entrypoint: deployments/feature_engineering_production_deployment.py:production_features_flow
    parameters:
      initial_run: false

  # Complete Pipeline
  - name: complete-data-and-features-ondemand
    schedule: null  # Manual trigger only
    entrypoint: deployments/complete_data_and_features_ondemand.py:complete_pipeline_flow
```

### Dashboard Configuration

**File**: `config/deployments_config.yaml`

Defines monitoring, alerting, and dashboard display settings:

```yaml
deployments:
  # Primary comprehensive deployment
  complete-data-and-features-ondemand:
    display_name: "Complete Data + Features Pipeline"
    category: "comprehensive-pipeline"
    priority: 1
    schedule_type: "manual"
    expected_runtime_minutes: 30
    alert_threshold_hours: 24

  # Critical production feature engineering
  feature-engineering-production-subprocess:
    display_name: "Production Feature Engineering"
    category: "production-pipeline"
    priority: 2
    schedule_type: "market_hours_offset"
    expected_runtime_minutes: 10
    alert_threshold_hours: 2

  # Supporting production data collection
  yahoo-production-data-collection:
    display_name: "Yahoo Finance Data Collection"
    category: "data-collection"
    priority: 3
    schedule_type: "market_hours"
    expected_runtime_minutes: 8
    alert_threshold_hours: 2

# Dashboard display configuration
dashboard:
  primary_deployments:
    - complete-data-and-features-ondemand
    - feature-engineering-production-subprocess
    - yahoo-production-data-collection
  max_visible_deployments: 5
  refresh_intervals:
    pipeline_status: 30
    system_health: 60
    data_freshness: 45

# Schedule type definitions
schedule_types:
  market_hours:
    cron: "0 9-16 * * 1-5"
    timezone: "America/New_York"
    description: "Hourly during market hours (9 AM - 4 PM EST, weekdays)"
  
  market_hours_offset:
    cron: "5 9-16 * * 1-5"
    timezone: "America/New_York"
    description: "5 minutes after each hour during market hours"
  
  manual:
    cron: null
    timezone: "UTC"
    description: "Manual trigger only, no automatic schedule"
```

## Production Workflow

### Daily Operation Schedule

**Typical Market Day Flow**:

```
9:00 AM EST → Yahoo Data Collection (3-day data update)
9:05 AM EST → Feature Engineering (technical indicators)
10:00 AM EST → Yahoo Data Collection
10:05 AM EST → Feature Engineering
11:00 AM EST → Yahoo Data Collection
11:05 AM EST → Feature Engineering
...continues hourly until 4:00 PM EST...
4:00 PM EST → Final data collection
4:05 PM EST → Final feature engineering
```

### Monitoring and Health Checks

**System Health Indicators**:
- **Data Freshness**: Latest timestamp per symbol
- **Pipeline Status**: Success/failure rates
- **Processing Performance**: Runtime vs. expected duration
- **System Resources**: Database connections and memory usage

**Alert Configuration**:
- **Immediate Alerts**: Processing failures, connection issues
- **Performance Alerts**: Runtime > 150% of expected duration  
- **Data Quality Alerts**: Missing data, calculation errors
- **System Health Alerts**: Resource exhaustion, timeout issues

## Deployment Procedures

### Initial System Setup

**Prerequisites**:
1. PostgreSQL database with proper configuration
2. Python environment with required dependencies
3. Prefect server running and accessible
4. Appropriate work pools configured

**Step 1: Database Preparation**
```bash
# Ensure database tables exist
python -c "from src.data.storage.database import DatabaseManager; dm = DatabaseManager(); print('Database ready')"
```

**Step 2: Complete Data Setup**
```bash
# Run complete setup deployment (one-time)
python deployments/complete_data_and_features_ondemand.py
```

**Step 3: Production Deployment**
```bash
# Deploy regular data collection
python deployments/yahoo_production_deployment.py

# Deploy feature engineering
python deployments/feature_engineering_production_deployment.py
```

### Ongoing Operations

**Daily Monitoring Tasks**:
1. Verify all scheduled deployments executed successfully
2. Check data freshness indicators in dashboard
3. Review processing times for performance degradation
4. Monitor database storage growth and optimize as needed

**Weekly Maintenance**:
1. Review deployment logs for error patterns
2. Analyze feature calculation accuracy
3. Optimize database indexes if query performance degrades
4. Update symbol lists if new stocks need processing

**Monthly Review**:
1. Assess storage requirements and implement archiving if needed
2. Review alert thresholds and adjust based on operational experience
3. Evaluate system performance and plan capacity upgrades
4. Update documentation with operational learnings

## Performance Optimization

### Database Optimization

**Index Management**:
```sql
-- Essential indexes for performance
CREATE INDEX idx_features_symbol_timestamp ON feature_engineered_data(symbol, timestamp);
CREATE INDEX idx_features_recent ON feature_engineered_data(symbol, timestamp DESC) 
    WHERE timestamp >= NOW() - INTERVAL '7 days';
```

**Connection Pool Tuning**:
- **Max Connections**: 25 concurrent connections
- **Pool Size**: 5-10 connections for typical workload
- **Connection Timeout**: 30 seconds
- **Pool Recycle**: 3600 seconds (1 hour)

### Processing Optimization

**Feature Engineering Performance**:
- **Target Speed**: <2.5 seconds per symbol
- **Batch Processing**: 5 symbols per batch with delays
- **Memory Management**: Subprocess isolation prevents accumulation
- **Timeout Management**: 30-second limit per symbol

**Data Collection Optimization**:
- **API Rate Limits**: Respect Yahoo Finance limitations
- **Concurrent Workers**: 5 parallel data fetches
- **Data Window**: 3-day period balances freshness and efficiency
- **Retry Logic**: Exponential backoff for failed requests

## Troubleshooting

### Common Issues

**1. Connection Pool Exhaustion**
- **Symptom**: "Connection pool is closed" errors
- **Solution**: Verify subprocess isolation is working correctly
- **Prevention**: Monitor connection usage and implement proper cleanup

**2. Processing Timeouts**
- **Symptom**: Symbol processing exceeds 30-second limit
- **Solution**: Check data quality and calculation complexity
- **Prevention**: Monitor processing times and optimize calculations

**3. Data Quality Issues**
- **Symptom**: Missing or incorrect feature calculations
- **Solution**: Verify input data completeness and recalculate
- **Prevention**: Implement data validation checks

**4. Schedule Conflicts**
- **Symptom**: Feature engineering starts before data collection completes
- **Solution**: Adjust schedule timing or increase data collection timeout
- **Prevention**: Monitor execution times and adjust schedules proactively

### Diagnostic Commands

**Check System Health**:
```bash
# Database connection test
python -c "from src.data.storage.database import DatabaseManager; dm = DatabaseManager(); print('Database OK')"

# Data freshness check
python -c "
from src.data.storage.database import DatabaseManager
dm = DatabaseManager()
conn = dm.get_connection()
cur = conn.cursor()
cur.execute('SELECT MAX(timestamp) FROM market_data')
print(f'Latest data: {cur.fetchone()[0]}')
dm.return_connection(conn)
"

# Feature data validation
python -c "
from src.data.storage.database import DatabaseManager
dm = DatabaseManager()
conn = dm.get_connection()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM feature_engineered_data WHERE created_at >= NOW() - INTERVAL \'1 day\'')
print(f'Recent features: {cur.fetchone()[0]}')
dm.return_connection(conn)
"
```

**Performance Monitoring**:
```bash
# Check processing performance
python scripts/feature_engineering_processor.py --dry-run

# Database performance
python -c "
import time
from src.data.storage.database import DatabaseManager
dm = DatabaseManager()
start = time.time()
conn = dm.get_connection()
cur = conn.cursor()
cur.execute('SELECT symbol, MAX(timestamp) FROM market_data GROUP BY symbol LIMIT 10')
results = cur.fetchall()
elapsed = time.time() - start
print(f'Query time: {elapsed:.3f}s for {len(results)} symbols')
dm.return_connection(conn)
"
```

## Security Considerations

### System Security
- **Process Isolation**: Subprocess boundaries prevent system compromise
- **Resource Limits**: Memory and CPU usage monitoring
- **Input Validation**: All parameters validated before processing
- **Error Containment**: Failed processes don't affect system stability

### Data Security
- **Database Security**: Connection pooling with proper authentication
- **API Security**: Rate limiting and request validation
- **Audit Logging**: Complete processing history with correlation IDs
- **Access Control**: Restricted access to production deployments

### Operational Security
- **Deployment Verification**: Validate configurations before production use
- **Change Management**: Version control for all configuration changes
- **Monitoring**: Real-time alerts for security-relevant events
- **Backup Strategy**: Regular database backups and recovery procedures

---

*This deployment guide provides complete instructions for setting up, configuring, and operating the MLTrading system in production environments with enterprise-level reliability and performance.*