#!/usr/bin/env python3
"""
Prefect deployment for on-demand Yahoo Finance data collection
This deployment can be triggered manually at any time
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflows.data_pipeline.yahoo_ondemand_flow import yahoo_ondemand_collection_flow

if __name__ == "__main__":
    # Serve the flow without schedule - purely on-demand
    yahoo_ondemand_collection_flow.serve(
        name="yahoo-ondemand-collection",
        description="On-demand Yahoo Finance data collection - can be triggered manually anytime",
        version="1.0.0",
        tags=["yahoo", "market-data", "ondemand", "manual"],
        # No cron schedule - this is purely on-demand
        limit=1
    )