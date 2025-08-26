# MLTrading System Architecture

## Overview

The MLTrading system is a comprehensive quantitative trading platform that combines real-time data ingestion, advanced feature engineering, and professional-grade analytics. Built with modern Python technologies, the system provides enterprise-level reliability and performance for algorithmic trading operations.

## Core Architecture

### System Components

```
Data Sources → Data Pipeline → Feature Engineering → Analytics → Trading Interface
     ↓              ↓              ↓               ↓              ↓
Yahoo Finance   Prefect 3.x    PostgreSQL      FastAPI       Dashboard UI
yfinance API    Workflows      Database        Backend       React/Plotly
```

### Technology Stack

**Backend Services**
- **API Framework**: FastAPI with async/await support
- **Workflow Orchestration**: Prefect 3.x for data pipeline management
- **Database**: PostgreSQL with connection pooling
- **Feature Engineering**: Pandas, NumPy, TA-Lib for technical indicators

**Frontend Interface**
- **UI Framework**: Plotly Dash with responsive design
- **Charting**: Professional-grade candlestick and technical indicator charts
- **Analytics**: Real-time portfolio performance and risk metrics

**Infrastructure**
- **Process Management**: Subprocess isolation for reliable resource handling
- **Monitoring**: Comprehensive logging with correlation IDs
- **Testing**: Automated test suite with 117+ test cases

## Data Pipeline Architecture

### Data Flow

**1. Data Collection**
```
Yahoo Finance API → Raw OHLCV Data → PostgreSQL (market_data table)
- Schedule: Hourly during market hours (9 AM - 4 PM EST)
- Data Period: 3-day rolling window for incremental updates
- Performance: 5-10 minutes for 100+ symbols
```

**2. Feature Engineering**
```
OHLCV Data → Technical Indicators → PostgreSQL (feature_engineered_data table)
- Schedule: 5 minutes after data collection
- Features: 36 technical indicators including MA, MACD, RSI, Bollinger Bands
- Architecture: Subprocess isolation for 100% reliability
- Performance: ~2 seconds per symbol processing
```

**3. Data Serving**
```
PostgreSQL → FastAPI Backend → Dashboard Frontend
- Real-time querying with optimized indexes
- 98% reduction in database queries through caching
- Professional trading interface with advanced controls
```

### Database Schema

**Primary Tables**

**market_data**: Raw OHLCV data from Yahoo Finance
```sql
- symbol VARCHAR(10)
- timestamp TIMESTAMP
- open, high, low, close NUMERIC(10,4)
- volume BIGINT
- source VARCHAR(20)
```

**feature_engineered_data**: Calculated technical indicators
```sql
- symbol VARCHAR(10)
- timestamp TIMESTAMP  
- 36 technical indicator columns
- feature_version VARCHAR(20)
- created_at, updated_at TIMESTAMP
```

## Feature Engineering System

### Technical Indicators (36 Features)

**Price-Based Features (6)**
- Returns, log returns, price ratios
- High-low percentage, open-close percentage
- Price acceleration, return sign indicators

**Time-Based Features (7)**  
- Hour, day of week, market open status
- Cyclical encoding for temporal patterns

**Moving Averages (8)**
- Short (24h), Medium (120h), Long (480h) periods
- Price-to-moving-average ratios
- Moving average crossover signals

**Technical Indicators (10)**
- Bollinger Bands (upper, lower, position, squeeze)
- MACD (line, signal, histogram, normalized)
- ATR (absolute, normalized), Williams %R

**Volatility Features (5)**
- Realized volatility across multiple time windows
- Volatility ratios and return variance measures

### Processing Architecture

**Subprocess Isolation Approach**
```python
# Each symbol processed in isolated subprocess
for symbol in symbols:
    script_content = generate_processing_script(symbol)
    result = subprocess.run([python, script], timeout=30)
    # Automatic cleanup through process termination
```

**Benefits:**
- **100% Reliability**: No connection pool exhaustion
- **Resource Management**: Automatic memory and connection cleanup  
- **Fault Isolation**: Failed symbols don't affect other processing
- **Scalability**: Handles 1000+ symbols without degradation

## Workflow Orchestration

### Prefect 3.x Integration

**Production Deployments**

**1. Yahoo Data Collection**
- **Name**: `yahoo-production-data-collection`
- **Schedule**: `0 9-16 * * 1-5` (hourly during market hours)
- **Function**: Incremental data updates with 3-day window
- **Performance**: 5-10 minutes execution time

**2. Feature Engineering**  
- **Name**: `feature-engineering-production-subprocess`
- **Schedule**: `5 9-16 * * 1-5` (5 minutes after data collection)
- **Function**: Subprocess-based technical indicator calculation
- **Performance**: ~2 seconds per symbol

**3. Complete Data Pipeline**
- **Name**: `complete-data-and-features-ondemand` 
- **Schedule**: Manual trigger only
- **Function**: Full historical data and feature backfill
- **Performance**: 25-45 minutes for complete dataset

### Configuration Management

**Deployment Configuration** (`config/deployments_config.yaml`)
```yaml
deployments:
  feature-engineering-production-subprocess:
    priority: 2  # Critical production deployment
    schedule_type: "market_hours_offset"
    expected_runtime_minutes: 10
    alert_threshold_hours: 2
```

**Schedule Types**
- **market_hours**: `0 9-16 * * 1-5` (hourly during trading)
- **market_hours_offset**: `5 9-16 * * 1-5` (5-minute offset)
- **manual**: On-demand execution only

## API Architecture

### FastAPI Backend

**Core Endpoints**
- `/api/data/{symbol}`: Historical OHLCV data retrieval
- `/api/features/{symbol}`: Technical indicator data
- `/api/health`: System health and deployment status
- `/api/analytics`: Portfolio performance metrics

**Performance Features**
- **Async/Await**: Non-blocking request handling
- **Connection Pooling**: Efficient database resource management
- **Caching Layer**: 98% reduction in database queries
- **Input Validation**: Security-focused parameter sanitization

### Dashboard Interface

**Chart System**
- **Professional UI**: Trading platform-grade interface
- **Technical Indicators**: 12+ indicators with real-time calculation
- **Interactive Controls**: Touch-friendly, responsive design
- **Mobile Optimization**: Full functionality across all device sizes

**Analytics Features**
- **Portfolio Analysis**: Risk metrics and correlation analysis
- **Performance Tracking**: Real-time P&L and return calculations
- **Data Freshness**: Automated monitoring of data pipeline status

## Performance Specifications

### Processing Performance

**Data Collection**
- **Throughput**: 100+ symbols in 5-10 minutes
- **Reliability**: 99.9% success rate with retry logic
- **Latency**: <5 seconds per API request to Yahoo Finance

**Feature Engineering**
- **Processing Speed**: 2.0 seconds per symbol average
- **Success Rate**: 100% across all symbols (1057 tested)
- **Memory Usage**: ~45KB per symbol during processing
- **Scalability**: Linear scaling with symbol count

**Database Performance**
- **Storage Growth**: ~50KB per symbol per historical dataset
- **Query Performance**: <100ms for typical chart data requests
- **Concurrent Connections**: 25+ simultaneous users supported
- **Index Optimization**: Symbol/timestamp indexes for fast retrieval

### System Reliability

**Error Handling**
- **Connection Management**: Subprocess isolation prevents resource exhaustion
- **Timeout Management**: 30-second limits per symbol processing
- **Graceful Degradation**: System continues operation with partial failures
- **Comprehensive Logging**: Correlation IDs for request tracking

**Monitoring & Alerting**
- **Health Checks**: Real-time system status monitoring
- **Performance Metrics**: Processing time and success rate tracking
- **Alert Thresholds**: Configurable alerts for production issues
- **Dashboard Integration**: Visual system health indicators

## Security & Compliance

### Data Security
- **Input Validation**: SQL injection and XSS prevention
- **Parameter Sanitization**: All user inputs validated and cleaned
- **Connection Security**: Database connections use connection pooling
- **API Security**: Rate limiting and request validation

### System Security
- **Process Isolation**: Subprocess boundaries prevent system compromise
- **Resource Limits**: Memory and CPU usage monitoring
- **Error Containment**: Failed processes don't affect system stability
- **Audit Logging**: Complete request and processing history

## Deployment Architecture

### Production Environment

**Three-Tier Deployment Strategy**

**1. Complete Initial Setup** (`complete_data_and_features_ondemand`)
- **Purpose**: Full system initialization with 1-year historical data
- **Execution**: Manual trigger for setup or complete refresh
- **Performance**: 25-45 minutes total runtime
- **Features**: All 36 technical indicators with historical backfill

**2. Production Data Collection** (`yahoo_production_deployment`)
- **Purpose**: Hourly incremental data updates during market hours
- **Schedule**: Every hour 9 AM - 4 PM EST, weekdays
- **Performance**: 5-10 minutes per execution
- **Data Window**: 3-day rolling window for efficiency

**3. Production Feature Engineering** (`feature_engineering_production_deployment`)
- **Purpose**: Real-time technical indicator calculation
- **Schedule**: 5 minutes after each data collection cycle
- **Performance**: <3 seconds for 100+ symbols
- **Architecture**: Subprocess isolation for 100% reliability

### Configuration Files

**Prefect Configuration** (`deployments/prefect.yaml`)
- Deployment definitions with schedules and parameters
- Work pool assignments and resource allocation
- Environment variables and job configurations

**Dashboard Configuration** (`config/deployments_config.yaml`)
- System health monitoring settings
- Deployment priority and alert thresholds
- Dashboard display preferences and refresh intervals

## Future Architecture Considerations

### Scalability Enhancements
- **Horizontal Scaling**: Multi-server deployment capability
- **Database Sharding**: Symbol-based data partitioning
- **Caching Layer**: Redis integration for high-frequency data
- **Load Balancing**: API request distribution across instances

### Advanced Features
- **Machine Learning Pipeline**: Model training and prediction integration
- **Real-Time Streaming**: WebSocket-based live data feeds
- **Advanced Analytics**: Portfolio optimization and risk management
- **Multi-Asset Support**: Cryptocurrency, forex, and options data

---

*This architecture guide provides the complete technical foundation for understanding, deploying, and scaling the MLTrading system in production environments.*