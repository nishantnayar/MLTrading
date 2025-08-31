#!/usr/bin/env python3
"""
Demo script for the MLTrading Alert System.

This script demonstrates how to use the alert system to send various types of alerts.

Prerequisites:
1. Set environment variables:
   - EMAIL_SENDER: Your Yahoo email address
   - EMAIL_PASSWORD: Your Yahoo app password (not regular password)
   - ALERT_RECIPIENT_EMAIL: Email address to receive alerts

2. For Yahoo Mail, enable 2-factor authentication and create an app password:
   - Go to Yahoo Account Security settings
   - App passwords > Generate new app password
   - Select "Mail" as the app type and generate password

3. Update config/config.yaml if needed to customize alert settings

Usage:
    python examples/alert_system_demo.py
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.settings import load_config
from utils.alerts import AlertManager, AlertFactory, AlertSeverity, AlertCategory


def check_environment():
    """Check if environment is properly configured."""
    required_vars = ['EMAIL_SENDER', 'EMAIL_PASSWORD', 'ALERT_RECIPIENT_EMAIL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables and try again.")
        return False
    
    print("✅ Environment variables configured")
    return True


def demo_basic_alerts(alert_manager):
    """Demonstrate basic alert functionality."""
    print("\n" + "="*50)
    print("📧 Testing Basic Alerts")
    print("="*50)
    
    # Test different severity levels
    alerts_to_send = [
        {
            'title': 'System Health Check',
            'message': 'This is an INFO level alert for system monitoring.',
            'severity': AlertSeverity.INFO,
            'category': AlertCategory.SYSTEM_HEALTH
        },
        {
            'title': 'Data Processing Warning',
            'message': 'Feature engineering process took longer than expected.',
            'severity': AlertSeverity.MEDIUM,
            'category': AlertCategory.DATA_PIPELINE
        },
        {
            'title': 'Trading System Error',
            'message': 'Failed to execute order due to insufficient funds.',
            'severity': AlertSeverity.HIGH,
            'category': AlertCategory.TRADING_ERRORS
        }
    ]
    
    for alert_info in alerts_to_send:
        print(f"Sending {alert_info['severity'].value} alert: {alert_info['title']}")
        
        status = alert_manager.send_alert(
            title=alert_info['title'],
            message=alert_info['message'],
            severity=alert_info['severity'],
            category=alert_info['category'],
            component="AlertDemo"
        )
        
        print(f"  Status: {status.value}")


def demo_specialized_alerts(alert_manager):
    """Demonstrate specialized alert types."""
    print("\n" + "="*50)
    print("🔧 Testing Specialized Alerts")
    print("="*50)
    
    # Trading error alert
    print("Sending trading error alert...")
    status = alert_manager.send_trading_error_alert(
        error_message="Order execution failed: Market is closed",
        component="AlpacaService",
        metadata={"symbol": "AAPL", "order_type": "MARKET"}
    )
    print(f"  Trading error alert status: {status.value}")
    
    # System health alert
    print("Sending system health alert...")
    status = alert_manager.send_system_health_alert(
        title="High Memory Usage",
        message="System memory usage is above 85% threshold",
        severity=AlertSeverity.MEDIUM,
        component="SystemMonitor",
        metadata={"memory_usage": "87%", "threshold": "85%"}
    )
    print(f"  System health alert status: {status.value}")
    
    # Data pipeline alert
    print("Sending data pipeline alert...")
    status = alert_manager.send_data_pipeline_alert(
        title="Feature Engineering Completed",
        message="Feature engineering pipeline completed successfully with 1,250 records processed",
        severity=AlertSeverity.INFO,
        component="FeatureEngineering",
        metadata={"records_processed": 1250, "processing_time": "2.3 minutes"}
    )
    print(f"  Data pipeline alert status: {status.value}")


def demo_alert_factory(alert_manager):
    """Demonstrate using the alert factory."""
    print("\n" + "="*50)
    print("🏭 Testing Alert Factory")
    print("="*50)
    
    # Create various alerts using the factory
    alerts = [
        AlertFactory.create_order_failure_alert(
            symbol="TSLA",
            order_type="LIMIT",
            error_message="Order rejected by broker",
            metadata={"price": 250.50, "quantity": 100}
        ),
        AlertFactory.create_database_connection_alert(
            error_message="Connection timeout after 30 seconds",
            component="PostgreSQL"
        ),
        AlertFactory.create_api_error_alert(
            api_name="Yahoo Finance",
            error_message="Rate limit exceeded (429)",
            component="YahooCollector",
            metadata={"endpoint": "/v8/finance/chart", "retry_after": 60}
        ),
        AlertFactory.create_performance_alert(
            metric_name="Response Time",
            current_value=2.5,
            threshold=2.0,
            component="WebAPI",
            metadata={"endpoint": "/api/data", "method": "GET"}
        )
    ]
    
    for alert in alerts:
        print(f"Sending factory alert: {alert.title}")
        status = alert_manager.process_alert(alert)
        print(f"  Status: {status.value}")


def demo_rate_limiting(alert_manager):
    """Demonstrate rate limiting functionality."""
    print("\n" + "="*50)
    print("⏰ Testing Rate Limiting")
    print("="*50)
    
    # Send multiple alerts of the same category to trigger rate limiting
    print("Sending multiple alerts to test rate limiting...")
    
    for i in range(5):
        status = alert_manager.send_alert(
            title=f"Rate Limit Test {i+1}",
            message=f"This is test alert #{i+1} to demonstrate rate limiting",
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM_HEALTH,
            component="RateLimitDemo"
        )
        print(f"  Alert {i+1} status: {status.value}")


def show_system_status(alert_manager):
    """Show current system status and statistics."""
    print("\n" + "="*50)
    print("📊 System Status and Statistics")
    print("="*50)
    
    # Show system status
    status = alert_manager.get_status()
    print("System Status:")
    print(f"  Enabled: {status['enabled']}")
    print(f"  Min Severity: {status['min_severity']}")
    print(f"  Email Service Available: {status['email_service_available']}")
    print(f"  Rate Limiting Enabled: {status['rate_limiting_enabled']}")
    
    # Show statistics
    stats = alert_manager.get_stats()
    print(f"\nAlert Statistics:")
    print(f"  Total Alerts: {stats['total_alerts']}")
    print(f"  Sent: {stats['sent_alerts']}")
    print(f"  Failed: {stats['failed_alerts']}")
    print(f"  Rate Limited: {stats['rate_limited_alerts']}")
    print(f"  Filtered: {stats['filtered_alerts']}")
    
    if 'alerts_by_severity' in stats:
        print(f"\nAlerts by Severity:")
        for severity, count in stats['alerts_by_severity'].items():
            print(f"  {severity}: {count}")
    
    if 'alerts_by_category' in stats:
        print(f"\nAlerts by Category:")
        for category, count in stats['alerts_by_category'].items():
            print(f"  {category}: {count}")


def main():
    """Main demo function."""
    print("🚀 MLTrading Alert System Demo")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        return 1
    
    # Load configuration
    try:
        config = load_config()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return 1
    
    # Initialize alert manager
    try:
        alert_manager = AlertManager(config)
        print("✅ Alert manager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize alert manager: {e}")
        return 1
    
    # Test email service
    print("\n📧 Testing email service connection...")
    if alert_manager.email_service.test_connection():
        print("✅ Email service test passed")
    else:
        print("❌ Email service test failed")
        print("Check your email configuration and credentials")
        return 1
    
    # Run demonstrations
    try:
        demo_basic_alerts(alert_manager)
        demo_specialized_alerts(alert_manager)
        demo_alert_factory(alert_manager)
        demo_rate_limiting(alert_manager)
        show_system_status(alert_manager)
        
        print("\n" + "="*50)
        print("✅ Demo completed successfully!")
        print("Check your email for the test alerts.")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())