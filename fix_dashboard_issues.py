#!/usr/bin/env python3
"""
Batch fix script for remaining dashboard flake8 issues.
Handles simple cases like unused imports, blank lines, and basic formatting.
"""

import os
import re
from pathlib import Path


def remove_unused_imports(file_path, unused_imports):
    """Remove specific unused imports from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for import_line in unused_imports:
            # Handle different import patterns
            patterns = [
                f"^{re.escape(import_line)}$",
                f"^{re.escape(import_line)},?$",
                f", {re.escape(import_line.split('.')[-1])}",
            ]
            
            for pattern in patterns:
                content = re.sub(pattern, "", content, flags=re.MULTILINE)
        
        # Clean up empty lines and trailing commas in imports
        content = re.sub(r'\n\s*,\s*\n', '\n', content)
        content = re.sub(r',(\s*\n\s*\))', r'\1', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def fix_blank_lines(file_path):
    """Fix blank line issues (E302, E303)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a function/class definition
            if re.match(r'^def |^class |^async def ', line.strip()):
                # Ensure 2 blank lines before function/class (except at start of file)
                if fixed_lines and not all(l.strip() == '' for l in fixed_lines[-2:]):
                    # Add appropriate blank lines
                    while len(fixed_lines) > 0 and fixed_lines[-1].strip() == '':
                        fixed_lines.pop()
                    fixed_lines.extend(['\n', '\n'])
            
            # Remove excessive blank lines (more than 2)
            if line.strip() == '':
                blank_count = 1
                while i + blank_count < len(lines) and lines[i + blank_count].strip() == '':
                    blank_count += 1
                
                # Add maximum 2 blank lines
                if blank_count > 2:
                    fixed_lines.extend(['\n', '\n'])
                    i += blank_count
                    continue
            
            fixed_lines.append(line)
            i += 1
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        print(f"Fixed blank lines in {file_path}")
        return True
        
    except Exception as e:
        print(f"Error fixing blank lines in {file_path}: {e}")
        return False


def main():
    """Fix dashboard issues."""
    
    # Files and their unused imports to remove
    unused_imports_map = {
        "src/dashboard/components/shared_components.py": [
            "from ..config import CARD_STYLE_ELEVATED, CHART_COLORS"
        ],
        "src/dashboard/layouts/analytics_components.py": [
            "import plotly.express as px"
        ],
        "src/dashboard/layouts/chart_components.py": [
            "import plotly.express as px",
            "from dash import dcc"
        ],
        "src/dashboard/layouts/dashboard_layout.py": [
            "from ..config import DEFAULT_CHART_HEIGHT, DEFAULT_TIME_RANGE, DEFAULT_SYMBOL, TIME_RANGE_OPTIONS",
            "from ..components.shared_components import create_chart_card, create_control_group"
        ],
        "src/dashboard/services/unified_data_service.py": [
            "from datetime import timedelta"
        ],
        "src/dashboard/utils/date_formatters.py": [
            "from datetime import timedelta",
            "from typing import Optional"
        ],
        "src/dashboard/utils/log_viewer.py": [
            "import dash",
            "from dash import Input, Output, State",
            "import pandas as pd",
            "import json",
            "import logging"
        ],
        "src/dashboard/utils/validators.py": [
            "from typing import List, Optional, Union"
        ]
    }
    
    print("Fixing dashboard flake8 issues...")
    
    # Remove unused imports
    for file_path, imports in unused_imports_map.items():
        path = Path(file_path)
        if path.exists():
            remove_unused_imports(path, imports)
        else:
            print(f"File not found: {file_path}")
    
    # Fix blank lines in key files
    blank_line_files = [
        "src/dashboard/layouts/chart_components.py",
        "src/dashboard/utils/log_viewer.py"
    ]
    
    for file_path in blank_line_files:
        path = Path(file_path)
        if path.exists():
            fix_blank_lines(path)
    
    print("Dashboard flake8 fixes completed!")


if __name__ == "__main__":
    main()