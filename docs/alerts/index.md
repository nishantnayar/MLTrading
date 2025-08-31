# MLTrading Alert System

The MLTrading Alert System provides comprehensive email notifications for critical system events, trading errors, and operational issues. Built with Yahoo Mail integration and designed to work seamlessly with Prefect workflows.

## 🔧 System Overview

The alert system consists of several key components:

- **AlertManager**: Central orchestration of all alerts
- **EmailService**: Yahoo Mail integration with circuit breaker protection
- **AlertFactory**: Pre-built alert templates for common scenarios
- **Rate Limiting**: Prevents alert spam with configurable limits
- **Severity Filtering**: Only sends alerts above configured importance level

## 📧 Email Configuration

### Prerequisites

1. **Yahoo Mail Account** with 2-factor authentication enabled
2. **App Password** generated for mail applications
3. **Environment Variables** configured in `.env` file

### Setup Steps

1. **Enable 2-Factor Authentication**:
   - Log into Yahoo Account Settings
   - Navigate to Security settings
   - Turn on 2-step verification

2. **Generate App Password**:
   - In Yahoo Account Security, find "App passwords"
   - Click "Generate new app password"
   - Select "Mail" as the application type
   - Copy the 16-character password

3. **Configure Environment Variables**:
   ```bash
   EMAIL_SENDER=your_email@yahoo.com
   EMAIL_PASSWORD=your_16_character_app_password
   ALERT_RECIPIENT_EMAIL=your_email@yahoo.com
   ```

4. **Update Configuration** (optional):
   ```yaml
   # config/config.yaml
   email_alerts:
     enabled: true
     smtp_server: "smtp.mail.yahoo.com"
     smtp_port: 587
     use_tls: true
     timeout: 30
   
   alerts:
     enabled: true
     min_severity: "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW, INFO
     rate_limiting:
       enabled: true
       max_alerts_per_hour: 10
       max_alerts_per_day: 50
   ```

## 🎯 Alert Severity Levels

| Level | Use Case | Example |
|-------|----------|---------|
| **CRITICAL** | System failures, security issues | Database down, unauthorized access |
| **HIGH** | Trading errors, major failures | Order execution failed, API timeouts |
| **MEDIUM** | Performance issues, warnings | Slow queries, circuit breaker opened |
| **LOW** | Minor issues, informational | Cache miss, retry successful |
| **INFO** | System events, notifications | System startup, deployment complete |

## 📊 Alert Categories

| Category | Purpose | Default Severity |
|----------|---------|------------------|
| **TRADING_ERRORS** | Trading system failures | HIGH |
| **SYSTEM_HEALTH** | Performance and availability | MEDIUM |
| **DATA_PIPELINE** | ETL and data processing | MEDIUM |
| **SECURITY** | Authentication and security | CRITICAL |
| **GENERAL** | Miscellaneous alerts | MEDIUM |

## 🚀 Usage Examples

### Basic Alert Sending

```python
from utils.alerts import AlertManager, AlertSeverity, AlertCategory
from config.settings import load_config

# Initialize
config = load_config()
alert_manager = AlertManager(config)

# Send basic alert
alert_manager.send_alert(
    title="Database Connection Issue",
    message="Failed to connect to PostgreSQL after 3 retries",
    severity=AlertSeverity.HIGH,
    category=AlertCategory.SYSTEM_HEALTH,
    component="DatabaseService",
    metadata={"retry_count": 3, "timeout": 30}
)
```

### Using Alert Factory

```python
from utils.alerts import AlertFactory, AlertManager

# Trading error
alert = AlertFactory.create_order_failure_alert(
    symbol="AAPL",
    order_type="MARKET",
    error_message="Insufficient funds",
    metadata={"amount": 1000, "account": "paper"}
)

alert_manager.process_alert(alert)

# Performance alert
alert = AlertFactory.create_performance_alert(
    metric_name="Query Response Time",
    current_value=5.2,
    threshold=3.0,
    component="DatabaseService"
)

alert_manager.process_alert(alert)
```

### Specialized Alert Methods

```python
# Trading error shorthand
alert_manager.send_trading_error_alert(
    error_message="Order execution failed: Market closed",
    component="AlpacaService",
    metadata={"symbol": "TSLA", "order_type": "LIMIT"}
)

# System health alert
alert_manager.send_system_health_alert(
    title="High Memory Usage",
    message="System memory usage above 85% threshold",
    severity=AlertSeverity.MEDIUM,
    component="SystemMonitor"
)

# Security alert (always CRITICAL)
alert_manager.send_security_alert(
    title="Multiple Failed Login Attempts",
    message="5 failed login attempts from IP: 192.168.1.100",
    component="AuthService"
)
```

## 🔄 Prefect Integration

The alert system is designed to work seamlessly with Prefect workflows:

### In Prefect Tasks

```python
from prefect import task, get_run_logger
from utils.alerts import get_alert_manager

@task
def process_data_with_alerts():
    logger = get_run_logger()
    alert_manager = get_alert_manager()
    
    try:
        # Your data processing logic
        result = process_market_data()
        
        # Success notification
        alert_manager.send_alert(
            title="Data Processing Complete",
            message=f"Processed {len(result)} records successfully",
            severity=AlertSeverity.INFO,
            category=AlertCategory.DATA_PIPELINE,
            component="DataProcessor"
        )
        
        return result
        
    except Exception as e:
        # Error notification
        alert_manager.send_alert(
            title="Data Processing Failed",
            message=f"Error processing data: {str(e)}",
            severity=AlertSeverity.HIGH,
            category=AlertCategory.DATA_PIPELINE,
            component="DataProcessor",
            metadata={"error_type": type(e).__name__}
        )
        raise
```

### In Prefect Flows

```python
from prefect import flow
from utils.alerts import get_alert_manager

@flow(name="feature-engineering-with-alerts")
def feature_engineering_flow():
    alert_manager = get_alert_manager()
    
    # Flow start notification
    alert_manager.send_alert(
        title="Feature Engineering Started",
        message="Feature engineering pipeline initiated",
        severity=AlertSeverity.INFO,
        category=AlertCategory.DATA_PIPELINE,
        component="FeatureEngineering"
    )
    
    try:
        # Execute tasks
        data = extract_data()
        features = engineer_features(data)
        store_features(features)
        
        # Success notification
        alert_manager.send_alert(
            title="Feature Engineering Complete",
            message=f"Generated {len(features)} features successfully",
            severity=AlertSeverity.INFO,
            category=AlertCategory.DATA_PIPELINE,
            component="FeatureEngineering"
        )
        
    except Exception as e:
        # Failure notification
        alert_manager.send_critical_alert(
            title="Feature Engineering Failed",
            message=f"Pipeline failed: {str(e)}",
            category=AlertCategory.DATA_PIPELINE,
            component="FeatureEngineering"
        )
        raise
```

## 🛡️ Error Handling & Resilience

### Circuit Breaker Protection

The email service includes circuit breaker protection:

- **Failure Threshold**: 3 consecutive failures
- **Recovery Timeout**: 5 minutes
- **Automatic Recovery**: Tests service availability periodically

### Rate Limiting

Prevents alert spam with configurable limits:

- **Hourly Limit**: Default 10 alerts per category
- **Daily Limit**: Default 50 alerts per category
- **Category-based**: Independent limits per alert category

### Fallback Mechanisms

When email service is unavailable:

1. **Logging**: All alerts logged to system logs
2. **Circuit Breaker**: Prevents repeated failure attempts
3. **Graceful Degradation**: System continues without email notifications
4. **Status Monitoring**: Alert service status available via API

## 📈 Monitoring & Statistics

### Get System Status

```python
status = alert_manager.get_status()
print(f"Email available: {status['email_service_available']}")
print(f"Rate limiting: {status['rate_limiting_enabled']}")
print(f"Min severity: {status['min_severity']}")
```

### Get Alert Statistics

```python
stats = alert_manager.get_stats()
print(f"Total alerts: {stats['total_alerts']}")
print(f"Sent: {stats['sent_alerts']}")
print(f"Failed: {stats['failed_alerts']}")
print(f"Rate limited: {stats['rate_limited_alerts']}")
```

### Email Service Health

```python
email_status = alert_manager.email_service.get_status()
print(f"Circuit breaker state: {email_status['circuit_breaker_state']}")
print(f"Failures: {email_status['circuit_breaker_failures']}")
```

## 🧪 Testing

### Basic System Test

```bash
# Test alert system without sending emails
python tests/test_alert_system.py
```

### Email Integration Test

```bash
# Send actual test email
python tests/test_email_alert.py
```

### Custom Test

```python
from utils.alerts import AlertManager
from config.settings import load_config

config = load_config()
alert_manager = AlertManager(config)

# Test email service
success = alert_manager.test_alert_system()
print(f"Alert system test: {'PASSED' if success else 'FAILED'}")
```

## 🔧 Configuration Reference

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_SENDER` | Yahoo email address | `user@yahoo.com` |
| `EMAIL_PASSWORD` | Yahoo app password | `abcd efgh ijkl mnop` |
| `ALERT_RECIPIENT_EMAIL` | Alert recipient email | `user@yahoo.com` |

### Configuration File Settings

```yaml
email_alerts:
  enabled: true                    # Enable/disable email alerts
  smtp_server: "smtp.mail.yahoo.com"  # SMTP server
  smtp_port: 587                   # SMTP port
  use_tls: true                    # Use TLS encryption
  timeout: 30                      # Connection timeout

alerts:
  enabled: true                    # Enable alert system
  min_severity: "MEDIUM"           # Minimum severity to send
  rate_limiting:
    enabled: true                  # Enable rate limiting
    max_alerts_per_hour: 10        # Max per hour per category
    max_alerts_per_day: 50         # Max per day per category
  alert_categories:
    trading_errors:
      enabled: true
      severity: "HIGH"
    system_health:
      enabled: true
      severity: "MEDIUM"
    data_pipeline:
      enabled: true
      severity: "MEDIUM"
    security:
      enabled: true
      severity: "CRITICAL"
```

## 🚨 Troubleshooting

### Common Issues

1. **Email Not Sending**:
   - Verify Yahoo app password (not regular password)
   - Check environment variables are loaded
   - Confirm 2-factor authentication is enabled

2. **Alerts Being Filtered**:
   - Check minimum severity level in config
   - Verify alert severity meets threshold
   - Review category-specific settings

3. **Rate Limiting Issues**:
   - Check rate limiting configuration
   - Review alert frequency
   - Consider adjusting limits for your use case

4. **Circuit Breaker Open**:
   - Wait for recovery timeout (5 minutes)
   - Check email service connectivity
   - Review circuit breaker statistics

### Debug Commands

```python
# Check email service availability
alert_manager.email_service.is_available()

# Test email connection
alert_manager.email_service.test_connection()

# Get detailed status
status = alert_manager.get_status()
stats = alert_manager.get_stats()
```

## 📚 API Reference

See the [Alert System API Documentation](api/alerts.md) for detailed method signatures and parameters.