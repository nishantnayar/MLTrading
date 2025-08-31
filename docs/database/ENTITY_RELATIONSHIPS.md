# 🔗 Database Entity Relationship Diagrams

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Market Data Layer"
        SI[stock_info<br/>📊 Symbol Metadata]
        MD[market_data<br/>📈 OHLCV Data<br/>1.9M+ records]
        FED[feature_engineered_data<br/>🧠 ML Features<br/>100+ columns]
        MV[mv_features_dashboard_summary<br/>⚡ Dashboard Cache]
    end
    
    subgraph "Trading Layer"
        M[models<br/>🤖 ML Models]
        P[predictions<br/>🎯 Model Outputs]
        O[orders<br/>📋 Trade Orders]
        F[fills<br/>✅ Executions]
    end
    
    subgraph "Monitoring Layer"
        SL[system_logs<br/>📝 App Logs]
        TL[trading_events<br/>💰 Trade Events]
        PL[performance_logs<br/>⚡ Metrics]
        EL[error_logs<br/>❌ Errors]
        UAL[user_action_logs<br/>👤 User Activity]
    end
    
    subgraph "Views"
        RSA[recent_system_activity<br/>📊 Unified Activity]
    end
    
    %% Data Flow Relationships
    SI -->|enriches| MD
    MD -->|transforms to| FED
    FED -->|aggregates to| MV
    
    M -->|generates| P
    FED -.->|feeds| P
    P -.->|triggers| O
    O -->|executes as| F
    
    %% Logging Relationships
    SL -->|feeds| RSA
    TL -->|feeds| RSA
    PL -->|feeds| RSA
    EL -->|feeds| RSA
    
    %% Style
    classDef marketData fill:#e1f5fe
    classDef trading fill:#f3e5f5
    classDef logging fill:#fff3e0
    classDef views fill:#e8f5e8
    
    class SI,MD,FED,MV marketData
    class M,P,O,F trading
    class SL,TL,PL,EL,UAL logging
    class RSA views
```

## Detailed Entity Relationships

### Market Data Domain

```mermaid
erDiagram
    stock_info ||--o{ market_data : "has market data for"
    market_data ||--|| feature_engineered_data : "transforms to features"
    feature_engineered_data }o--|| mv_features_dashboard_summary : "aggregates to"
    
    stock_info {
        bigserial id PK
        varchar symbol UK "AAPL, GOOGL, etc"
        varchar company_name
        varchar sector "Technology, Healthcare"
        varchar industry
        bigint market_cap
        varchar country
        varchar currency
        varchar exchange
        varchar source "yahoo"
        timestamp created_at
        timestamp updated_at
    }
    
    market_data {
        bigserial id PK
        varchar symbol FK "References stock_info"
        timestamp timestamp
        decimal open
        decimal high
        decimal low
        decimal close
        bigint volume
        varchar source "yahoo, alpaca"
        timestamp created_at
        unique_constraint "symbol+timestamp+source"
    }
    
    feature_engineered_data {
        serial id PK
        varchar symbol
        timestamp timestamp
        double_precision open
        double_precision high
        double_precision low
        double_precision close
        double_precision volume
        double_precision returns
        double_precision rsi_1d
        double_precision price_ma_short
        double_precision bb_upper
        double_precision macd
        double_precision atr
        varchar feature_version "3.0"
        timestamp created_at
        timestamp updated_at
        unique_constraint "symbol+timestamp+source"
    }
    
    mv_features_dashboard_summary {
        varchar symbol PK
        timestamp latest_timestamp
        bigint total_records
        varchar latest_version
        float rsi_coverage
        float ma_coverage
    }
```

### Trading Domain

```mermaid
erDiagram
    models ||--o{ predictions : "generates"
    orders ||--o{ fills : "executes as"
    predictions }o--o{ orders : "may trigger"
    
    models {
        bigserial id PK
        varchar model_id UK "lstm_v1.0, rf_momentum"
        varchar name "Price Direction Model"
        varchar version "1.0"
        varchar model_type "LSTM, RandomForest"
        jsonb parameters "hyperparameters"
        jsonb metrics "accuracy, precision"
        varchar file_path
        varchar status "active, deprecated"
        timestamp created_at
        timestamp updated_at
    }
    
    predictions {
        bigserial id PK
        varchar prediction_id UK
        varchar model_id FK
        varchar symbol "AAPL"
        timestamp timestamp
        varchar prediction_type "price_direction, volatility"
        decimal prediction_value
        decimal confidence "0.0-1.0"
        jsonb features "input features used"
        timestamp created_at
    }
    
    orders {
        bigserial id PK
        varchar order_id UK "alpaca_order_123"
        varchar symbol "AAPL"
        varchar side "buy, sell"
        integer quantity
        varchar order_type "market, limit"
        decimal price
        varchar status "pending, filled, cancelled"
        varchar strategy "momentum, pairs"
        varchar model_id "references model used"
        timestamp created_at
        timestamp updated_at
    }
    
    fills {
        bigserial id PK
        varchar fill_id UK
        varchar order_id FK
        varchar symbol
        integer quantity "shares filled"
        decimal price "execution price"
        decimal commission
        timestamp timestamp "execution time"
        timestamp created_at
    }
```

### Logging Domain

```mermaid
erDiagram
    system_logs ||--o{ recent_system_activity : "contributes to"
    trading_events ||--o{ recent_system_activity : "contributes to"
    performance_logs ||--o{ recent_system_activity : "contributes to"
    error_logs ||--o{ recent_system_activity : "contributes to"
    
    system_logs {
        bigserial id PK
        timestamptz timestamp
        varchar level "DEBUG, INFO, WARNING, ERROR"
        varchar logger_name "dashboard, alpaca_service"
        varchar correlation_id "trace requests"
        text message
        varchar module
        varchar function_name
        integer line_number
        varchar thread_name
        integer process_id
        jsonb metadata
        timestamptz created_at
    }
    
    trading_events {
        bigserial id PK
        timestamptz timestamp
        varchar event_type "order_placed, signal_generated"
        varchar symbol
        varchar side "buy, sell"
        decimal quantity
        decimal price
        varchar order_id
        varchar strategy
        varchar correlation_id
        jsonb metadata
        timestamptz created_at
    }
    
    performance_logs {
        bigserial id PK
        timestamptz timestamp
        varchar operation_name "get_features, calculate_rsi"
        decimal duration_ms
        varchar status "success, error, timeout"
        varchar component "dashboard, ml_pipeline"
        varchar correlation_id
        decimal memory_usage_mb
        decimal cpu_usage_percent
        jsonb metadata
        timestamptz created_at
    }
    
    error_logs {
        bigserial id PK
        timestamptz timestamp
        varchar error_type "ConnectionError, ValidationError"
        text error_message
        text stack_trace
        varchar component
        varchar correlation_id
        varchar user_id
        varchar request_path
        jsonb metadata
        timestamptz created_at
    }
    
    user_action_logs {
        bigserial id PK
        timestamptz timestamp
        varchar action_type "page_view, api_call"
        varchar user_id
        varchar session_id
        inet ip_address
        text user_agent
        varchar request_path
        varchar request_method
        integer response_status
        decimal duration_ms
        varchar correlation_id
        jsonb metadata
        timestamptz created_at
    }
    
    recent_system_activity {
        varchar source "system_log, trading_event"
        timestamptz timestamp
        varchar severity "INFO, WARNING, ERROR"
        varchar component
        text description
        varchar correlation_id
        jsonb metadata
    }
```

## Data Flow Patterns

### 1. Market Data Ingestion Flow
```mermaid
sequenceDiagram
    participant YF as Yahoo Finance API
    participant MD as market_data
    participant FED as feature_engineered_data
    participant MV as mv_features_dashboard_summary
    participant D as Dashboard
    
    YF->>MD: OHLCV data
    Note over MD: Raw price/volume data
    
    MD->>FED: Feature engineering pipeline
    Note over FED: 100+ technical indicators<br/>RSI, MACD, Bollinger Bands<br/>Volatility measures<br/>Lagged features
    
    FED->>MV: Hourly aggregation
    Note over MV: Dashboard performance cache<br/>Latest values & coverage stats
    
    MV->>D: Sub-millisecond queries
    Note over D: Real-time dashboard<br/>Technical analysis charts
```

### 2. ML Prediction Flow
```mermaid
sequenceDiagram
    participant FED as feature_engineered_data
    participant M as models
    participant P as predictions
    participant O as orders
    participant F as fills
    participant A as Alpaca API
    
    FED->>M: Feature vectors
    Note over M: LSTM, Random Forest<br/>Trained models
    
    M->>P: Generate predictions
    Note over P: Price direction<br/>Volatility forecast<br/>Confidence scores
    
    P->>O: Trading signals
    Note over O: Buy/sell decisions<br/>Position sizing<br/>Risk management
    
    O->>A: Order placement
    A->>F: Execution confirmation
    Note over F: Fill prices<br/>Commission costs<br/>Partial fills
```

### 3. System Monitoring Flow
```mermaid
sequenceDiagram
    participant APP as Application
    participant SL as system_logs
    participant TL as trading_events
    participant PL as performance_logs
    participant EL as error_logs
    participant RSA as recent_system_activity
    participant MON as Monitoring Dashboard
    
    APP->>SL: Application logs
    APP->>TL: Trading events
    APP->>PL: Performance metrics
    APP->>EL: Error tracking
    
    SL->>RSA: Unified view
    TL->>RSA: Unified view
    PL->>RSA: Unified view
    EL->>RSA: Unified view
    
    RSA->>MON: System health
    Note over MON: Real-time monitoring<br/>Alert generation<br/>Performance analysis
```

## Key Constraints and Relationships

### Primary Keys
- All tables use `BIGSERIAL` for high-volume data handling
- `feature_engineered_data` uses `SERIAL` (sufficient for current volume)

### Foreign Key Relationships
- `fills.order_id` → `orders.order_id` (CASCADE DELETE)
- `predictions.model_id` → `models.model_id` (RESTRICT DELETE)

### Unique Constraints
- `market_data`: (symbol, timestamp, source)
- `feature_engineered_data`: (symbol, timestamp, source)
- `stock_info`: symbol

### Indexes (Performance Optimized ✅)
- **Primary indexes**: symbol+version+timestamp patterns
- **Covering indexes**: Include commonly queried columns
- **Partial indexes**: Recent data and market hours
- **Composite indexes**: Multi-column query patterns

## Data Volume & Growth Patterns

### Current State
- **feature_engineered_data**: 1.9M records (primary growth driver)
- **market_data**: High-frequency ingestion (hourly updates)
- **system_logs**: Moderate volume (application logging)
- **predictions**: Growing with ML model usage

### Growth Projections
- **feature_engineered_data**: ~2M records/year (1K symbols × 2K hours/year)
- **market_data**: ~500K records/year (base OHLCV data)
- **Logging tables**: ~10M records/year (system monitoring)

### Scaling Considerations
- **Partitioning**: Consider date-based partitioning for large tables
- **Archival**: Implement automated archival policies
- **Read Replicas**: Separate read/write workloads for high traffic