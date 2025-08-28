# ML Trading System Documentation

A comprehensive machine learning trading system with real-time data collection, advanced feature engineering, and automated deployment.

## 📋 Table of Contents

- [🏗️ System Architecture](#️-system-architecture)
- [🚀 Getting Started](#-getting-started)
- [📊 Feature Engineering](#-feature-engineering)
- [🔄 Deployment & Operations](#-deployment--operations)
- [🧪 Testing & Development](#-testing--development)
- [🔧 API Reference](#-api-reference)

## 🏗️ System Architecture

### Core Components

1. **Data Pipeline**
   - Yahoo Finance data collection (hourly during market hours)
   - Real-time market data ingestion and storage
   - 3-day optimized window for incremental updates

2. **Feature Engineering**
   - **Phase 1**: Foundation features (13) - basic price and time features
   - **Phase 2**: Core Technical (23) - moving averages, volatility, Bollinger bands
   - **Phase 3**: Advanced ML (54+) - RSI multi-timeframe, volume indicators, lagged features
   - **Total**: 90+ comprehensive features for advanced ML analysis

3. **Database Layer**
   - PostgreSQL with connection pooling
   - Optimized table structure for time-series data
   - Feature-engineered data storage with proper indexing

4. **Dashboard & Analytics**
   - Real-time trading dashboard with Dash/Plotly
   - Technical indicator visualization
   - Pipeline status monitoring
   - Database-first feature architecture (10-50x performance improvement)

5. **Orchestration**
   - Prefect workflows with subprocess isolation
   - Automated deployment scheduling
   - Production-ready error handling and monitoring

### Data Flow

```
Market Data → Yahoo Collector → PostgreSQL → Feature Engineering → ML-Ready Features → Dashboard
     ↓              ↓              ↓              ↓                    ↓            ↓
  API Calls    3-day Window   Connection Pool  90+ Features      Real-time UI   Analytics
```

### Deployment Architecture

**Current Production Setup:**
- **Yahoo Data Collection**: Runs hourly (9 AM - 4 PM EST, weekdays)
- **Comprehensive Feature Engineering**: Runs every 2 hours (90+ features)
- **Dashboard**: Real-time monitoring and analysis interface

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Prefect 2.0+

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd MLTrading
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database and API credentials
   ```

3. **Database Setup**
   ```bash
   python scripts/test_db_connection.py
   ```

4. **Start Services**
   ```bash
   # Start Prefect server
   prefect server start
   
   # Deploy workflows
   prefect deploy --all
   
   # Start dashboard
   python -m src.dashboard.app
   ```

### Quick Test

```python
# Test data collection
python scripts/run_yahoo_collector.py

# Test feature engineering
python scripts/feature_engineering_processor.py

# Test dashboard
# Navigate to http://localhost:8050
```

## 📊 Feature Engineering

### Architecture Overview

Our feature engineering system processes market data through three phases:

**Phase 1: Foundation Features (13)**
- Price returns and log returns
- Price ratios (high/close, low/close, etc.)
- Time-based features (hour, day of week, month)

**Phase 2: Core Technical Indicators (23)**
- Moving averages (SMA/EMA: 12, 24, 120, 480 periods)
- Volatility measures (rolling std, ATR)
- Bollinger Bands (20-period, 2 std dev)
- MACD (12/26/9 configuration)

**Phase 3: Advanced ML Features (54+)**
- **RSI Multi-timeframe**: 1d, 3d, 1w, 2w, EMA-based
- **Volume Indicators**: Volume oscillator, price-volume trend
- **Intraday Features**: Daily reference points
- **Lagged Features**: 1h, 2h, 4h, 8h, 24h lags
- **Rolling Statistics**: 6h, 12h, 24h windows

### RSI Calculation

Optimized for intraday data (7 records/day):
```python
RSI_WINDOWS = {
    'rsi_1d': 7,         # 1 day (~7 intraday records)
    'rsi_3d': 21,        # 3 days
    'rsi_1w': 35,        # 1 week (5 trading days)
    'rsi_2w': 70         # 2 weeks (10 trading days)
}
```

### Usage

```python
# Process single symbol with comprehensive features
from src.data.processors.feature_engineering import FeatureEngineerPhase1And2
engineer = FeatureEngineerPhase1And2()
success = engineer.process_symbol_phase3_comprehensive("AAPL", initial_run=True)

# Bulk processing
python scripts/feature_engineering_processor.py
```

### Database Schema

**Key Tables:**
- `market_data`: OHLCV data with timestamps
- `feature_engineered_data`: All calculated features (90+ columns)
- Connection pooling for optimal performance

## 🔄 Deployment & Operations

### Production Deployments

**1. Yahoo Finance Data Collection**
```yaml
name: yahoo-production-data-collection
schedule: "0 9-16 * * 1-5"  # Hourly during market hours
purpose: Regular 3-day incremental data collection
performance: 5-10 minutes for 100+ symbols
```

**2. Comprehensive Feature Engineering**
```yaml
name: comprehensive-feature-engineering-production-subprocess
schedule: "10 9-15/2 * * 1-5"  # Every 2 hours during market
purpose: Calculate 90+ ML-ready features
performance: ~4s per symbol with subprocess isolation
reliability: 100% success rate
```

### Monitoring & Health

- **Pipeline Status**: Real-time deployment monitoring
- **Data Freshness**: Automatic alerts for stale data
- **System Health**: Success rates and performance metrics
- **Connection Management**: Optimized database pooling

### Configuration Files

- `deployments/prefect.yaml`: Deployment definitions
- `config/deployments_config.yaml`: Dashboard monitoring config
- `.env`: Environment variables and credentials

## 🧪 Testing & Development

### Test Structure

```bash
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for workflows  
├── e2e/           # End-to-end system tests
└── performance/   # Performance and load tests
```

### Running Tests

```bash
# All tests
python scripts/run_tests.py

# Specific test suites
pytest tests/unit/test_feature_engineering.py
pytest tests/integration/test_data_pipeline.py

# Performance tests
python scripts/test_optimized_ui_features.py
```

### Development Workflow

1. **Feature Development**
   ```bash
   # Create feature branch
   git checkout -b feature/new-indicator
   
   # Develop with tests
   pytest tests/unit/test_new_feature.py
   
   # Integration testing
   python scripts/feature_engineering_processor.py
   ```

2. **Database Testing**
   ```bash
   # Test connections
   python scripts/test_db_connection.py
   
   # Verify feature data
   SELECT COUNT(*) FROM feature_engineered_data WHERE rsi_1d IS NOT NULL;
   ```

3. **Deployment Testing**
   ```bash
   # Test deployments
   python scripts/test_deployments.py
   
   # Verify production readiness
   python scripts/verify_production_readiness.py
   ```

## 🔧 API Reference

### Core Classes

**FeatureEngineerPhase1And2**
```python
# Phase 1+2 features (36 indicators)
engineer = FeatureEngineerPhase1And2()
success = engineer.process_symbol_phase1_and_phase2(symbol, initial_run=True)

# Phase 1+2+3 comprehensive features (90+ indicators) 
success = engineer.process_symbol_phase3_comprehensive(symbol, initial_run=True)
```

**DatabaseManager**
```python
from src.data.storage.database import get_db_manager
db = get_db_manager()
conn = db.get_connection()
```

**PrefectService**
```python
from src.services.prefect_service import get_prefect_service
service = get_prefect_service()
status = service.get_deployment_status("deployment-name")
```

### Dashboard Services

**FeatureDataService** - Database-first feature access
```python
from src.dashboard.services.feature_data_service import FeatureDataService
service = FeatureDataService()
features = service.get_all_indicators_from_db(symbol="AAPL")
```

**TechnicalIndicatorService** - Optimized technical indicators
```python
from src.dashboard.services.technical_indicators import TechnicalIndicatorService
service = TechnicalIndicatorService()
rsi = service.get_rsi_optimized(symbol="AAPL", period=14)
```

### Configuration

**Environment Variables**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_data
DB_USER=postgres
DB_PASSWORD=admin123
PREFECT_API_URL=http://localhost:4200/api
```

**Feature Engineering Windows**
```python
RSI_WINDOWS = {
    'rsi_1d': 7, 'rsi_3d': 21, 'rsi_1w': 35, 'rsi_2w': 70
}
MOVING_WINDOWS = [12, 24, 120, 480]  # Short, medium, long, very long
VOLATILITY_WINDOWS = [12, 24, 120]  # 12h, 1d, 5d
```

---

## 📝 Recent Updates

- **RSI Fix**: Corrected RSI calculation windows for intraday data frequency
- **Consolidated Deployments**: Streamlined to 2 core deployments for optimal performance  
- **Database Optimization**: 10-50x performance improvement with database-first architecture
- **Comprehensive Features**: Full 90+ feature implementation with Phase 1+2+3
- **Dashboard Enhancement**: Real-time monitoring with detailed analysis tabs

## 📚 Additional Documentation

For specialized topics, see these focused guides:

- **[Troubleshooting Connection Issues](TROUBLESHOOTING-CONNECTION-ISSUES.md)** - Database connection pooling and PostgreSQL optimization
- **[Testing Deployments](TESTING-DEPLOYMENTS.md)** - Comprehensive deployment testing strategy independent of market hours

## 🔗 Quick Links

- **Dashboard**: http://localhost:8050
- **Prefect UI**: http://localhost:4200
- **Database**: PostgreSQL on localhost:5432
- **Logs**: `scripts/logs/`

---

*Last updated: August 2025*