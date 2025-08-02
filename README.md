# ML Trading System

A comprehensive machine learning-based trading system with real-time dashboard and database integration.

## Features

- **Real-time Dashboard**: Interactive web interface with live market data
- **Database Integration**: PostgreSQL backend with market_data table
- **Multi-page UI**: Dashboard, Logs, and Settings pages
- **Theme Toggle**: Light and dark theme support
- **Responsive Design**: Mobile-friendly interface
- **Symbol Selection**: Switch between different stock symbols

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Conda environment (recommended: `trading_env`)

### Installation

1. **Activate conda environment**:
   ```bash
   conda activate trading_env
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**:
   ```bash
   # Make sure PostgreSQL is running with these credentials:
   # Host: localhost
   # Port: 5432
   # Database: mltrading
   # User: postgres
   # Password: nishant
   
   # Create tables (safe for both new and existing databases):
   psql -h localhost -U postgres -d mltrading -f src/data/storage/create_tables.sql
   ```

4. **Run the application**:
   ```bash
   python run_ui.py
   ```

### Access the UI

- **Dashboard**: http://localhost:8050
- **API Documentation**: http://localhost:8000/docs

## Database Schema

The system uses PostgreSQL with the following main tables:

- **market_data**: Stock price and volume data
- **stock_info**: Stock information including sector and industry data
- **orders**: Trading orders
- **fills**: Order executions
- **models**: ML model metadata
- **predictions**: Model predictions

## Features

### Dashboard
- Real-time market data visualization
- Price charts and volume analysis
- Trading signals and statistics
- Symbol selection (AAPL, GOOGL, MSFT, TSLA, AMZN)

### Navigation
- Collapsible sidebar navigation
- Theme toggle (light/dark)
- Responsive mobile design

### Data Integration
- Connected to PostgreSQL market_data table
- Real-time data updates
- Historical data analysis

## Development

### Project Structure
```
MLTrading/
├── src/
│   ├── dashboard/          # Dash web interface
│   ├── api/               # FastAPI backend
│   ├── data/              # Database and data processing
│   │   ├── collectors/    # Data collection modules
│   │   ├── processors/    # Data processing modules
│   │   └── storage/       # Database storage modules
│   └── utils/             # Utilities and helpers
├── scripts/               # Setup and utility scripts
├── docs/                  # Documentation
├── tests/                 # Test suite
└── requirements.txt       # Python dependencies
```

### Testing
- **Quick API Check**: `python run_tests.py --type quick`
- **Run All Tests**: `python run_tests.py --type all`
- **API Tests**: `python run_tests.py --type api`
- **Full Testing Documentation**: See [docs/TESTING.md](docs/TESTING.md)

### Key Components

- **Dashboard**: `src/dashboard/app.py` - Main Dash application
- **Data Service**: `src/dashboard/services/data_service.py` - Database integration
- **Database**: `src/data/storage/database.py` - PostgreSQL connection
- **API**: `src/api/main.py` - FastAPI backend

## Configuration

Database connection settings are in `src/data/storage/database.py`:
- Host: localhost
- Port: 5432
- Database: mltrading
- User: postgres
- Password: nishant

## Troubleshooting

### Database Connection Issues
1. Ensure PostgreSQL is running
2. Check database credentials in `src/data/storage/database.py`
3. Run `python scripts/setup_database.py` to create tables

### UI Issues
1. Check if all dependencies are installed: `pip install -r requirements.txt`
2. Ensure both FastAPI and Dash are running: `python run_ui.py`
3. Check browser console for JavaScript errors

## Next Steps

1. Add real-time data streaming
2. Implement trading algorithms
3. Add user authentication
4. Create portfolio management features
5. Add more technical indicators
6. Implement backtesting framework 