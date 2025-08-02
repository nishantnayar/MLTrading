#!/usr/bin/env python3
"""
Runner script for Yahoo Finance data collection.
This script imports and runs the yahoo_collector module.
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data.collectors.yahoo_collector import main

if __name__ == "__main__":
    main() 