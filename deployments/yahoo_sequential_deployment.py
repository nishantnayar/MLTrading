#!/usr/bin/env python3
"""
Prefect deployment for Sequential Pipeline: Yahoo Finance + Feature Engineering
Schedules the complete pipeline to run every hour during market hours on weekdays
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflows.data_pipeline.yahoo_market_hours_flow import yahoo_market_hours_collection_flow

if __name__ == "__main__":
    print("Starting Sequential Pipeline Deployment Server...")
    print("Pipeline: Yahoo Data Collection + Phase 1+2 Feature Engineering")
    print("Schedule: Every hour during market hours (9-16 EST, weekdays)")
    print("Features: 36 total (13 foundation + 23 technical indicators)")
    print("Performance: <3 seconds for feature calculation")
    print("=" * 70)
    
    # Serve the sequential flow with schedule - Prefect 3.x approach
    yahoo_market_hours_collection_flow.serve(
        name="yahoo-data-and-features-hourly",
        description="Sequential pipeline: Yahoo Finance data collection + Phase 1+2 feature engineering (36 features) every hour during market hours",
        version="2.0.0",
        tags=["yahoo", "features", "sequential", "production", "phase1-and-2"],
        # Schedule to run every hour during market hours
        cron="0 9-16 * * 1-5",  # Every hour from 9-16 EST on Monday-Friday
        limit=1
    )