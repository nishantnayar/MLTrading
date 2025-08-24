#!/usr/bin/env python3
"""
Prefect deployment for INITIAL BACKFILL: Yahoo Finance + Feature Engineering
Processes ALL historical data for complete feature backfill - use for first run only
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflows.data_pipeline.feature_engineering_flow import feature_engineering_flow

if __name__ == "__main__":
    print("Starting INITIAL BACKFILL Deployment Server...")
    print("CAUTION: This processes ALL historical market data")
    print("Pipeline: Feature Engineering with COMPLETE historical backfill") 
    print("Trigger: Manual execution for initial setup")
    print("Features: 36 total (13 foundation + 23 technical indicators)")
    print("Data Scope: ALL historical records in market_data table")
    print("Expected Runtime: 10-30+ minutes depending on data volume")
    print("=" * 70)
    
    # Serve the feature engineering flow with initial_run=True
    def initial_backfill_flow():
        """Wrapper flow that calls feature engineering with initial_run=True"""
        return feature_engineering_flow(initial_run=True)
    
    initial_backfill_flow.serve(
        name="feature-engineering-initial-backfill",
        description="INITIAL BACKFILL: Feature engineering with ALL historical data - use once for setup",
        version="2.0.0",
        tags=["features", "initial", "backfill", "all-data", "setup"],
        # No cron schedule = manual trigger only
        limit=1
    )