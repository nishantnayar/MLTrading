# Quick Start Guide

Get up and running with MLTrading in minutes.

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd MLTrading
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure system**:
   Create `.env` file with your database credentials:
   ```bash
   # Database password (required)
   DB_PASSWORD=your_password
   
   # Alpaca API keys (optional, for trading features)
   ALPACA_PAPER_API_KEY=your_paper_key
   ALPACA_PAPER_SECRET_KEY=your_paper_secret
   ```
   
   Edit `config/config.yaml` if you need to change default settings:
   ```yaml
   database:
     host: localhost
     port: 5432
     name: mltrading
     user: postgres
   ```

4. **Initialize database**:
   ```bash
   python scripts/test_db_connection.py
   ```

## First Run

1. **Start data collection**:
   ```bash
   python scripts/run_yahoo_collector.py
   ```

2. **Run feature engineering**:
   ```bash
   python scripts/feature_engineering_processor.py
   ```

3. **Launch dashboard**:
   ```bash
   python scripts/run_ui.py
   ```

4. **Access dashboard**: Open http://localhost:8050

## Deployment (Optional)

For automated scheduling:

1. **Install Prefect**:
   ```bash
   pip install prefect
   ```

2. **Deploy workflows**:
   ```bash
   cd deployments
   prefect deploy --all
   ```

3. **Start worker**:
   ```bash
   prefect worker start --pool features-pool
   ```

## Next Steps

- Review [Architecture](../architecture/SYSTEM_ARCHITECTURE.md) to understand the system
- Check [API Documentation](../api/index.md) for development details
- See [Troubleshooting](../troubleshooting/TROUBLESHOOTING-CONNECTION-ISSUES.md) if you encounter issues