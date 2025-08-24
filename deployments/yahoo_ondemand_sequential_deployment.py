#!/usr/bin/env python3
"""
Prefect on-demand deployment for Sequential Pipeline: Yahoo Finance + Feature Engineering
Manual trigger for testing the complete pipeline
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflows.data_pipeline.yahoo_market_hours_flow import yahoo_market_hours_collection_flow

if __name__ == "__main__":
    print("Starting On-Demand Sequential Pipeline Deployment Server...")
    print("Pipeline: Yahoo Data Collection + Phase 1+2 Feature Engineering") 
    print("Trigger: Manual execution for testing")
    print("Features: 36 total (13 foundation + 23 technical indicators)")
    print("Data Scope: Recent data only (incremental mode)")
    print("Performance: <3 seconds for feature calculation")
    print()
    print("For INITIAL BACKFILL with ALL historical data, use:")
    print("  python deployments/yahoo_initial_backfill_deployment.py")
    print("=" * 70)
    
    # Serve the sequential flow without schedule - manual trigger only
    # Uses incremental mode (recent data only) for performance
    yahoo_market_hours_collection_flow.serve(
        name="yahoo-data-and-features-ondemand",
        description="On-demand sequential pipeline (incremental): Yahoo Finance data + Phase 1+2 feature engineering (36 features)",
        version="2.0.0",
        tags=["yahoo", "features", "ondemand", "testing", "phase1-and-2", "incremental"],
        # No cron schedule = manual trigger only
        limit=1
    )