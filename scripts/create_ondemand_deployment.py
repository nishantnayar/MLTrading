#!/usr/bin/env python3
"""
Script to create the on-demand Yahoo Finance deployment using Prefect 3.x
This deployment can be triggered manually at any time
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our flow
from src.workflows.data_pipeline.yahoo_ondemand_flow import yahoo_ondemand_collection_flow

def create_ondemand_deployment():
    """Create the on-demand Yahoo Finance deployment"""
    
    print("Creating on-demand Yahoo Finance data collection deployment...")
    
    # Use Prefect 3.x deployment method - no schedule for on-demand
    deployment = yahoo_ondemand_collection_flow.deploy(
        name="yahoo-ondemand-collection",
        description="On-demand Yahoo Finance data collection - can be triggered manually anytime",
        version="1.0.0",
        tags=["yahoo", "market-data", "ondemand", "manual"],
        # No schedule - this is purely on-demand
        work_pool_name="yahoo-data-pool"
    )
    
    print(f"Created deployment: yahoo-ondemand-collection")
    print(f"No automatic schedule - this is for manual/on-demand execution")
    print(f"Deployment result: {deployment}")
    
    return deployment

if __name__ == "__main__":
    result = create_ondemand_deployment()
    print("\nOn-demand deployment created successfully!")
    print("\nTo trigger this deployment manually, use:")
    print("prefect deployment run 'yahoo-ondemand-data-collection/yahoo-ondemand-collection'")
    print("\nOr with custom parameters:")
    print("prefect deployment run 'yahoo-ondemand-data-collection/yahoo-ondemand-collection' --param symbols_limit=10 --param period=5d")
    print("\nTo start a worker to execute runs, use:")
    print("prefect worker start --pool yahoo-data-pool")