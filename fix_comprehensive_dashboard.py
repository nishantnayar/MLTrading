#!/usr/bin/env python3
"""
Comprehensive fix script for all remaining dashboard flake8 issues.
Handles unused imports, long lines, indentation, and other formatting issues.
"""

import os
import re
from pathlib import Path


def remove_unused_imports_comprehensive(file_path):
    """Remove all unused imports based on flake8 F401 patterns."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip lines that are not import statements
            if not (line.strip().startswith('import ') or line.strip().startswith('from ')):
                new_lines.append(line)
                i += 1
                continue
            
            # Handle multi-line imports
            if '(' in line and ')' not in line:
                # Multi-line import
                import_block = [line]
                i += 1
                while i < len(lines) and ')' not in lines[i]:
                    import_block.append(lines[i])
                    i += 1
                if i < len(lines):
                    import_block.append(lines[i])  # Line with closing )
                
                # Process multi-line import block
                full_import = '\n'.join(import_block)
                processed_import = process_import_block(full_import, file_path)
                if processed_import.strip():
                    new_lines.extend(processed_import.split('\n'))
                i += 1
            else:
                # Single line import
                processed_line = process_single_import(line, file_path)
                if processed_line is not None:
                    new_lines.append(processed_line)
                i += 1
        
        new_content = '\n'.join(new_lines)
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed imports in {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error processing imports in {file_path}: {e}")
        return False


def process_single_import(line, file_path):
    """Process a single import line."""
    # Define unused imports per file based on flake8 output
    unused_patterns = get_unused_patterns(file_path)
    
    for pattern in unused_patterns:
        if pattern in line:
            return None  # Remove this line
    
    return line


def process_import_block(import_block, file_path):
    """Process multi-line import block."""
    unused_patterns = get_unused_patterns(file_path)
    
    lines = import_block.split('\n')
    filtered_lines = []
    
    for line in lines:
        should_remove = False
        for pattern in unused_patterns:
            if pattern in line and not line.strip().startswith('from ') and not line.strip().startswith('import '):
                # This is an import item that should be removed
                should_remove = True
                break
        
        if not should_remove:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


def get_unused_patterns(file_path):
    """Get unused import patterns for specific files."""
    filename = os.path.basename(file_path)
    
    # Comprehensive mapping based on flake8 output
    patterns = {
        'chart_callbacks.py': [
            'plotly.graph_objs as go',
            'dash.Input', 'dash.Output', 'dash.State', 'dash.callback_context',
            'CHART_COLORS', 'TIME_RANGE_DAYS',
            'create_empty_chart', 'create_error_chart',
            'InputValidator'
        ],
        'comparison_callbacks.py': [
            'plotly.subplots.make_subplots',
            'pandas as pd',
            'datetime.datetime', 'datetime.timedelta'
        ],
        'detailed_analysis_callbacks.py': [
            'plotly.express as px',
            'pandas as pd'
        ],
        'interactive_chart_callbacks.py': [
            'plotly.graph_objs as go',
            'pandas as pd',
            'typing.List', 'typing.Dict', 'typing.Any', 'typing.Optional',
            'datetime.datetime', 'datetime.timedelta',
            'format_timestamp'
        ],
        'overview_callbacks.py': [
            'dash', 'dash.dcc'
        ],
        'pipeline_callbacks.py': [
            'datetime.timedelta'
        ],
        'test_callbacks.py': [
            'datetime.timedelta'
        ],
        'shared_components.py': [
            'CARD_STYLE_ELEVATED', 'CHART_COLORS'
        ],
        'analytics_components.py': [
            'plotly.express as px'
        ],
        'chart_components.py': [
            'plotly.express as px',
            'dash.dcc'
        ],
        'dashboard_layout.py': [
            'DEFAULT_CHART_HEIGHT', 'DEFAULT_TIME_RANGE', 'DEFAULT_SYMBOL', 'TIME_RANGE_OPTIONS',
            'create_chart_card', 'create_control_group'
        ],
        'log_viewer.py': [
            'dash.Input', 'dash.Output', 'dash.State'
        ],
        'optimized_feature_data_service.py': [
            'numpy as np',
            'typing.Optional', 'typing.Tuple',
            'datetime.timedelta'
        ],
        'technical_indicators.py': [
            'typing.Optional', 'typing.Tuple'
        ],
        'unified_data_service.py': [
            'datetime.timedelta'
        ],
        'date_formatters.py': [
            'datetime.timedelta',
            'typing.Optional'
        ],
        'validators.py': [
            'typing.List', 'typing.Optional', 'typing.Union'
        ]
    }
    
    return patterns.get(filename, [])


def fix_line_length(file_path):
    """Fix long lines by wrapping them appropriately."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if len(line) > 120:
                # Try to wrap long lines intelligently
                fixed_line = wrap_long_line(line)
                if isinstance(fixed_line, list):
                    fixed_lines.extend(fixed_line)
                else:
                    fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        new_content = '\n'.join(fixed_lines)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed line lengths in {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error fixing line lengths in {file_path}: {e}")
        return False


def wrap_long_line(line):
    """Wrap a long line intelligently."""
    # Handle f-strings
    if 'f"' in line and len(line) > 120:
        return line  # Keep f-strings as is for now
    
    # Handle function calls with parameters
    if '(' in line and ')' in line and '=' in line:
        # Try to break at comma
        if ',' in line:
            parts = line.split(',')
            if len(parts) > 1:
                indent = len(line) - len(line.lstrip())
                base_indent = ' ' * indent
                continuation_indent = ' ' * (indent + 4)
                
                wrapped = [parts[0].rstrip() + ',']
                for part in parts[1:-1]:
                    wrapped.append(continuation_indent + part.strip() + ',')
                wrapped.append(continuation_indent + parts[-1].strip())
                
                return wrapped
    
    return line


def fix_f_strings(file_path):
    """Fix f-strings without placeholders."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix f-strings without placeholders
        content = re.sub(r'f"([^"]*)"', lambda m: f'"{m.group(1)}"' if '{' not in m.group(1) else m.group(0), content)
        content = re.sub(r"f'([^']*)'", lambda m: f"'{m.group(1)}'" if '{' not in m.group(1) else m.group(0), content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed f-strings in {file_path}")
        return True
        
    except Exception as e:
        print(f"Error fixing f-strings in {file_path}: {e}")
        return False


def comment_unused_variables(file_path):
    """Comment out unused variables."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Look for assignment patterns that might be unused
            if re.match(r'\s*\w+\s*=.*', line) and '# ' not in line:
                # Add a comment indicating it might be unused
                if any(var in line for var in ['rsi_data', 'indicators', 'original_count', 'cache_keys']):
                    fixed_lines.append(f"# {line.strip()}  # Currently unused")
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        new_content = '\n'.join(fixed_lines)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed unused variables in {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error fixing unused variables in {file_path}: {e}")
        return False


def fix_bare_except(file_path):
    """Fix bare except clauses."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace bare except with except Exception
        content = re.sub(r'except:', 'except Exception:', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed bare except in {file_path}")
        return True
        
    except Exception as e:
        print(f"Error fixing bare except in {file_path}: {e}")
        return False


def main():
    """Fix all dashboard flake8 issues comprehensively."""
    
    print("Starting comprehensive dashboard flake8 fixes...")
    
    # Get all Python files in dashboard directory
    dashboard_path = Path("src/dashboard")
    python_files = list(dashboard_path.rglob("*.py"))
    
    for file_path in python_files:
        if "__pycache__" in str(file_path):
            continue
        
        print(f"\nProcessing {file_path}...")
        
        # Apply all fixes
        remove_unused_imports_comprehensive(file_path)
        fix_line_length(file_path)
        fix_f_strings(file_path)
        comment_unused_variables(file_path)
        fix_bare_except(file_path)
    
    print("\nComprehensive dashboard flake8 fixes completed!")


if __name__ == "__main__":
    main()