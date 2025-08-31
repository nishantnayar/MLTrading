#!/usr/bin/env python3
"""
Standalone Alert System Demo - No Prefect Server Required

This demo shows the alert system functionality without needing Prefect server running.
It demonstrates all the core features and integration capabilities.
"""

import sys
import os
from datetime import datetime, timezone
import yaml
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def load_config():
    """Load configuration - simplified for demo."""
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path) as f:
        return yaml.safe_load(f)

def demo_basic_alerts():
    """Demonstrate basic alert functionality."""
    print("="*60)
    print("BASIC ALERT SYSTEM DEMO")
    print("="*60)
    
    from utils.alerts import AlertManager, AlertSeverity, AlertCategory, AlertFactory
    
    # Load environment and config
    load_env_file()
    config = load_config()
    
    # Initialize alert manager
    alert_manager = AlertManager(config)
    print(f"[OK] Alert manager initialized")
    print(f"[OK] Email service available: {alert_manager.email_service.is_available()}")
    
    # Test different alert types
    alerts = [
        {
            "title": "System Health Check",
            "message": "Routine system health check completed successfully",
            "severity": AlertSeverity.INFO,
            "category": AlertCategory.SYSTEM_HEALTH
        },
        {
            "title": "Data Pipeline Warning",
            "message": "Feature engineering took longer than expected (15.2s vs 10s threshold)",
            "severity": AlertSeverity.MEDIUM,
            "category": AlertCategory.DATA_PIPELINE,
            "metadata": {"duration": 15.2, "threshold": 10.0}
        },
        {
            "title": "Trading Error",
            "message": "Order execution failed: Insufficient buying power",
            "severity": AlertSeverity.HIGH,
            "category": AlertCategory.TRADING_ERRORS,
            "metadata": {"symbol": "AAPL", "amount": 10000, "available": 5000}
        },
        {
            "title": "Security Alert",
            "message": "Multiple failed login attempts detected from IP 192.168.1.100",
            "severity": AlertSeverity.CRITICAL,
            "category": AlertCategory.SECURITY,
            "metadata": {"ip": "192.168.1.100", "attempts": 5}
        }
    ]
    
    print(f"\nSending {len(alerts)} test alerts...")
    results = []
    
    for i, alert_config in enumerate(alerts, 1):
        print(f"  {i}. {alert_config['severity'].value}: {alert_config['title']}")
        status = alert_manager.send_alert(**alert_config)
        results.append((alert_config['title'], status.value))
        print(f"     Status: {status.value}")
        time.sleep(0.5)  # Small delay between alerts
    
    # Show statistics
    stats = alert_manager.get_stats()
    print(f"\nAlert Statistics:")
    print(f"  Total alerts: {stats['total_alerts']}")
    print(f"  Sent successfully: {stats['sent_alerts']}")
    print(f"  Failed: {stats['failed_alerts']}")
    print(f"  Rate limited: {stats['rate_limited_alerts']}")
    print(f"  Filtered: {stats['filtered_alerts']}")
    
    return len([r for r in results if r[1] == 'sent'])

def demo_alert_factory():
    """Demonstrate alert factory usage."""
    print("\n" + "="*60)
    print("ALERT FACTORY DEMO")
    print("="*60)
    
    from utils.alerts import AlertFactory, get_alert_manager
    
    alert_manager = get_alert_manager()
    if not alert_manager:
        print("[ERROR] Alert manager not available")
        return 0
    
    # Create various alerts using factory methods
    factory_alerts = [
        AlertFactory.create_order_failure_alert(
            symbol="TSLA",
            order_type="LIMIT",
            error_message="Order rejected: Price too far from current market",
            metadata={"price": 200.00, "market_price": 245.50}
        ),
        AlertFactory.create_database_connection_alert(
            error_message="Connection pool exhausted after 30 seconds",
            metadata={"pool_size": 20, "active_connections": 20}
        ),
        AlertFactory.create_api_error_alert(
            api_name="Yahoo Finance",
            error_message="Rate limit exceeded: 429 Too Many Requests",
            component="DataCollector",
            metadata={"requests_per_hour": 2000, "limit": 2000}
        ),
        AlertFactory.create_performance_alert(
            metric_name="Database Query Time",
            current_value=5.2,
            threshold=3.0,
            component="DatabaseService",
            metadata={"query": "SELECT * FROM market_data", "table_size": "1.2M rows"}
        ),
        AlertFactory.create_system_startup_alert(
            component="MLTrading System",
            version="2.0.0",
            metadata={"startup_time": "12.3s", "environment": "development"}
        )
    ]
    
    print(f"Processing {len(factory_alerts)} factory-created alerts...")
    sent_count = 0
    
    for i, alert in enumerate(factory_alerts, 1):
        print(f"  {i}. {alert.severity.value}: {alert.title}")
        status = alert_manager.process_alert(alert)
        if status.value == 'sent':
            sent_count += 1
        print(f"     Status: {status.value}")
        time.sleep(0.5)
    
    return sent_count

def demo_prefect_integration():
    """Demonstrate Prefect integration features (without actual Prefect)."""
    print("\n" + "="*60)
    print("PREFECT INTEGRATION DEMO (Simulated)")
    print("="*60)
    
    from utils.alerts import (
        initialize_alert_manager, 
        get_alert_manager,
        alert_on_failure,
        alert_on_long_runtime,
        AlertSeverity,
        AlertCategory
    )
    
    config = load_config()
    alert_manager = initialize_alert_manager(config)
    
    print("[OK] Prefect-aware alert manager initialized")
    
    # Simulate Prefect flow lifecycle
    flow_name = "feature-engineering-demo"
    
    # Flow start
    print(f"\n1. Simulating flow start: {flow_name}")
    status = alert_manager.send_flow_start_alert(
        flow_name=flow_name,
        metadata={"scheduled": True, "environment": "development"}
    )
    print(f"   Flow start alert: {status.value}")
    
    # Simulate some processing time
    time.sleep(1)
    
    # Flow success
    print(f"2. Simulating flow success: {flow_name}")
    status = alert_manager.send_flow_success_alert(
        flow_name=flow_name,
        duration=45.2,
        metadata={"features_generated": 95, "records_processed": 1250}
    )
    print(f"   Flow success alert: {status.value}")
    
    # Simulate error scenario
    print(f"3. Simulating flow failure: {flow_name}")
    error = ValueError("Simulated data processing error")
    status = alert_manager.send_flow_failure_alert(
        flow_name=flow_name,
        error=error,
        metadata={"stage": "feature_calculation", "retry_count": 0}
    )
    print(f"   Flow failure alert: {status.value}")
    
    # Test decorators
    print(f"4. Testing alert decorators...")
    
    @alert_on_failure(severity=AlertSeverity.MEDIUM, send_success_alert=True)
    def demo_function_success():
        """Demo function that succeeds."""
        time.sleep(1)
        return {"result": "success", "processing_time": 1.0}
    
    @alert_on_long_runtime(threshold_seconds=0.5)
    def demo_function_long():
        """Demo function with long runtime."""
        time.sleep(1.0)  # Exceed threshold
        return "completed"
    
    @alert_on_failure(severity=AlertSeverity.HIGH)
    def demo_function_failure():
        """Demo function that fails."""
        raise RuntimeError("Simulated function failure")
    
    # Test successful function
    print("   Testing successful function with decorator...")
    result = demo_function_success()
    print(f"   Function result: {result}")
    
    # Test long runtime function
    print("   Testing long runtime function...")
    result = demo_function_long()
    print(f"   Long runtime result: {result}")
    
    # Test failing function
    print("   Testing failing function...")
    try:
        demo_function_failure()
    except RuntimeError as e:
        print(f"   Expected error caught: {e}")
    
    return 3  # Number of main alerts sent

def demo_rate_limiting():
    """Demonstrate rate limiting functionality."""
    print("\n" + "="*60)
    print("RATE LIMITING DEMO")
    print("="*60)
    
    from utils.alerts import get_alert_manager, AlertSeverity, AlertCategory
    
    alert_manager = get_alert_manager()
    if not alert_manager:
        print("[ERROR] Alert manager not available")
        return 0
    
    print("Sending multiple alerts quickly to test rate limiting...")
    
    sent_count = 0
    rate_limited_count = 0
    
    for i in range(8):  # Send 8 alerts quickly
        status = alert_manager.send_alert(
            title=f"Rate Limit Test #{i+1}",
            message=f"This is test alert number {i+1} for rate limiting demonstration",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.SYSTEM_HEALTH,
            component="RateLimitDemo",
            metadata={"test_number": i+1}
        )
        
        print(f"  Alert {i+1}: {status.value}")
        
        if status.value == 'sent':
            sent_count += 1
        elif status.value == 'rate_limited':
            rate_limited_count += 1
        
        time.sleep(0.2)  # Small delay
    
    print(f"\nRate limiting results:")
    print(f"  Alerts sent: {sent_count}")
    print(f"  Alerts rate limited: {rate_limited_count}")
    
    return sent_count

def main():
    """Run complete alert system demonstration."""
    print("MLTrading Alert System - Comprehensive Demo")
    print("="*80)
    
    try:
        # Check email configuration
        load_env_file()
        from utils.alerts import AlertManager
        config = load_config()
        temp_manager = AlertManager(config)
        email_available = temp_manager.email_service.is_available()
        
        print(f"Email service configured: {email_available}")
        if not email_available:
            print("\nTo receive actual emails, configure these environment variables:")
            print("  EMAIL_SENDER=your_email@yahoo.com")
            print("  EMAIL_PASSWORD=your_yahoo_app_password")
            print("  ALERT_RECIPIENT_EMAIL=your_email@yahoo.com")
        print()
        
        # Run all demos
        results = {}
        
        results['basic'] = demo_basic_alerts()
        results['factory'] = demo_alert_factory()
        results['prefect'] = demo_prefect_integration()
        results['rate_limiting'] = demo_rate_limiting()
        
        # Final summary
        print("\n" + "="*80)
        print("DEMO SUMMARY")
        print("="*80)
        
        total_sent = sum(results.values())
        
        print(f"Basic Alerts Demo: {results['basic']} alerts sent")
        print(f"Factory Demo: {results['factory']} alerts sent")
        print(f"Prefect Integration Demo: {results['prefect']} alerts sent")
        print(f"Rate Limiting Demo: {results['rate_limiting']} alerts sent")
        print(f"\nTotal alerts sent: {total_sent}")
        
        # Show final statistics
        final_alert_manager = temp_manager
        final_stats = final_alert_manager.get_stats()
        
        print(f"\nFinal System Statistics:")
        print(f"  Total alerts processed: {final_stats['total_alerts']}")
        print(f"  Successfully sent: {final_stats['sent_alerts']}")
        print(f"  Failed to send: {final_stats['failed_alerts']}")
        print(f"  Rate limited: {final_stats['rate_limited_alerts']}")
        print(f"  Filtered by severity: {final_stats['filtered_alerts']}")
        
        if email_available and final_stats['sent_alerts'] > 0:
            print(f"\n[SUCCESS] {final_stats['sent_alerts']} emails were sent to your inbox!")
            print("Check your email for the test alerts.")
        elif final_stats['sent_alerts'] > 0:
            print(f"\n[INFO] {final_stats['sent_alerts']} alerts were processed but not emailed (service not configured)")
        
        print("\n[SUCCESS] All demos completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())