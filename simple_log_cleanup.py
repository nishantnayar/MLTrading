#!/usr/bin/env python3
"""
Simple log cleanup script without Unicode characters
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.log_manager import get_log_manager
from src.utils.logging_config import get_log_statistics

def show_status():
    """Show current log status"""
    print("=== Current Log Status ===")
    stats = get_log_statistics()
    
    if stats['status'] == 'success':
        print(f"Total log files: {stats['total_log_files']}")
        print(f"Compressed files: {stats['total_compressed_files']}")
        print(f"Total size: {stats['total_size']:,} bytes ({stats['total_size']/1024/1024:.1f} MB)")
        print(f"Files by age:")
        print(f"  - Last 24h: {stats['files_by_age']['1d']}")
        print(f"  - Last 7d:  {stats['files_by_age']['7d']}")
        print(f"  - Last 30d: {stats['files_by_age']['30d']}")
        print(f"  - Older:    {stats['files_by_age']['older']}")
    else:
        print(f"Error getting stats: {stats.get('message', 'Unknown error')}")
    print()

def quick_cleanup():
    """Run quick cleanup"""
    print("=== Quick Cleanup ===")
    manager = get_log_manager()
    
    # Health check
    health = manager.health_check()
    print(f"Health status: {health['status']}")
    if health['recommendations']:
        print("Recommendations:")
        for rec in health['recommendations']:
            print(f"  - {rec}")
    
    # Consolidation
    print("Running consolidation...")
    consolidation = manager.manual_consolidation()
    print(f"Consolidation: {consolidation['message']}")
    
    # Cleanup
    print("Running cleanup...")
    cleanup = manager.manual_cleanup()
    print(f"Cleanup: {cleanup['message']}")
    print()

def emergency_cleanup():
    """Run emergency cleanup"""
    print("=== Emergency Cleanup ===")
    print("WARNING: This will aggressively clean logs!")
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    manager = get_log_manager()
    results = manager.emergency_cleanup()
    print(f"Emergency cleanup completed!")
    print(f"Total space freed: {results.get('total_space_freed', 0):,} bytes")
    print()

def main():
    print("ML Trading System - Log Cleanup Tool")
    print("="*40)
    
    show_status()
    
    print("Options:")
    print("1. Quick cleanup (recommended)")
    print("2. Emergency cleanup (aggressive)")
    print("3. Show status only")
    print("0. Exit")
    
    choice = input("Choose option (0-3): ").strip()
    
    if choice == "1":
        quick_cleanup()
        show_status()
    elif choice == "2":
        emergency_cleanup()
        show_status()
    elif choice == "3":
        show_status()
    elif choice == "0":
        print("Goodbye!")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()