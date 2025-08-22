#!/usr/bin/env python3
"""
Comprehensive Repository Cleanup
Removes unnecessary files, analyzes unused code, and optimizes the repository
"""

import os
import shutil
from pathlib import Path
import glob
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Main cleanup function"""
    print("=== ML Trading Repository Comprehensive Cleanup ===")
    
    repo_root = Path(__file__).parent.parent
    print(f"Repository root: {repo_root}")
    
    # Get initial repository size
    initial_size = get_directory_size(repo_root)
    print(f"Initial repository size: {initial_size / (1024*1024):.1f} MB")
    
    # Run cleanup
    print("\n" + "="*50)
    from cleanup_repository import cleanup_repository
    files_removed = cleanup_repository()
    
    # Analyze unused code
    print("\n" + "="*50) 
    try:
        from analyze_unused_code import analyze_unused_code
        unused_imports, unused_functions = analyze_unused_code(repo_root)
        
        # Generate report
        generate_cleanup_report(repo_root, files_removed, unused_imports, unused_functions)
        
    except Exception as e:
        print(f"Code analysis failed: {e}")
    
    # Get final repository size
    final_size = get_directory_size(repo_root)
    space_saved = initial_size - final_size
    
    print(f"\n=== Final Summary ===")
    print(f"Initial size: {initial_size / (1024*1024):.1f} MB")
    print(f"Final size: {final_size / (1024*1024):.1f} MB") 
    print(f"Space saved: {space_saved / (1024*1024):.1f} MB")
    print(f"Files/directories removed: {files_removed}")
    
    # Create .gitignore additions
    create_gitignore_additions(repo_root)
    
    print("\n✅ Comprehensive cleanup completed!")
    print("Check cleanup_report.md for detailed analysis")

def get_directory_size(directory):
    """Calculate total size of directory"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass
    except Exception:
        pass
    return total_size

def generate_cleanup_report(repo_root, files_removed, unused_imports, unused_functions):
    """Generate a detailed cleanup report"""
    
    report_path = repo_root / "cleanup_report.md"
    
    with open(report_path, 'w') as f:
        f.write("# Repository Cleanup Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Files Removed\n\n")
        f.write(f"Total files/directories removed: {files_removed}\n\n")
        
        if unused_imports:
            f.write("## Potentially Unused Imports\n\n")
            f.write("The following imports might be unused and can be reviewed:\n\n")
            for imp in unused_imports[:20]:
                file_name = Path(imp['file']).name
                module = imp.get('module', '')
                if module:
                    f.write(f"- `{file_name}:{imp['line']}` - `from {module} import {imp['name']}`\n")
                else:
                    f.write(f"- `{file_name}:{imp['line']}` - `import {imp['name']}`\n")
            f.write("\n")
        
        if unused_functions:
            f.write("## Potentially Unused Functions\n\n")
            f.write("The following functions might be unused and can be reviewed:\n\n")
            for func in unused_functions[:15]:
                file_name = Path(func['file']).name
                f.write(f"- `{file_name}:{func['line']}` - `{func['name']}()`\n")
            f.write("\n")
        
        f.write("## Recommendations\n\n")
        f.write("1. **Log Files**: Automatically cleaned up - they regenerate as needed\n")
        f.write("2. **ML Data Files**: Large binary files removed - can be regenerated from notebooks\n")
        f.write("3. **Cache Files**: Pytest and Python cache files removed\n")
        f.write("4. **IDE Files**: Editor-specific configuration files removed\n")
        f.write("5. **Code Review**: Review potentially unused imports and functions above\n\n")
        
        f.write("## Next Steps\n\n")
        f.write("1. Review the potentially unused code listed above\n")
        f.write("2. Test the system to ensure nothing important was removed\n")
        f.write("3. Consider adding more items to `.gitignore`\n")
        f.write("4. Run tests to ensure system integrity: `python run_tests.py`\n")

def create_gitignore_additions(repo_root):
    """Create or update .gitignore with cleanup-related entries"""
    
    gitignore_path = repo_root / ".gitignore"
    
    additions = [
        "",
        "# Cleanup-related ignores",
        "*.log*",
        "logs/",
        "__pycache__/",
        "*.pyc",
        ".pytest_cache/",
        "*.npy",
        ".cursor/",
        ".claude/",
        "cleanup_report.md",
        "",
        "# ML/Data files", 
        "*.csv",
        "*.parquet",
        "*.pkl",
        "*.h5",
        "",
        "# Temporary files",
        "*.tmp",
        "*.temp",
        ".DS_Store",
        "Thumbs.db"
    ]
    
    # Check if .gitignore exists and what's already in it
    existing_content = ""
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            existing_content = f.read()
    
    # Add new entries that aren't already present
    new_entries = []
    for entry in additions:
        if entry and entry not in existing_content:
            new_entries.append(entry)
    
    if new_entries:
        with open(gitignore_path, 'a') as f:
            f.write('\n'.join(new_entries))
        print(f"Added {len(new_entries)} entries to .gitignore")

if __name__ == "__main__":
    main()