#!/usr/bin/env python3
"""
Fix critical dashboard flake8 issues that are causing syntax/undefined name errors.
"""

import os
import re
from pathlib import Path


def fix_critical_issues():
    """Fix critical syntax and undefined variable errors."""
    
    # Fix detailed_analysis_callbacks.py - restore commented variables
    detailed_analysis_file = "src/dashboard/callbacks/detailed_analysis_callbacks.py"
    try:
        with open(detailed_analysis_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Restore vol_data variable
        content = content.replace('# vol_data = ', 'vol_data = ')
        content = content.replace('# volume_data = ', 'volume_data = ')
        content = content.replace('# original_count = ', 'original_count = ')
        
        with open(detailed_analysis_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed critical issues in {detailed_analysis_file}")
    except Exception as e:
        print(f"Error fixing {detailed_analysis_file}: {e}")
    
    # Fix batch_data_service.py
    batch_service_file = "src/dashboard/services/batch_data_service.py"
    try:
        with open(batch_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('# original_count = ', 'original_count = ')
        
        with open(batch_service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed critical issues in {batch_service_file}")
    except Exception as e:
        print(f"Error fixing {batch_service_file}: {e}")
    
    # Fix market_data_service.py
    market_service_file = "src/dashboard/services/market_data_service.py"
    try:
        with open(market_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('# original_count = ', 'original_count = ')
        
        with open(market_service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed critical issues in {market_service_file}")
    except Exception as e:
        print(f"Error fixing {market_service_file}: {e}")
    
    # Fix syntax errors in feature_data_service.py and technical_indicators.py
    files_with_syntax_errors = [
        "src/dashboard/services/feature_data_service.py",
        "src/dashboard/services/technical_indicators.py"
    ]
    
    for file_path in files_with_syntax_errors:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix unmatched braces in f-strings
            content = re.sub(r'f"([^"]*)\}([^{]*)"', r'f"\1}}\2"', content)
            content = re.sub(r"f'([^']*)\}([^{]*)'", r"f'\1}}\2'", content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed syntax errors in {file_path}")
        except Exception as e:
            print(f"Error fixing syntax in {file_path}: {e}")
    
    # Fix optimized_feature_data_service.py indentation
    optimized_service_file = "src/dashboard/services/optimized_feature_data_service.py"
    try:
        with open(optimized_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('# cache_keys = ', 'cache_keys = ')
        
        with open(optimized_service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed critical issues in {optimized_service_file}")
    except Exception as e:
        print(f"Error fixing {optimized_service_file}: {e}")
    
    # Fix constants.py corruption
    constants_file = "src/dashboard/config/constants.py"
    try:
        with open(constants_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix corrupted lines
        content = content.replace("'success_light': '#95c95',", "'success_light': '#95c95f',")
        content = content.replace("'secondary': '#e9ece',", "'secondary': '#e9ecef',")
        content = content.replace('"Inter", -apple-system, BlinkMacSystemFont, "Segue UI", Roboto, sans-seri', 
                                '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif')
        
        with open(constants_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed constants file corruption in {constants_file}")
    except Exception as e:
        print(f"Error fixing {constants_file}: {e}")


if __name__ == "__main__":
    fix_critical_issues()
    print("Critical fixes completed!")