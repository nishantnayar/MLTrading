# Configuration Guide

Learn how to configure MLTrading using the unified configuration system.

## Unified Configuration

MLTrading now uses a single unified configuration file `config/config.yaml` that consolidates all system settings with type validation.

### Main Configuration File

Edit `config/config.yaml` to configure the entire system:

```yaml
# Database Configuration
database:
  host: localhost
  port: 5432
  name: mltrading
  user: postgres
  # password loaded from DB_PASSWORD environment variable
  min_connections: 1
  max_connections: 20
  timeout: 30

# Alpaca Trading Configuration
alpaca:
  paper_trading:
    base_url: "https://paper-api.alpaca.markets"
    # Credentials: ALPACA_PAPER_API_KEY, ALPACA_PAPER_SECRET_KEY
  live_trading:
    base_url: "https://api.alpaca.markets"
    # Credentials: ALPACA_LIVE_API_KEY, ALPACA_LIVE_SECRET_KEY

# Trading Settings
trading:
  mode: "paper"              # "paper" or "live" - START WITH PAPER!
  default_order_type: "market"
  default_time_in_force: "day"
  max_order_value: 10000     # Maximum $ per order

# Risk Management
risk:
  max_daily_orders: 25       # Limit orders per day
  max_position_size: 1000    # Max shares per position
  emergency_stop: false      # Emergency stop all trading

# Deployment Configuration
deployments:
  feature-engineering:
    name: "feature-engineering"
    display_name: "Feature Engineering (Comprehensive)"
    priority: 1
    schedule_type: "comprehensive_schedule"
    expected_runtime_minutes: 20
    alert_threshold_hours: 3

  yahoo-data-collection:
    name: "yahoo-data-collection"
    display_name: "Yahoo Finance Data Collection"
    priority: 2
    schedule_type: "market_hours"
    expected_runtime_minutes: 8
    alert_threshold_hours: 2

# Enhanced Error Handling
circuit_breakers:
  yahoo_api:
    failure_threshold: 5
    recovery_timeout: 120
    timeout: 30
  database:
    failure_threshold: 3
    recovery_timeout: 60
    timeout: 10

retry_settings:
  api_calls:
    max_attempts: 4
    base_delay: 1.0
    max_delay: 60.0
  database_operations:
    max_attempts: 3
    base_delay: 0.5
    max_delay: 10.0
```

## Environment Variables

Create a `.env` file for sensitive credentials:

```bash
# Database Password
DB_PASSWORD=your_password

# Alpaca API Credentials
ALPACA_PAPER_API_KEY=your_paper_key
ALPACA_PAPER_SECRET_KEY=your_paper_secret

# For live trading (use with extreme caution)
ALPACA_LIVE_API_KEY=your_live_key
ALPACA_LIVE_SECRET_KEY=your_live_secret
```

## Symbol Configuration

Edit `config/symbols.txt` to specify which stocks to track:

```
# Add one symbol per line
AAPL
GOOGL
MSFT
TSLA
# Lines starting with # are comments
```

## Configuration Management

The unified configuration system provides:

- **Type Safety**: Pydantic validation ensures correct data types
- **Environment Integration**: Automatic loading of sensitive values from environment variables
- **Single Source**: All settings in one file instead of scattered configs
- **Auto-Reload**: Configuration changes are detected automatically

### Accessing Configuration in Code

```python
from src.config.settings import get_settings

settings = get_settings()
print(f"Database: {settings.database.host}:{settings.database.port}")
print(f"Trading mode: {settings.trading.mode}")
```

## Prefect Configuration

Set up Prefect for workflow orchestration:

1. **Initialize Prefect**:
   ```bash
   prefect server start  # In separate terminal
   ```

2. **Create work pool**:
   ```bash
   prefect work-pool create features-pool --type process
   ```

3. **Deploy workflows**:
   ```bash
   cd deployments
   prefect deploy --all
   ```

## Database Setup

1. **Create database**:
   ```sql
   CREATE DATABASE mltrading;
   CREATE USER mltrading_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE mltrading TO mltrading_user;
   ```

2. **Tables are created automatically** when you first run the data collector.

## Enhanced Error Handling

The system includes circuit breakers and retry logic:

### Circuit Breakers
Protect against external service failures:
- **Yahoo API**: 5 failures triggers 120-second circuit break
- **Database**: 3 failures triggers 60-second circuit break

### Retry Logic
Automatic retry with exponential backoff:
- **API calls**: Up to 4 attempts with increasing delays
- **Database ops**: Up to 3 attempts with shorter delays

## Security

- Keep API keys in `.env` file (never commit to git)
- Use paper trading URLs for testing (`mode: "paper"`)
- Restrict database access to application user only
- Use HTTPS in production deployments
- Emergency stop feature for immediate trading halt (`emergency_stop: true`)