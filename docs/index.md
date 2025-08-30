# MLTrading System Documentation

Welcome to the MLTrading system - a comprehensive machine learning-based trading platform with advanced feature engineering and automated deployment capabilities.

## 🚀 System Overview

MLTrading is a production-ready trading system that combines:

- **Real-time data collection** from Yahoo Finance
- **Advanced feature engineering** with 90+ ML-ready features  
- **Interactive dashboard** with professional-grade charts
- **Automated deployment** using Prefect 3.x workflows
- **Robust database architecture** with PostgreSQL

## 📊 Key Features

### Data Pipeline
- Hourly Yahoo Finance data collection during market hours
- Comprehensive feature engineering every 2 hours
- Sequential processing to prevent database connection issues
- Automated error handling and logging

### Interactive Dashboard  
- Real-time technical analysis charts
- Symbol comparison and filtering
- Market overview and performance metrics
- Top symbols by volume analysis

### Deployment Automation
- **Combined Sequential Flow**: Yahoo collection → Feature engineering
- Scheduled execution during market hours (9 AM - 4 PM EST)
- Production logging with absolute paths
- Work pool management for reliable execution

## 🏗️ Architecture

The system uses a modular architecture with:

- **Data Layer**: PostgreSQL with optimized connection pooling
- **Processing Layer**: Feature engineering with subprocess isolation  
- **Service Layer**: Unified data services with caching
- **Presentation Layer**: Dash-based interactive dashboard
- **Orchestration Layer**: Prefect 3.x for workflow management

## 📚 Documentation Sections

### [Architecture](architecture/SYSTEM_ARCHITECTURE.md)
Detailed system design and component interactions

### [Deployment](deployment/deployments.md) 
Prefect deployment configuration and management

### [Troubleshooting](troubleshooting/TROUBLESHOOTING-CONNECTION-ISSUES.md)
Common issues and solutions

### [Testing](testing/regression_test_manual.md)
Manual testing procedures and checklists

## 🚀 Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure database**: Set up PostgreSQL connection
3. **Deploy workflows**: `cd deployments && prefect deploy --all`
4. **Start dashboard**: `python scripts/run_ui.py`
5. **Monitor**: Access dashboard at http://localhost:8050

## 💡 Key Components

| Component | Purpose | Status |
|-----------|---------|---------|
| Yahoo Collector | Market data ingestion | ✅ Production |
| Feature Engineering | ML feature generation | ✅ Production |
| Dashboard | Interactive visualization | ✅ Production |
| Sequential Flow | Automated pipeline | ✅ Active |

## 📈 Data Flow

```
Yahoo Finance → Data Collection → Feature Engineering → Dashboard
     ↓              ↓                    ↓              ↓
  Raw OHLCV    PostgreSQL DB      90+ Features    Real-time UI
```

---

*This documentation is built with MkDocs and automatically updated with system changes.*