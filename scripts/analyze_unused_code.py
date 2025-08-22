#!/usr/bin/env python3
"""
Analyze unused code in ML Trading System
Identifies potentially unused imports, functions, and classes
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
import importlib.util

def find_python_files(repo_root):
    """Find all Python files in the repository"""
    python_files = []
    for root, dirs, files in os.walk(repo_root):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', '.pytest_cache', 'logs']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    return python_files

def analyze_file(file_path):
    """Analyze a Python file for imports and definitions"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        imports = []
        definitions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'name': alias.name,
                        'line': node.lineno,
                        'file': str(file_path)
                    })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.append({
                            'type': 'from_import',
                            'module': node.module,
                            'name': alias.name,
                            'line': node.lineno,
                            'file': str(file_path)
                        })
            elif isinstance(node, ast.FunctionDef):
                definitions.append({
                    'type': 'function',
                    'name': node.name,
                    'line': node.lineno,
                    'file': str(file_path)
                })
            elif isinstance(node, ast.ClassDef):
                definitions.append({
                    'type': 'class',
                    'name': node.name,
                    'line': node.lineno,
                    'file': str(file_path)
                })
        
        return imports, definitions
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return [], []

def analyze_unused_code(repo_root):
    """Analyze the repository for unused code"""
    
    print("=== Unused Code Analysis ===")
    print(f"Repository root: {repo_root}")
    
    python_files = find_python_files(repo_root)
    print(f"Found {len(python_files)} Python files")
    
    all_imports = []
    all_definitions = []
    
    # Analyze all files
    for file_path in python_files:
        imports, definitions = analyze_file(file_path)
        all_imports.extend(imports)
        all_definitions.extend(definitions)
    
    print(f"Total imports: {len(all_imports)}")
    print(f"Total definitions: {len(all_definitions)}")
    
    # Find potentially unused imports
    print("\n=== Potentially Unused Imports ===")
    
    # Group imports by file
    imports_by_file = defaultdict(list)
    for imp in all_imports:
        imports_by_file[imp['file']].append(imp)
    
    unused_imports = []
    
    for file_path, imports in imports_by_file.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for imp in imports:
                import_name = imp['name']
                # Skip common imports that might be used indirectly
                if import_name in ['os', 'sys', 'logging', '__init__', '*']:
                    continue
                
                # Simple check: is the import name mentioned in the file after import?
                lines = content.split('\n')
                import_line = imp['line'] - 1
                
                # Check if import is used after the import line
                used = False
                for i, line in enumerate(lines[import_line + 1:], import_line + 1):
                    if import_name in line and not line.strip().startswith('#'):
                        used = True
                        break
                
                if not used:
                    unused_imports.append(imp)
        
        except Exception as e:
            continue
    
    # Display potentially unused imports
    if unused_imports:
        print("Found potentially unused imports:")
        for imp in unused_imports[:20]:  # Show first 20
            print(f"  {Path(imp['file']).name}:{imp['line']} - {imp.get('module', '')}.{imp['name']}")
    else:
        print("No obviously unused imports found")
    
    # Find potentially unused functions
    print("\n=== Potentially Unused Functions ===")
    
    function_definitions = [d for d in all_definitions if d['type'] == 'function']
    function_names = set(d['name'] for d in function_definitions)
    
    # Check which functions are never called
    unused_functions = []
    
    for func_def in function_definitions:
        func_name = func_def['name']
        
        # Skip special methods and common patterns
        if func_name.startswith('_') or func_name in ['main', 'run', 'setup', 'teardown']:
            continue
        
        # Check if function is called in any file
        called = False
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple check for function calls
                if f"{func_name}(" in content or f".{func_name}(" in content:
                    called = True
                    break
            except:
                continue
        
        if not called:
            unused_functions.append(func_def)
    
    if unused_functions:
        print("Found potentially unused functions:")
        for func in unused_functions[:15]:  # Show first 15
            print(f"  {Path(func['file']).name}:{func['line']} - {func['name']}()")
    else:
        print("No obviously unused functions found")
    
    # Summary
    print(f"\n=== Analysis Summary ===")
    print(f"Potentially unused imports: {len(unused_imports)}")
    print(f"Potentially unused functions: {len(unused_functions)}")
    
    return unused_imports, unused_functions

if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    analyze_unused_code(repo_root)