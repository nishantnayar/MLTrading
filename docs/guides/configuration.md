# Configuration Guide

Learn how to configure MLTrading for your environment.

## Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mltrading
DB_USER=your_username
DB_PASSWORD=your_password

# Trading Configuration (Optional)
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Paper trading

# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8050
DASHBOARD_DEBUG=true
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

## Deployment Configuration

Configure deployments in `config/deployments_config.yaml`:

```yaml
deployments:
  feature-engineering:
    name: "feature-engineering"
    display_name: "Feature Engineering"
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

3. **Configure deployment**:
   Edit `deployments/prefect.yaml` for your environment:
   ```yaml
   pull:
   - prefect.deployments.steps.set_working_directory:
       directory: /your/project/path
   ```

## Database Setup

1. **Create database**:
   ```sql
   CREATE DATABASE mltrading;
   CREATE USER mltrading_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE mltrading TO mltrading_user;
   ```

2. **Tables are created automatically** when you first run the data collector.

## Logging Configuration

Logs are stored in `logs/` folder. Configure log levels in code or use production logging:

```python
from src.utils.production_logging import setup_production_logging
setup_production_logging("INFO")
```

## Performance Tuning

### Database Connection Pool

Edit connection settings in `src/utils/connection_config.py`:

```python
# Connection pool settings
MIN_CONNECTIONS = 1
MAX_CONNECTIONS = 5
CONNECTION_TIMEOUT = 30
```

### Feature Engineering

Adjust batch sizes in `scripts/feature_engineering_processor.py`:

```python
# Process symbols in batches
BATCH_SIZE = 10  # Reduce if memory issues
```

## Security

- Keep API keys in `.env` file (never commit to git)
- Use paper trading URLs for testing
- Restrict database access to application user only
- Use HTTPS in production deployments