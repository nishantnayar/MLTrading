#!/usr/bin/env python3
"""
Example of integrating MLTrading Alert System with Prefect workflows.

This example demonstrates:
1. Initializing alert manager in Prefect flows
2. Using decorators for automatic error alerts
3. Manual alert sending for specific events
4. Context-aware alerts that include Prefect metadata
"""

import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from prefect import flow, task, get_run_logger
    from prefect.task_runners import ConcurrentTaskRunner
    PREFECT_AVAILABLE = True
except ImportError:
    print("Prefect not available. Install with: pip install prefect")
    PREFECT_AVAILABLE = False
    sys.exit(1)

from utils.alerts import (
    initialize_alert_manager,
    get_alert_manager,
    alert_on_failure,
    alert_on_long_runtime,
    AlertSeverity,
    AlertCategory
)


def load_config():
    """Load configuration - simplified for demo."""
    import yaml
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path) as f:
        return yaml.safe_load(f)


# Initialize global alert manager
config = load_config()
alert_manager = initialize_alert_manager(config)


@task
@alert_on_failure(severity=AlertSeverity.MEDIUM, send_success_alert=True)
def collect_market_data() -> dict:
    """Collect market data with automatic failure alerts."""
    logger = get_run_logger()
    alert_manager = get_alert_manager()
    
    logger.info("Starting market data collection...")
    
    # Simulate data collection
    import time
    time.sleep(2)  # Simulate work
    
    # Example of manual success alert with custom metadata
    result = {"symbols": ["AAPL", "MSFT", "GOOGL"], "records": 1250}
    
    alert_manager.send_alert(
        title="Market Data Collection Complete",
        message=f"Successfully collected data for {len(result['symbols'])} symbols ({result['records']} records)",
        severity=AlertSeverity.INFO,
        category=AlertCategory.DATA_PIPELINE,
        metadata=result
    )
    
    return result


@task
@alert_on_failure(severity=AlertSeverity.HIGH)
@alert_on_long_runtime(threshold_seconds=10, severity=AlertSeverity.MEDIUM)
def process_features(data: dict) -> dict:
    """Process features with runtime monitoring."""
    logger = get_run_logger()
    
    logger.info(f"Processing features for {len(data['symbols'])} symbols...")
    
    # Simulate feature processing
    import time
    time.sleep(5)  # Simulate work
    
    return {"features_generated": 95, "processing_time": 5.2}


@task
@alert_on_failure(severity=AlertSeverity.HIGH)
def validate_data_quality(features: dict) -> bool:
    """Validate data quality with custom alerts."""
    logger = get_run_logger()
    alert_manager = get_alert_manager()
    
    # Simulate validation
    feature_count = features.get("features_generated", 0)
    
    if feature_count < 90:
        # Send data quality alert
        alert_manager.send_alert(
            title="Data Quality Issue",
            message=f"Only {feature_count} features generated (expected: 90+)",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.DATA_PIPELINE,
            metadata={"feature_count": feature_count, "threshold": 90}
        )
        return False
    
    # Send success alert
    alert_manager.send_alert(
        title="Data Quality Validation Passed",
        message=f"All {feature_count} features passed quality checks",
        severity=AlertSeverity.INFO,
        category=AlertCategory.DATA_PIPELINE,
        metadata=features
    )
    
    return True


@task
def simulate_trading_error():
    """Simulate a trading error for demonstration."""
    logger = get_run_logger()
    alert_manager = get_alert_manager()
    
    # Simulate trading error
    error_msg = "Order execution failed: Insufficient buying power"
    
    alert_manager.send_trading_error_alert(
        error_message=error_msg,
        component="TradingSimulator",
        metadata={
            "symbol": "AAPL",
            "order_type": "MARKET",
            "quantity": 100,
            "account_balance": 5000,
            "required_amount": 15000
        }
    )
    
    logger.warning(f"Trading error simulated: {error_msg}")
    return False


@flow(
    name="enhanced-data-pipeline-with-alerts",
    description="Example data pipeline with comprehensive alert integration",
    task_runner=ConcurrentTaskRunner()
)
def enhanced_data_pipeline():
    """Enhanced data pipeline with integrated alerts."""
    logger = get_run_logger()
    alert_manager = get_alert_manager()
    
    # Send flow start alert
    alert_manager.send_flow_start_alert(
        flow_name="enhanced-data-pipeline-with-alerts",
        metadata={"started_by": "scheduler", "environment": "development"}
    )
    
    start_time = datetime.now(timezone.utc)
    
    try:
        # Data collection with automatic failure alerts
        logger.info("Starting data collection...")
        market_data = collect_market_data()
        
        # Feature processing with runtime monitoring
        logger.info("Processing features...")
        features = process_features(market_data)
        
        # Data quality validation with custom alerts
        logger.info("Validating data quality...")
        quality_passed = validate_data_quality(features)
        
        if not quality_passed:
            raise ValueError("Data quality validation failed")
        
        # Simulate trading operation
        logger.info("Simulating trading operation...")
        trading_success = simulate_trading_error()  # This will generate an alert
        
        # Calculate total duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Send comprehensive flow success alert
        alert_manager.send_flow_success_alert(
            flow_name="enhanced-data-pipeline-with-alerts",
            duration=duration,
            metadata={
                "symbols_processed": len(market_data["symbols"]),
                "features_generated": features["features_generated"],
                "data_quality_passed": quality_passed,
                "trading_success": trading_success,
                "total_records": market_data["records"]
            }
        )
        
        logger.info("[SUCCESS] Pipeline completed successfully!")
        return {
            "status": "success",
            "duration": duration,
            "features": features,
            "quality_passed": quality_passed
        }
        
    except Exception as e:
        # Send detailed failure alert
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        alert_manager.send_flow_failure_alert(
            flow_name="enhanced-data-pipeline-with-alerts",
            error=e,
            metadata={
                "duration": duration,
                "failure_stage": "unknown",
                "environment": "development"
            }
        )
        
        logger.error(f"[ERROR] Pipeline failed: {str(e)}")
        raise


@flow(name="alert-system-demo")
def alert_system_demo():
    """Demonstrate various alert system features."""
    logger = get_run_logger()
    alert_manager = get_alert_manager()
    
    logger.info("Starting Alert System Demo...")
    
    # Test different alert types
    alerts_to_send = [
        {
            "method": "send_system_health_alert",
            "kwargs": {
                "title": "High Memory Usage",
                "message": "System memory usage is at 87% (threshold: 85%)",
                "severity": AlertSeverity.MEDIUM,
                "metadata": {"memory_usage": 87, "threshold": 85}
            }
        },
        {
            "method": "send_security_alert",
            "kwargs": {
                "title": "Unusual Login Activity",
                "message": "Login from new IP address: 192.168.1.100",
                "metadata": {"ip_address": "192.168.1.100", "location": "Unknown"}
            }
        },
        {
            "method": "send_data_pipeline_alert",
            "kwargs": {
                "title": "Data Freshness Warning",
                "message": "Yahoo Finance data is 2 hours old (threshold: 1 hour)",
                "severity": AlertSeverity.MEDIUM,
                "metadata": {"data_age_hours": 2, "threshold_hours": 1}
            }
        }
    ]
    
    for alert_config in alerts_to_send:
        method_name = alert_config["method"]
        method = getattr(alert_manager, method_name)
        status = method(**alert_config["kwargs"])
        logger.info(f"Sent {method_name}: {status.value}")
    
    # Show alert statistics
    stats = alert_manager.get_stats()
    logger.info(f"Alert Statistics: {stats['total_alerts']} total, {stats['sent_alerts']} sent")
    
    return {"alerts_sent": len(alerts_to_send), "stats": stats}


if __name__ == "__main__":
    print("MLTrading Alert System - Prefect Integration Demo")
    print("="*60)
    
    if not alert_manager:
        print("[ERROR] Alert manager not initialized properly")
        sys.exit(1)
    
    # Check if email service is available
    email_available = alert_manager.email_service.is_available()
    print(f"Email service available: {email_available}")
    
    if not email_available:
        print("\nTo enable email alerts, set environment variables:")
        print("   EMAIL_SENDER=your_email@yahoo.com")
        print("   EMAIL_PASSWORD=your_yahoo_app_password")
        print("   ALERT_RECIPIENT_EMAIL=your_email@yahoo.com")
        print()
    
    print("Running Prefect flows with alert integration...\n")
    
    # Run the demo flows
    try:
        # Run alert system demo
        print("1. Running Alert System Demo...")
        demo_result = alert_system_demo()
        print(f"   Demo completed: {demo_result['alerts_sent']} alerts sent\n")
        
        # Run enhanced data pipeline
        print("2. Running Enhanced Data Pipeline...")
        pipeline_result = enhanced_data_pipeline()
        print(f"   Pipeline completed in {pipeline_result['duration']:.1f}s\n")
        
        print("[SUCCESS] All demos completed successfully!")
        
        # Show final statistics
        final_stats = alert_manager.get_stats()
        print(f"\nFinal Alert Statistics:")
        print(f"   Total alerts: {final_stats['total_alerts']}")
        print(f"   Sent successfully: {final_stats['sent_alerts']}")
        print(f"   Failed: {final_stats['failed_alerts']}")
        print(f"   Rate limited: {final_stats['rate_limited_alerts']}")
        
    except Exception as e:
        print(f"[ERROR] Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)