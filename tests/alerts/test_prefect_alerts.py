#!/usr/bin/env python3
"""
Test Prefect integration with the MLTrading Alert System.
"""

import sys
import os
from datetime import datetime, timezone
import yaml
from pathlib import Path

# Add src to path (adjust path since we're in tests folder)
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

def test_prefect_alert_integration():
    """Test Prefect integration without actually running Prefect flows."""
    print("Testing Prefect Alert Integration")
    print("="*50)
    
    # Load environment variables
    load_env_file()
    
    try:
        # Test imports
        from utils.alerts import (
            initialize_alert_manager,
            get_alert_manager,
            alert_on_failure,
            alert_on_long_runtime,
            PrefectAlertManager,
            AlertSeverity,
            AlertCategory
        )
        print("[OK] Prefect alert integration imports successful")
        
        # Load configuration
        config = load_config()
        print("[OK] Configuration loaded")
        
        # Initialize Prefect-aware alert manager
        prefect_alert_manager = initialize_alert_manager(config)
        print("[OK] Prefect alert manager initialized")
        
        # Test getting the global instance
        alert_manager = get_alert_manager()
        assert alert_manager is not None
        print("[OK] Global alert manager instance retrieved")
        
        # Test basic alert sending (will include empty Prefect context)
        print("\nTesting Prefect-aware alert sending...")
        
        status = alert_manager.send_alert(
            title="Prefect Integration Test",
            message="Testing Prefect-aware alert system functionality",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.SYSTEM_HEALTH,
            component="TestSuite",
            metadata={"integration_test": True}
        )
        
        print(f"Alert status: {status.value}")
        
        # Test specialized Prefect methods (without actual Prefect context)
        print("\nTesting Prefect-specific alert methods...")
        
        # Test flow start alert
        status = alert_manager.send_flow_start_alert(
            flow_name="test-integration-flow",
            metadata={"test_mode": True}
        )
        print(f"Flow start alert: {status.value}")
        
        # Test flow success alert
        status = alert_manager.send_flow_success_alert(
            flow_name="test-integration-flow",
            duration=15.5,
            metadata={"records_processed": 1000}
        )
        print(f"Flow success alert: {status.value}")
        
        # Test flow failure alert
        test_error = ValueError("Simulated test error")
        status = alert_manager.send_flow_failure_alert(
            flow_name="test-integration-flow",
            error=test_error,
            metadata={"stage": "data_processing"}
        )
        print(f"Flow failure alert: {status.value}")
        
        # Test task failure alert
        status = alert_manager.send_task_failure_alert(
            task_name="test-task",
            error=test_error,
            metadata={"retry_count": 2}
        )
        print(f"Task failure alert: {status.value}")
        
        print("\n[OK] All Prefect alert integration tests passed!")
        
        # Show statistics
        stats = alert_manager.get_stats()
        print(f"\nAlert Statistics:")
        print(f"  Total alerts: {stats['total_alerts']}")
        print(f"  Sent alerts: {stats['sent_alerts']}")
        print(f"  Failed alerts: {stats['failed_alerts']}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alert_decorators():
    """Test alert decorators without Prefect context."""
    print("\nTesting Alert Decorators")
    print("="*50)
    
    try:
        from utils.alerts import alert_on_failure, alert_on_long_runtime, AlertSeverity, AlertCategory
        
        # Test function with failure decorator
        @alert_on_failure(severity=AlertSeverity.MEDIUM, send_success_alert=True)
        def test_function_success():
            """Test function that succeeds."""
            return "success"
        
        @alert_on_failure(severity=AlertSeverity.HIGH)
        def test_function_failure():
            """Test function that fails."""
            raise ValueError("Test error for decorator")
        
        @alert_on_long_runtime(threshold_seconds=1.0, severity=AlertSeverity.LOW)
        def test_function_long_runtime():
            """Test function with long runtime."""
            import time
            time.sleep(1.5)  # Exceed threshold
            return "completed"
        
        # Test successful function
        print("Testing successful function with decorator...")
        result = test_function_success()
        print(f"Function result: {result}")
        
        # Test long runtime function
        print("Testing function with long runtime...")
        result = test_function_long_runtime()
        print(f"Long runtime function result: {result}")
        
        # Test failing function (should raise exception and send alert)
        print("Testing failing function with decorator...")
        try:
            test_function_failure()
        except ValueError as e:
            print(f"Expected error caught: {e}")
        
        print("[OK] Alert decorators test completed")
        return True
        
    except Exception as e:
        print(f"Decorator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mock_prefect_context():
    """Test with mocked Prefect context."""
    print("\nTesting with Mocked Prefect Context")
    print("="*50)
    
    try:
        # This tests the scenario where Prefect is available but no context exists
        from utils.alerts import get_alert_manager, AlertSeverity, AlertCategory
        
        alert_manager = get_alert_manager()
        if not alert_manager:
            print("[SKIP] No alert manager available")
            return True
        
        # Test context-aware alert (should fall back gracefully)
        status = alert_manager.send_alert(
            title="Mock Prefect Context Test",
            message="Testing alert system with no active Prefect context",
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM_HEALTH,
            metadata={"mock_test": True}
        )
        
        print(f"Mock context alert status: {status.value}")
        print("[OK] Mock Prefect context test passed")
        
        return True
        
    except Exception as e:
        print(f"Mock context test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Prefect alert integration tests."""
    print("MLTrading Prefect Alert Integration Test Suite")
    print("="*60)
    
    tests = [
        ("Prefect Alert Integration", test_prefect_alert_integration),
        ("Alert Decorators", test_alert_decorators),
        ("Mock Prefect Context", test_mock_prefect_context)
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
        print("\n[SUCCESS] All Prefect alert integration tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())