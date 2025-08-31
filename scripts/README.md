# 🛠️ Scripts Directory

This directory contains operational and maintenance scripts for the ML Trading System.

## 📁 **Current Scripts**

### **🔧 System Operations**
- **`run_ui.py`** - Start the Dash dashboard application
- **`run_tests.py`** - Execute the test suite  
- **`run_regression_tests.py`** - Run comprehensive regression tests
- **`run_yahoo_collector.py`** - Yahoo Finance data collection
- **`load_env.py`** - Environment variable loading utility

### **📊 Data Processing**
- **`feature_engineering_processor.py`** - Feature engineering pipeline processor
- **`test_optimized_ui_features.py`** - UI optimization testing and validation

### **🗄️ Database Operations**
- **`optimize_feature_database.py`** - Main database optimization script ⭐
- **`optimize_feature_indexes_fixed.py`** - Direct index optimization (backup)

### **🔍 Monitoring & Maintenance**  
- **`cleanup_logs.py`** - Log file cleanup and archival
- **`monitor_connections.py`** - Database connection monitoring

---

## 🚀 **Usage Examples**

### Start the System
```bash
# Start dashboard
python scripts/run_ui.py

# Run data collection
python scripts/run_yahoo_collector.py
```

### Run Tests
```bash
# Basic test suite
python scripts/run_tests.py

# Comprehensive regression tests  
python scripts/run_regression_tests.py
```

### Database Operations
```bash
# Optimize database performance (one-time setup)
python scripts/optimize_feature_database.py

# Monitor database connections
python scripts/monitor_connections.py
```

### Maintenance
```bash
# Clean up old log files
python scripts/cleanup_logs.py

# Process features for ML models
python scripts/feature_engineering_processor.py
```

---

## 🧹 **Cleanup History**

**Removed Scripts** (2025-08-31):
- `direct_feature_optimization.py` - One-time database connection bypass
- `optimize_feature_indexes.py` - First optimization attempt (replaced)
- `apply_feature_optimization.sql` - PostgreSQL-specific commands (unused)
- `test_db_connection.py` - One-time connection debugging

**Reason**: These scripts were created for specific troubleshooting or one-time optimization tasks and are no longer needed after successful completion.

---

## 📋 **Script Categories**

### **Production Scripts** (Keep Always)
- System operations (UI, tests, data collection)
- Monitoring and maintenance utilities
- Database optimization tools

### **Development Scripts** (Review Periodically)  
- Testing and validation scripts
- Feature processing utilities
- Performance testing tools

### **One-time Scripts** (Remove After Use)
- Troubleshooting utilities
- Migration scripts
- Temporary fixes and workarounds

---

## 🎯 **Best Practices**

1. **Document Purpose**: All scripts should have clear docstrings explaining their purpose
2. **One-time Use**: Mark temporary scripts clearly and remove after use
3. **Error Handling**: Include proper error handling and logging
4. **Environment**: Use `load_env.py` for consistent environment loading
5. **Testing**: Test scripts in development before using in production

This directory is now clean and contains only actively used operational scripts.