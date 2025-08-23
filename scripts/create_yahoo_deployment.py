#!/usr/bin/env python3
"""
Script to create and schedule the Yahoo Finance deployment using Prefect 3.x
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our flow
from src.workflows.data_pipeline.yahoo_market_hours_flow import yahoo_market_hours_collection_flow

def create_deployment():
    """Create the Yahoo Finance deployment with hourly schedule"""
    
    # Use Prefect 3.x deployment method
    deployment = yahoo_market_hours_collection_flow.deploy(
        name="yahoo-market-hours-hourly",
        description="Collects Yahoo Finance data every hour during market hours (9:00 AM - 4:00 PM EST) on weekdays",
        version="1.0.0",
        tags=["yahoo", "market-data", "hourly", "production"],
        # Schedule to run every hour during market hours  
        cron="0 9-16 * * 1-5",  # Every hour from 9-16 EST on Monday-Friday
        work_pool_name="yahoo-data-pool"
    )
    
    print(f"Created deployment: yahoo-market-hours-hourly")
    print(f"Schedule: Every hour during market hours (9 AM - 4 PM EST) on weekdays")
    print(f"Deployment result: {deployment}")
    
    return deployment

if __name__ == "__main__":
    result = create_deployment()
    print("\nDeployment created successfully!")
    print("To start a worker to run this deployment, use:")
    print("prefect worker start --pool yahoo-data-pool")