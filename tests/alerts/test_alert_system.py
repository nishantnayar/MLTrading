#!/usr/bin/env python3
"""
Comprehensive test suite for the MLTrading Alert System.
"""

import sys
import os
from datetime import datetime, timezone
import yaml
from pathlib import Path

# Add src to path (adjust path since we're now in tests folder)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        print(f"Loading environment from {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("[OK] Environment variables loaded from .env file")
    else:
        print("[INFO] No .env file found")

def load_config():
    """Load configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def test_alert_system_basic():
    """Test basic alert system functionality without sending emails."""
    print("Testing Basic Alert System")
    print("="*50)
    
    # Load environment variables from .env file
    load_env_file()
    
    try:
        # Import alert system components
        from utils.alerts import AlertManager, AlertSeverity, AlertCategory, AlertFactory
        print("[OK] Alert system imports successful")
        
        # Load configuration
        config = load_config()
        print("[OK] Configuration loaded")
        
        # Initialize alert manager
        alert_manager = AlertManager(config)
        print("[OK] Alert manager initialized")
        
        # Test alert creation (these will be filtered due to severity)
        print("\nTesting alert creation...")
        
        status = alert_manager.send_alert(
            title="Test Alert",
            message="This is a test alert to verify the system is working.",
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM_HEALTH,
            component="TestScript",
            metadata={"test": True, "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        
        print(f"INFO Alert status: {status.value}")
        
        # Test using alert factory
        print("\nTesting alert factory...")
        
        factory_alert = AlertFactory.create_system_startup_alert(
            component="AlertSystemTest",
            version="1.0.0",
            metadata={"test_mode": True}
        )
        
        factory_status = alert_manager.process_alert(factory_alert)
        print(f"Factory alert status: {factory_status.value}")
        
        # Test MEDIUM level alert (should pass filter)
        print("\nTesting MEDIUM severity alert...")
        
        medium_status = alert_manager.send_alert(
            title="Medium Test Alert",
            message="This MEDIUM level alert should pass the severity filter.",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.SYSTEM_HEALTH,
            component="TestScript",
            metadata={"test": True, "severity_test": "medium"}
        )
        
        print(f"MEDIUM Alert status: {medium_status.value}")
        
        # Show statistics
        print("\nAlert Statistics:")
        stats = alert_manager.get_stats()
        for key, value in stats.items():
            if not isinstance(value, dict):
                print(f"  {key}: {value}")
        
        # Show system status
        print("\nSystem Status:")
        status = alert_manager.get_status()
        for key, value in status.items():
            if not isinstance(value, dict):
                print(f"  {key}: {value}")
        
        print("\n[OK] Basic alert system test completed successfully!")
        
        # Show email configuration status
        email_available = alert_manager.email_service.is_available()
        print(f"\nEmail service available: {email_available}")
        
        if not email_available:
            print("\nTo enable email alerts, set these environment variables:")
            print("   - EMAIL_SENDER: Your Yahoo email address")
            print("   - EMAIL_PASSWORD: Your Yahoo app password")
            print("   - ALERT_RECIPIENT_EMAIL: Email to receive alerts")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alert_factory_methods():
    """Test various alert factory methods."""
    print("\nTesting Alert Factory Methods")
    print("="*50)
    
    try:
        from utils.alerts import AlertFactory, AlertSeverity, AlertCategory
        
        # Test different factory methods
        alerts = [
            AlertFactory.create_order_failure_alert(
                symbol="AAPL",
                order_type="MARKET",
                error_message="Insufficient funds",
                metadata={"amount": 1000}
            ),
            AlertFactory.create_database_connection_alert(
                error_message="Connection timeout"
            ),
            AlertFactory.create_api_error_alert(
                api_name="Yahoo Finance",
                error_message="Rate limit exceeded",
                component="DataCollector"
            ),
            AlertFactory.create_performance_alert(
                metric_name="Response Time",
                current_value=2.5,
                threshold=2.0,
                component="WebAPI"
            ),
            AlertFactory.create_security_alert(
                title="Unauthorized Access",
                message="Multiple failed login attempts",
                component="AuthSystem"
            )
        ]
        
        print(f"[OK] Created {len(alerts)} different alert types")
        
        # Validate each alert
        for i, alert in enumerate(alerts):
            print(f"Alert {i+1}: {alert.severity.value} - {alert.title}")
            assert alert.title is not None
            assert alert.message is not None
            assert isinstance(alert.severity, AlertSeverity)
            assert isinstance(alert.category, AlertCategory)
        
        print("[OK] All alert factory methods working correctly")
        return True
        
    except Exception as e:
        print(f"Factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\nTesting Rate Limiting")
    print("="*50)
    
    try:
        from utils.alerts import AlertManager, AlertSeverity, AlertCategory
        
        config = load_config()
        alert_manager = AlertManager(config)
        
        # Send multiple alerts quickly to test rate limiting
        print("Sending multiple alerts to test rate limiting...")
        
        results = []
        for i in range(5):
            status = alert_manager.send_alert(
                title=f"Rate Limit Test {i+1}",
                message=f"This is test alert #{i+1}",
                severity=AlertSeverity.MEDIUM,  # Use MEDIUM to pass severity filter
                category=AlertCategory.SYSTEM_HEALTH,
                component="RateLimitTest"
            )
            results.append(status.value)
            print(f"  Alert {i+1}: {status.value}")
        
        # Check if any were rate limited (depends on configuration)
        rate_limited_count = sum(1 for r in results if r == "rate_limited")
        print(f"Rate limited alerts: {rate_limited_count}")
        
        print("[OK] Rate limiting test completed")
        return True
        
    except Exception as e:
        print(f"Rate limiting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all alert system tests."""
    print("MLTrading Alert System Test Suite")
    print("="*60)
    
    tests = [
        ("Basic Alert System", test_alert_system_basic),
        ("Alert Factory Methods", test_alert_factory_methods),
        ("Rate Limiting", test_rate_limiting)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"[PASS] {test_name}")
            else:
                print(f"[FAIL] {test_name}")
        except Exception as e:
            print(f"[ERROR] {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())