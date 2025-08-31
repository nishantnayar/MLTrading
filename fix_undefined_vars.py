#!/usr/bin/env python3
"""
Fix remaining critical F821 undefined variable errors.
"""

import os
import re
from pathlib import Path


def fix_undefined_variables():
    """Fix specific undefined variables that were incorrectly commented out."""
    
    # Specific fixes for undefined variables
    fixes = [
        # Interactive chart layout
        ("src/dashboard/layouts/interactive_chart.py", [
            ("# chart_config = indicator_service.get_indicator_config()  # Currently unused",
             "chart_config = indicator_service.get_indicator_config()")
        ]),
        
        # Data collector fixes
        ("src/data/collectors/yahoo_collector.py", [
            ("# start_time = time.time()  # Currently unused",
             "start_time = time.time()")
        ]),
        
        # Trading strategy fixes
        ("src/trading/strategies/custom_pairs_trading.py", [
            ("# pair_name = pair_trade.get('symbol')  # Currently unused",
             "pair_name = pair_trade.get('symbol')")
        ]),
        
        ("src/trading/strategies/pairs_trading.py", [
            ("# pair_name = pair_trade.get('pair_name')  # Currently unused",
             "pair_name = pair_trade.get('pair_name')")
        ]),
        
        # Utils fixes
        ("src/utils/alerts/prefect_integration.py", [
            ("# start_time = datetime.now(timezone.utc)  # Currently unused",
             "start_time = datetime.now(timezone.utc)")
        ]),
        
        ("src/utils/database_log_manager.py", [
            ("# start_time = datetime.now() - timedelta(hours=24)  # Currently unused",
             "start_time = datetime.now() - timedelta(hours=24)")
        ]),
        
        ("src/utils/database_logging.py", [
            ("# start_time = time.time()  # Currently unused",
             "start_time = time.time()")
        ]),
        
        ("src/utils/database_performance_monitor.py", [
            ("# start_time = time.time()  # Currently unused",
             "start_time = time.time()")
        ]),
        
        ("src/utils/logging_config.py", [
            ("# start_time = time.time()  # Currently unused",
             "start_time = time.time()")
        ]),
        
        ("src/utils/resilient_database_logging.py", [
            ("# start_time = time.time()  # Currently unused",
             "start_time = time.time()")
        ]),
        
        ("src/utils/sequential_task_runner.py", [
            ("# start_time = time.time()  # Currently unused",
             "start_time = time.time()")
        ]),
        
        # Prefect service indentation fix
        ("src/services/prefect_service.py", [
            ("                    else:\n                     \n                        states_dict[state_name] = state_count",
             "                    else:\n                        states_dict[state_name] = state_count")
        ]),
        
        # Optimized feature data service indentation fix  
        ("src/dashboard/services/optimized_feature_data_service.py", [
            ("            # cache_keys = list(self.cache.keys())  # Currently unused",
             "            cache_keys = list(self.cache.keys())")
        ])
    ]
    
    for file_path, replacements in fixes:
        if os.path.exists(file_path):
            print(f"Processing {file_path}...")
            fix_variables_in_file(file_path, replacements)


def fix_variables_in_file(file_path, replacements):
    """Fix undefined variables in a specific file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old_pattern, new_pattern in replacements:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                print(f"  - Fixed: {old_pattern[:50]}...")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  - Updated {file_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    fix_undefined_variables()
    print("Undefined variable fixes completed!")