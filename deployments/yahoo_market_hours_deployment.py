#!/usr/bin/env python3
"""
Prefect deployment for Yahoo Finance market hours data collection
Schedules the workflow to run every hour during market hours on weekdays
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflows.data_pipeline.yahoo_market_hours_flow import yahoo_market_hours_collection_flow

if __name__ == "__main__":
    # Serve the flow with schedule - Prefect 3.x approach
    yahoo_market_hours_collection_flow.serve(
        name="yahoo-market-hours-hourly",
        description="Collects Yahoo Finance data every hour during market hours (9:30 AM - 4:00 PM EST) on weekdays",
        version="1.0.0",
        tags=["yahoo", "market-data", "hourly", "production"],
        # Schedule to run every hour during market hours
        cron="0 9-16 * * 1-5",  # Every hour from 9-16 EST on Monday-Friday
        limit=1
    )