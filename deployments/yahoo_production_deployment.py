#!/usr/bin/env python3
"""
Production Yahoo Finance Data Collection
Regular optimized data ingestion (3-day window) that runs hourly during market hours
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Patch logging to avoid rotation conflicts in production
try:
    from src.utils.production_logging import patch_for_production
    patch_for_production()
except ImportError:
    pass  # Continue if production logging not available

from src.workflows.data_pipeline.yahoo_market_hours_flow import yahoo_market_hours_collection_flow
from prefect import flow

@flow(name="yahoo-production-data-collection")
def production_data_flow():
    """Production data collection with 3-day optimized window"""
    return yahoo_market_hours_collection_flow(data_period="3d")

if __name__ == "__main__":
    print("Starting Production Yahoo Finance Data Collection...")
    print("Schedule: Every hour during market hours (9 AM - 4 PM EST)")
    print("Data Period: 3 days (optimized for incremental updates)")
    print("Performance: 5-10 minutes for 100+ symbols")
    print("Purpose: Regular data ingestion for trading operations")
    print("=" * 70)
    
    # Serve the flow
    production_data_flow.serve(
        name="yahoo-production-data-collection",
        description="Production Yahoo Finance data collection (3-day optimized) - runs hourly during market hours",
        version="1.0.0",
        tags=["yahoo", "production", "hourly", "optimized"],
        # Schedule to run every hour during market hours
        cron="0 9-16 * * 1-5",  # Every hour from 9-16 EST on Monday-Friday
        limit=1
    )