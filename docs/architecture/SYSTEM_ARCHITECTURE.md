# System Architecture

## Overview

The MLTrading system is a comprehensive machine learning trading platform built with microservices architecture, featuring real-time data collection, advanced feature engineering, and automated deployment capabilities.

## High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Orchestration  │    │   Analytics     │
│                 │    │                  │    │                 │
│ • Yahoo Finance │───▶│ • Prefect Server │───▶│ • Dashboard     │
│ • Market APIs   │    │ • Workflows      │    │ • Monitoring    │
│ • Real-time     │    │ • Scheduling     │    │ • Visualization │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Data Pipeline  │    │  Feature Engine  │    │   ML/Analytics  │
│                 │    │                  │    │                 │
│ • Collection    │───▶│ • 90+ Features   │───▶│ • Indicators    │
│ • Validation    │    │ • 3 Phases       │    │ • Predictions   │
│ • Storage       │    │ • Real-time      │    │ • Backtesting   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
         ┌───────────────────────────────────────────────┐
         │            PostgreSQL Database                │
         │                                               │
         │ • market_data (OHLCV + metadata)             │
         │ • feature_engineered_data (90+ features)     │
         │ • Connection pooling & optimization           │
         └───────────────────────────────────────────────┘
```

## Core Components

### 1. Data Collection Layer

**Yahoo Finance Collector**
- **Purpose**: Real-time market data ingestion
- **Schedule**: Hourly during market hours (9 AM - 4 PM EST)
- **Data**: OHLCV + volume with 3-day optimized window
- **Performance**: 100+ symbols in 5-10 minutes
- **Architecture**: Prefect workflows with concurrent task execution

**Data Flow**:
```
Yahoo API → Data Validation → PostgreSQL → Feature Engineering
```

### 2. Feature Engineering Engine

**Three-Phase Architecture**:

**Phase 1: Foundation Features (13)**
- Price returns and ratios
- Time-based features
- Basic market metrics

**Phase 2: Core Technical (23)**
- Moving averages (SMA/EMA)
- Volatility measures
- Bollinger Bands, MACD
- Technical indicators

**Phase 3: Advanced ML (54+)**
- RSI multi-timeframe
- Volume indicators
- Intraday features
- Lagged features
- Rolling statistics

**Processing Model**:
```
Raw Data → Phase 1 → Phase 2 → Phase 3 → ML-Ready Features
```

### 3. Database Layer

**PostgreSQL with Optimized Schema**

**Core Tables**:
- `market_data`: Time-series OHLCV data
- `feature_engineered_data`: Calculated features (90+ columns)
- `stock_info`: Symbol metadata

**Performance Optimizations**:
- Connection pooling (1-2 connections per process)
- Proper indexing on symbol + timestamp
- Batch insert operations
- Connection timeout management

### 4. Orchestration Layer

**Prefect 2.0 Workflows**

**Production Deployments**:
1. **Yahoo Data Collection**: Hourly market data
2. **Comprehensive Feature Engineering**: Every 2 hours, 90+ features
3. **Monitoring & Health Checks**: Real-time system status

**Workflow Features**:
- Subprocess isolation for reliability
- Automatic retries and error handling  
- Distributed task execution
- Real-time monitoring

### 5. Analytics & Dashboard

**Dash/Plotly Web Interface**

**Key Features**:
- Real-time technical indicator visualization
- Pipeline status monitoring
- Feature analysis and exploration
- System health dashboards

**Performance Architecture**:
- Database-first feature access (10-50x improvement)
- Optimized technical indicator services
- Caching for frequently accessed data

## Data Flow Architecture

### Real-time Data Pipeline

```
Market Hours → Yahoo API → Prefect Task → Validation → PostgreSQL
     ↓              ↓           ↓            ↓           ↓
  9-4 EST      3-day data   Concurrent   Schema check  Time-series
   Mon-Fri      window      processing   Error handle   storage
```

### Feature Engineering Pipeline

```
Market Data → Phase 1 Features → Phase 2 Features → Phase 3 Features → Storage
     ↓              ↓                 ↓                  ↓              ↓
 Raw OHLCV    Price/Time        Technical           Advanced ML      90+ columns
  100 symbols   13 features      23 features         54 features    PostgreSQL
```

### Dashboard Data Flow

```
PostgreSQL → Feature Services → Technical Indicators → Dash Components → Web UI
     ↓              ↓                    ↓                   ↓           ↓
  90+ features  Database-first      Optimized calcs     Real-time    Interactive
  Pre-calculated   access          (vs real-time)      updates       charts
```

## Deployment Architecture

### Production Environment

**Infrastructure**:
- PostgreSQL database with connection pooling
- Prefect server for workflow orchestration  
- Dash web application for analytics
- Background schedulers for automation

**Scaling Strategy**:
- Horizontal scaling via Prefect workers
- Connection pool management (2 workers max)
- Database read replicas for analytics (future)
- Caching layer for dashboard performance

### High Availability

**Reliability Features**:
- Subprocess isolation prevents cascade failures
- Connection pool exhaustion protection
- Automatic retry logic with exponential backoff
- Health monitoring and alerting

**Data Consistency**:
- ACID transactions for data integrity
- Conflict resolution (ON CONFLICT clauses)
- Data validation at ingestion
- Feature engineering idempotency

## Security Architecture

### Database Security
- Connection pooling with authentication
- Environment variable configuration
- SQL injection prevention (parameterized queries)
- Connection timeout and limits

### Application Security
- Input validation and sanitization
- Error handling without information disclosure
- Logging without sensitive data exposure

## Performance Characteristics

### Benchmarks

**Data Collection**:
- 100 symbols: 5-10 minutes
- 3-day window: ~17-50 records per symbol
- Success rate: 90-95%

**Feature Engineering**:
- Phase 1+2: ~2s per symbol
- Phase 3 (comprehensive): ~4s per symbol  
- Batch processing: 1000+ symbols in 1-2 hours

**Dashboard Performance**:
- Database queries: <100ms typical
- Feature loading: 10-50x faster than real-time calculation
- Interactive response: <1s for most operations

### Resource Usage

**Database Connections**:
- Maximum: 6-8 concurrent connections
- Pool size: 1-2 per process
- Workers: 2 concurrent maximum

**Memory Usage**:
- Feature engineering: ~100-200MB per process
- Dashboard: ~50-100MB
- Database: Varies with data volume

**CPU Usage**:
- Data collection: Low (I/O bound)
- Feature engineering: Moderate (computation)
- Dashboard: Low (database queries)

## Technology Stack

### Backend
- **Python 3.8+**: Core language
- **Prefect 2.0**: Workflow orchestration
- **PostgreSQL 12+**: Primary database
- **pandas**: Data manipulation
- **numpy**: Numerical computations

### Frontend  
- **Dash/Plotly**: Interactive web interface
- **Bootstrap**: UI framework
- **JavaScript**: Client-side interactivity

### Infrastructure
- **psycopg2**: PostgreSQL adapter
- **python-dotenv**: Environment management
- **logging**: Structured logging

## Monitoring & Observability

### Logging
- Structured logging with correlation IDs
- Performance tracking for all operations
- Error tracking with full context
- Log aggregation and rotation

### Metrics
- System health monitoring
- Pipeline success rates
- Data freshness tracking
- Connection pool utilization

### Alerting
- Connection limit warnings
- Pipeline failure notifications
- Data staleness alerts
- Performance degradation detection

## Future Architecture Considerations

### Scalability Improvements
- Microservices decomposition
- Container orchestration (Docker/Kubernetes)
- Message queues for async processing
- Distributed caching (Redis)

### Data Architecture Evolution
- Time-series database (InfluxDB) for metrics
- Data lake for historical analysis
- Real-time streaming (Kafka)
- Multi-region deployment

### ML Integration
- Model training pipelines
- A/B testing framework
- Model versioning and deployment
- Real-time prediction services