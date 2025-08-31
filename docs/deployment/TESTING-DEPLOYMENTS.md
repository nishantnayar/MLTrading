# Deployment Testing Strategy

## Overview

This document outlines a comprehensive testing strategy for MLTrading deployments that decouples testing from market hour dependencies, ensuring reliable deployment verification regardless of market conditions.

## Testing Philosophy

### Core Principle: Market-Independent Validation

The MLTrading system's tight coupling with market hours (9 AM - 4 PM EST, weekdays) creates testing challenges. Our strategy addresses this through:

1. **Function Import Testing**: Verify Prefect can import deployment functions
2. **Component Isolation Testing**: Test individual components without full pipeline execution
3. **Simulation Testing**: Mock market conditions for comprehensive validation
4. **Production Readiness Verification**: Complete system health checks

## Testing Tools

### 1. Deployment Function Testing

**File**: `scripts/test_deployments.py`

**Purpose**: Verify that Prefect deployment functions can be imported and registered correctly.

```bash
# Test deployment function imports
python scripts/test_deployments.py
```

**What it tests**:
- Function import from deployment files
- Prefect flow registration
- Configuration file validation
- Dependency imports

### 2. Test Deployment

**File**: `deployments/test_deployment.py`

**Purpose**: Complete system validation without market dependencies.

```bash
# Run test deployment (can run anytime)
python deployments/test_deployment.py
```

**What it tests**:
- Database connectivity
- Feature engineering module imports
- Yahoo flow imports
- Subprocess-based processing
- Overall system readiness

### 3. Production Readiness Verification

**File**: `scripts/verify_production_readiness.py`

**Purpose**: Comprehensive pre-deployment validation.

```bash
# Complete production readiness check
python scripts/verify_production_readiness.py
```

**What it tests**:
- All deployment function imports
- Database schema and connectivity
- Feature engineering system readiness
- Subprocess isolation functionality
- Configuration file integrity
- Deployment flow simulation

## Testing Methodology

### Pre-Deployment Validation Sequence

**Step 1: Basic Function Import Testing**
```bash
cd D:\PythonProjects\MLTrading
python -c "
from deployments.feature_engineering_production_deployment import production_features_flow
from deployments.yahoo_production_deployment import production_data_flow
print('✅ All deployment functions imported successfully')
print(f'Feature Engineering Flow: {production_features_flow.name}')
print(f'Yahoo Data Flow: {production_data_flow.name}')
"
```

**Expected Output**:
```
✅ All deployment functions imported successfully
Feature Engineering Flow: feature-engineering-production-subprocess
Yahoo Data Flow: yahoo-production-data-collection
```

**Step 2: Test Deployment Execution**
```bash
python deployments/test_deployment.py
```

**Expected Output**:
```
✅ ALL SYSTEMS READY FOR PRODUCTION DEPLOYMENT
Final result: {
  'overall_status': 'success',
  'ready_for_production': True,
  'database_connection': 'success',
  'feature_engineering_import': 'success',
  'yahoo_flow_import': 'success',
  'subprocess_feature_engineering': 'success'
}
```

**Step 3: Production Readiness Verification**
```bash
python scripts/verify_production_readiness.py
```

**Expected Output**:
```
🎉 ALL SYSTEMS GO - READY FOR PRODUCTION DEPLOYMENT!
```

### Market Hour Independent Testing

#### Database Testing Without Market Data Dependencies

```python
# Test database connectivity and schema
def test_database_readiness():
    from src.data.storage.database import DatabaseManager
    dm = DatabaseManager()
    conn = dm.get_connection()
    cur = conn.cursor()
    
    # Test basic connectivity
    cur.execute("SELECT 1")
    
    # Test essential tables exist
    cur.execute("SELECT COUNT(*) FROM market_data")
    cur.execute("SELECT COUNT(*) FROM feature_engineered_data")
    
    # Test recent data availability (if any)
    cur.execute("SELECT MAX(timestamp) FROM market_data")
    
    dm.return_connection(conn)
    return True
```

#### Feature Engineering Testing Without Full Processing

```python
# Test feature engineering system readiness
def test_feature_engineering_components():
    from src.data.processors.feature_engineering import TradingFeatureEngine
    
    # Test instantiation
    engineer = TradingFeatureEngine()
    
    # Test database connection through feature engineering
    conn = engineer.db_manager.get_connection()
    cur = conn.cursor()
    
    # Test feature table schema
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'feature_engineered_data'")
    columns = cur.fetchall()
    
    engineer.db_manager.return_connection(conn)
    return len(columns) > 36  # Should have 36+ feature columns
```

#### Subprocess Isolation Testing

```python
# Test subprocess execution without symbol processing
def test_subprocess_capability():
    import subprocess
    import sys
    
    test_script = '''
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.data.storage.database import DatabaseManager
dm = DatabaseManager()
conn = dm.get_connection()
cur = conn.cursor()
cur.execute("SELECT 1")
dm.return_connection(conn)
print("SUCCESS")
'''
    
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    return result.returncode == 0 and "SUCCESS" in result.stdout
```

## Configuration Validation

### Prefect Configuration Testing

**File**: `deployments/prefect.yaml`

**Validation Points**:
- Correct entrypoint references
- Valid cron schedules
- Proper parameter configuration
- Work pool assignments

**Test Command**:
```bash
python -c "
import yaml
with open('deployments/prefect.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
for deployment in config['deployments']:
    print(f'✅ {deployment[\"name\"]}: {deployment[\"entrypoint\"]}')
"
```

### Dashboard Configuration Testing

**File**: `config/deployments_config.yaml`

**Validation Points**:
- Deployment definitions match Prefect configuration
- Alert thresholds are reasonable
- Schedule types are properly defined
- Dashboard display settings are valid

## Mock Testing for Market Dependencies

### Simulated Market Conditions

For comprehensive testing without waiting for market hours:

```python
# Mock market hours testing
def test_with_mock_market_conditions():
    import datetime
    from unittest.mock import patch
    
    # Mock current time to be during market hours
    mock_time = datetime.datetime(2024, 1, 15, 14, 30, 0)  # Monday 2:30 PM EST
    
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_time
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)
        
        # Run market-hour-dependent logic
        # Test scheduling logic
        # Test data collection timing
```

### Data Simulation

For testing without fresh market data:

```python
# Test with simulated data
def test_with_simulated_data():
    from src.data.storage.database import DatabaseManager
    
    # Insert test data for a specific symbol
    test_data = {
        'symbol': 'TEST',
        'timestamp': '2024-01-15 14:30:00',
        'open': 100.0,
        'high': 102.0,
        'low': 98.0,
        'close': 101.0,
        'volume': 1000000
    }
    
    dm = DatabaseManager()
    conn = dm.get_connection()
    # Insert test data, run feature engineering, verify results, cleanup
```

## Continuous Integration Testing

### Automated Testing Pipeline

```yaml
# CI/CD pipeline testing (example)
test_stages:
  - name: "Import Testing"
    command: "python -c 'from deployments.feature_engineering_production_deployment import production_features_flow'"
    
  - name: "Database Connectivity"
    command: "python -c 'from src.data.storage.database import DatabaseManager; dm = DatabaseManager(); conn = dm.get_connection(); dm.return_connection(conn)'"
    
  - name: "Test Deployment"
    command: "python deployments/test_deployment.py"
    
  - name: "Production Readiness"
    command: "python scripts/verify_production_readiness.py"
```

## Troubleshooting Guide

### Common Issues and Solutions

**Issue**: `RuntimeError: Function with name 'production_features_flow' not found`
- **Cause**: Function defined inside `if __name__ == "__main__"` block
- **Solution**: Move function to module level (outside the main block)
- **Test**: `python -c "from deployments.feature_engineering_production_deployment import production_features_flow"`

**Issue**: Database connection errors during testing
- **Cause**: Database not running or connection pool issues
- **Solution**: Ensure PostgreSQL is running and connection parameters are correct
- **Test**: `python -c "from src.data.storage.database import DatabaseManager; dm = DatabaseManager()"`

**Issue**: Import errors for workflow modules
- **Cause**: Python path not set correctly or missing dependencies
- **Solution**: Ensure project root is in Python path
- **Test**: `python -c "import sys; sys.path.insert(0, '.'); from src.workflows.data_pipeline.feature_engineering_flow_updated import feature_engineering_flow_subprocess"`

## Production Deployment Confidence Checklist

### Pre-Deployment Verification

- [ ] **Function Import Test**: All deployment functions import successfully
- [ ] **Database Connectivity**: Database connection and essential tables verified
- [ ] **Feature Engineering Ready**: TradingFeatureEngine instantiates correctly
- [ ] **Subprocess Isolation**: Process isolation working correctly
- [ ] **Configuration Valid**: All YAML configuration files are valid
- [ ] **Test Deployment Success**: Test deployment completes with 100% success
- [ ] **Production Readiness**: All systems pass readiness verification

### Deployment Commands

Once all tests pass, deploy using:

```bash
# Deploy feature engineering (subprocess-based, reliable)
python deployments/feature_engineering_production_deployment.py

# Deploy Yahoo data collection (optimized 3-day window)
python deployments/yahoo_production_deployment.py

# Optional: Complete setup (if needed)
python deployments/complete_data_and_features_ondemand.py
```

### Post-Deployment Verification

```bash
# Verify deployments are registered in Prefect
prefect deployment ls

# Check deployment status
prefect deployment inspect <deployment-name>

# Monitor first few executions
# (Wait for market hours or trigger manually for testing)
```

## Success Criteria

### Testing Success Indicators

1. **Import Success**: All deployment functions import without errors
2. **Flow Registration**: Functions are properly registered as Prefect flows
3. **Database Ready**: Database connection and schema validation pass
4. **Subprocess Works**: Process isolation executes successfully
5. **Configuration Valid**: All config files pass validation
6. **Test Deployment**: 100% success rate on test deployment execution

### Production Readiness Confirmation

```
✅ ALL SYSTEMS GO - READY FOR PRODUCTION DEPLOYMENT!
```

When this message appears from the production readiness verification, the system is confirmed ready for deployment regardless of market conditions.

---

*This testing strategy ensures reliable deployment validation independent of market hours, providing confidence in production deployments through comprehensive pre-deployment verification.*