#!/usr/bin/env python3
"""
Test script to send an actual email alert.
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

def test_email_alert():
    """Test sending an actual email alert."""
    print("Testing Email Alert System")
    print("="*50)
    
    # Load environment variables from .env file
    load_env_file()
    
    try:
        # Import alert system components
        from utils.alerts import AlertManager, AlertSeverity, AlertCategory
        print("[OK] Alert system imports successful")
        
        # Load configuration
        config = load_config()
        print("[OK] Configuration loaded")
        
        # Initialize alert manager
        alert_manager = AlertManager(config)
        print("[OK] Alert manager initialized")
        
        # Check if email service is available
        if not alert_manager.email_service.is_available():
            print("[ERROR] Email service not available!")
            print("Check your environment variables:")
            print("  - EMAIL_SENDER")
            print("  - EMAIL_PASSWORD")  
            print("  - ALERT_RECIPIENT_EMAIL")
            return False
        
        print("[OK] Email service is available")
        
        # Send a MEDIUM level alert that should pass the filter
        print("\nSending MEDIUM severity test alert...")
        status = alert_manager.send_alert(
            title="Test Email Alert",
            message="This is a test email alert to verify the Yahoo Mail integration is working correctly. If you receive this email, the alert system is functioning properly!",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.SYSTEM_HEALTH,
            component="EmailTest",
            metadata={
                "test": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system": "MLTrading Alert System"
            }
        )
        
        print(f"Alert status: {status.value}")
        
        if status.value == "sent":
            print("\n[SUCCESS] Email alert sent successfully!")
            print("Check your email inbox for the test alert.")
        else:
            print(f"\n[WARNING] Alert not sent. Status: {status.value}")
            
        # Show final statistics
        stats = alert_manager.get_stats()
        print(f"\nFinal Statistics:")
        print(f"  Total alerts: {stats['total_alerts']}")
        print(f"  Sent alerts: {stats['sent_alerts']}")
        print(f"  Failed alerts: {stats['failed_alerts']}")
        
        return status.value == "sent"
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_email_alert()
    print("\n" + "="*50)
    if success:
        print("Email alert test PASSED!")
    else:
        print("Email alert test FAILED!")
    print("="*50)
    sys.exit(0 if success else 1)