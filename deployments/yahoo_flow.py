#!/usr/bin/env python3
"""
Simple Yahoo Finance Data Collection Flow
Wraps the working scripts/run_yahoo_collector.py in a Prefect flow
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prefect import flow, task
from prefect.logging import get_run_logger

# Import the working collector
from src.data.collectors.yahoo_collector import main as yahoo_main


@task(name="yahoo-data-collection")
def collect_yahoo_data():
    """Task that runs the working Yahoo data collection"""
    logger = get_run_logger()
    logger.info("Starting Yahoo Finance data collection")
    
    try:
        # Run the working collector
        yahoo_main()
        logger.info("Yahoo data collection completed successfully")
        return {"status": "success", "message": "Data collection completed"}
    
    except Exception as e:
        logger.error(f"Yahoo data collection failed: {e}")
        return {"status": "error", "message": str(e)}


@flow(name="yahoo-finance-data-collection")
def yahoo_data_collection_flow():
    """Simple flow that collects Yahoo Finance data using the working collector"""
    logger = get_run_logger()
    logger.info("Starting Yahoo Finance data collection flow")
    
    # Run the data collection task
    result = collect_yahoo_data()
    
    logger.info(f"Flow completed with result: {result}")
    return result


if __name__ == "__main__":
    # Test the flow locally
    print("Testing Yahoo data collection flow...")
    result = yahoo_data_collection_flow()
    print(f"Result: {result}")