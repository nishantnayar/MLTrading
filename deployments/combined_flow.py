#!/usr/bin/env python3
"""
Combined Sequential Flow
Runs Yahoo data collection followed by feature engineering in sequence
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prefect import flow, task
from prefect.logging import get_run_logger

# Import the working scripts
from src.data.collectors.yahoo_collector import main as yahoo_main
from scripts.feature_engineering_processor import main as feature_engineering_main


@task(name="yahoo-data-collection-task")
def collect_yahoo_data():
    """Task that runs the working Yahoo data collection"""
    logger = get_run_logger()
    logger.info("Starting Yahoo Finance data collection")
    
    try:
        yahoo_main()
        logger.info("Yahoo data collection completed successfully")
        return {"status": "success", "message": "Data collection completed"}
    except Exception as e:
        logger.error(f"Yahoo data collection failed: {e}")
        return {"status": "error", "message": str(e)}


@task(name="feature-engineering-task")
def process_feature_engineering():
    """Task that runs the working feature engineering processor"""
    logger = get_run_logger()
    logger.info("Starting comprehensive feature engineering processing")
    
    try:
        feature_engineering_main()
        logger.info("Feature engineering processing completed successfully")
        return {"status": "success", "message": "Feature engineering completed"}
    except Exception as e:
        logger.error(f"Feature engineering processing failed: {e}")
        return {"status": "error", "message": str(e)}


@flow(name="combined-sequential-flow")
def combined_sequential_flow():
    """Sequential flow that runs Yahoo collection first, then feature engineering"""
    logger = get_run_logger()
    logger.info("Starting combined sequential flow")
    
    # Step 1: Collect Yahoo data
    yahoo_result = collect_yahoo_data()
    
    if yahoo_result["status"] == "error":
        logger.error("Yahoo data collection failed, skipping feature engineering")
        return {"yahoo": yahoo_result, "features": {"status": "skipped", "message": "Skipped due to data collection failure"}}
    
    # Step 2: Process feature engineering (only if data collection succeeded)
    features_result = process_feature_engineering()
    
    logger.info(f"Combined flow completed - Yahoo: {yahoo_result['status']}, Features: {features_result['status']}")
    return {"yahoo": yahoo_result, "features": features_result}


if __name__ == "__main__":
    # Test the combined flow locally
    print("Testing combined sequential flow...")
    result = combined_sequential_flow()
    print(f"Result: {result}")