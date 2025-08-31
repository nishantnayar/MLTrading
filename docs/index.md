# MLTrading System Documentation

Welcome to the MLTrading system - a comprehensive machine learning-based trading platform with advanced feature engineering and automated deployment capabilities.

## 🚀 System Overview

MLTrading is a production-ready trading system that combines:

- **Real-time data collection** from Yahoo Finance
- **Advanced feature engineering** with 90+ ML-ready features  
- **Interactive dashboard** with professional-grade charts
- **Automated deployment** using Prefect 3.x workflows
- **Robust database architecture** with PostgreSQL
- **Email alerting system** with Yahoo Mail integration

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

### Alert System
- **Multi-level severity**: Critical, High, Medium, Low, Info alerts
- **Email notifications**: Yahoo Mail integration with app passwords
- **Rate limiting**: Prevents alert spam with configurable limits
- **Circuit breaker**: Protects against email service failures
- **Categorized alerts**: Trading errors, system health, data pipeline, security

## 🏗️ Architecture

The system uses a modular architecture with:

- **Data Layer**: PostgreSQL with optimized connection pooling
- **Processing Layer**: Feature engineering with subprocess isolation  
- **Service Layer**: Unified data services with caching
- **Presentation Layer**: Dash-based interactive dashboard
- **Orchestration Layer**: Prefect 3.x for workflow management
- **Alert Layer**: Email notification system with failure resilience

## 📚 Documentation Sections

### [Architecture](architecture/SYSTEM_ARCHITECTURE.md)
Detailed system design and component interactions

### [Deployment](deployment/deployments.md) 
Prefect deployment configuration and management

### [Troubleshooting](troubleshooting/TROUBLESHOOTING-CONNECTION-ISSUES.md)
Common issues and solutions

### [Testing](testing/regression_test_manual.md)
Manual testing procedures and checklists

### [Database](database/DATABASE_SCHEMA.md)
Database Schema details

## 🚀 Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure environment**: Copy `.env.example` to `.env` and fill in your credentials
3. **Configure system**: Edit `config/config.yaml` with your database settings
4. **Set up email alerts**: Configure Yahoo Mail app password in `.env` file
5. **Deploy workflows**: `cd deployments && prefect deploy --all`
6. **Start dashboard**: `python scripts/run_ui.py`
7. **Monitor**: Access dashboard at http://localhost:8050

### Email Alert Setup (Yahoo Mail)

1. **Enable 2-factor authentication** on your Yahoo account
2. **Generate app password**: 
   - Go to Yahoo Account Security → App passwords
   - Create password for "Mail" application
3. **Configure environment variables**:
   ```bash
   EMAIL_SENDER=your_email@yahoo.com
   EMAIL_PASSWORD=your_16_char_app_password
   ALERT_RECIPIENT_EMAIL=your_email@yahoo.com
   ```
4. **Test alerts**: Run `python tests/test_alert_system.py` to verify setup
5. **Test email sending**: Run `python tests/test_email_alert.py` to send actual test email

## ⚙️ Configuration

All system settings are now managed through a single `config/config.yaml` file:

```yaml
# Database settings
database:
  host: localhost
  port: 5432
  name: mltrading
  # password loaded from DB_PASSWORD environment variable

# Trading configuration  
trading:
  mode: "paper"  # Start with paper trading
  max_order_value: 10000

# Enhanced error handling
circuit_breakers:
  yahoo_api:
    failure_threshold: 5
    recovery_timeout: 120

# Email alerts
email_alerts:
  enabled: true
  smtp_server: "smtp.mail.yahoo.com"
  
# Alert configuration
alerts:
  enabled: true
  min_severity: "MEDIUM"
  rate_limiting:
    enabled: true
    max_alerts_per_hour: 10
```

## 💡 Key Components

| Component | Purpose | Status |
|-----------|---------|---------|
| Yahoo Collector | Market data ingestion | ✅ Production |
| Feature Engineering | ML feature generation | ✅ Production |
| Dashboard | Interactive visualization | ✅ Production |
| Sequential Flow | Automated pipeline | ✅ Active |
| Alert System | Email notifications | ✅ Production |

## 📈 Data Flow

```
Yahoo Finance → Data Collection → Feature Engineering → Dashboard
     ↓              ↓                    ↓              ↓
  Raw OHLCV    PostgreSQL DB      90+ Features    Real-time UI
```

---

*This documentation is built with MkDocs and automatically updated with system changes.*