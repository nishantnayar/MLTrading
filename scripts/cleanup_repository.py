#!/usr/bin/env python3
"""
Repository Cleanup Script
Removes unnecessary files from ML Trading System repository
"""

import os
import shutil
from pathlib import Path
import glob

def cleanup_repository():
    """Clean up unnecessary files from the repository"""
    
    repo_root = Path(__file__).parent.parent
    removed_files = []
    removed_dirs = []
    
    print("=== ML Trading Repository Cleanup ===")
    print(f"Repository root: {repo_root}")
    
    # 1. Remove log files (can be regenerated)
    print("\n1. Removing log files...")
    log_patterns = [
        "logs/*.log*",
        "notebooks/exploration/logs/*.log"
    ]
    
    for pattern in log_patterns:
        for file_path in glob.glob(str(repo_root / pattern)):
            try:
                os.remove(file_path)
                removed_files.append(file_path)
                print(f"   Removed: {file_path}")
            except Exception as e:
                print(f"   Error removing {file_path}: {e}")
    
    # 2. Remove large binary ML data files (NOT notebooks)
    print("\n2. Removing large ML data files...")
    data_patterns = [
        "notebooks/exploration/*.npy",  # NumPy binary files
        "notebooks/exploration/*_config.csv",  # Generated config files
        "notebooks/exploration/*_metadata.csv",  # Generated metadata files
    ]
    
    for pattern in data_patterns:
        for file_path in glob.glob(str(repo_root / pattern)):
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                removed_files.append(file_path)
                print(f"   Removed: {file_path} ({file_size / (1024*1024):.1f} MB)")
            except Exception as e:
                print(f"   Error removing {file_path}: {e}")
    
    # 3. Remove unnecessary image files
    print("\n3. Removing unnecessary images...")
    unnecessary_images = [
        "notebooks/fig/Untitled.png"
    ]
    
    for file_path in unnecessary_images:
        full_path = repo_root / file_path
        if full_path.exists():
            try:
                os.remove(full_path)
                removed_files.append(str(full_path))
                print(f"   Removed: {full_path}")
            except Exception as e:
                print(f"   Error removing {full_path}: {e}")
    
    # 4. Remove IDE-specific directories
    print("\n4. Removing IDE-specific files...")
    ide_dirs = [
        ".cursor",
        ".claude"
    ]
    
    for dir_name in ide_dirs:
        dir_path = repo_root / dir_name
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                removed_dirs.append(str(dir_path))
                print(f"   Removed directory: {dir_path}")
            except Exception as e:
                print(f"   Error removing {dir_path}: {e}")
    
    # 5. Remove standalone test files
    print("\n5. Removing standalone test files...")
    standalone_tests = [
        "test_aten_ingm_pairs.py"
    ]
    
    for file_path in standalone_tests:
        full_path = repo_root / file_path
        if full_path.exists():
            try:
                os.remove(full_path)
                removed_files.append(str(full_path))
                print(f"   Removed: {full_path}")
            except Exception as e:
                print(f"   Error removing {full_path}: {e}")
    
    # 6. Remove pytest cache
    print("\n6. Removing pytest cache...")
    cache_dirs = [
        ".pytest_cache",
        "__pycache__"
    ]
    
    for root, dirs, files in os.walk(repo_root):
        for dir_name in dirs:
            if dir_name in cache_dirs:
                dir_path = Path(root) / dir_name
                try:
                    shutil.rmtree(dir_path)
                    removed_dirs.append(str(dir_path))
                    print(f"   Removed cache: {dir_path}")
                except Exception as e:
                    print(f"   Error removing {dir_path}: {e}")
    
    # 7. Remove empty directories (except .git, src structure, etc.)
    print("\n7. Removing empty directories...")
    for root, dirs, files in os.walk(repo_root, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            # Skip important directories
            if dir_name in ['.git', 'src', 'tests', 'docs', 'config', 'logs', 'notebooks']:
                continue
            try:
                if not any(dir_path.iterdir()):  # Directory is empty
                    os.rmdir(dir_path)
                    removed_dirs.append(str(dir_path))
                    print(f"   Removed empty directory: {dir_path}")
            except (OSError, Exception):
                pass  # Directory not empty or other error
    
    # Summary
    print("\n=== Cleanup Summary ===")
    print(f"Files removed: {len(removed_files)}")
    print(f"Directories removed: {len(removed_dirs)}")
    
    if removed_files:
        print("\nRemoved files:")
        for file_path in removed_files:
            print(f"  - {file_path}")
    
    if removed_dirs:
        print("\nRemoved directories:")
        for dir_path in removed_dirs:
            print(f"  - {dir_path}")
    
    print("\n✅ Repository cleanup completed!")
    
    return len(removed_files) + len(removed_dirs)

if __name__ == "__main__":
    cleanup_repository()