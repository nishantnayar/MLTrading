#!/usr/bin/env python3
"""
Feature Engineering Flow
Wraps the working scripts/feature_engineering_processor.py in a Prefect flow
"""

import sys
import os
from pathlib import Path

# Add project root to path (parent of deployments folder)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prefect import flow, task
from prefect.logging import get_run_logger

# Import the working feature engineering processor
from scripts.feature_engineering_processor import main as feature_engineering_main


@task(name="feature-engineering-task")
def process_feature_engineering():
    """Task that runs the working feature engineering processor"""
    logger = get_run_logger()
    logger.info("Starting comprehensive feature engineering processing")
    
    try:
        # Run the working processor
        feature_engineering_main()
        logger.info("Feature engineering processing completed successfully")
        return {"status": "success", "message": "Feature engineering completed"}
    
    except Exception as e:
        logger.error(f"Feature engineering processing failed: {e}")
        return {"status": "error", "message": str(e)}


@flow(name="feature-engineering")
def feature_engineering_flow():
    """Simple flow that processes feature engineering using the working processor"""
    logger = get_run_logger()
    logger.info("Starting feature engineering flow")
    
    # Run the feature engineering task
    result = process_feature_engineering()
    
    logger.info(f"Flow completed with result: {result}")
    return result


if __name__ == "__main__":
    # Test the flow locally
    print("Testing feature engineering flow...")
    result = feature_engineering_flow()
    print(f"Result: {result}")