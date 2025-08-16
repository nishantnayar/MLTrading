#!/usr/bin/env python3
"""
Example script showing different ways to clean logs
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.log_manager import get_log_manager
from src.utils.logging_config import (
    consolidate_logs, 
    cleanup_old_logs, 
    get_log_statistics
)

def show_current_log_status():
    """Show current log status"""
    print("=== Current Log Status ===")
    stats = get_log_statistics()
    
    if stats['status'] == 'success':
        print(f"📊 Total log files: {stats['total_log_files']}")
        print(f"📦 Compressed files: {stats['total_compressed_files']}")
        print(f"💾 Total size: {stats['total_size']:,} bytes ({stats['total_size']/1024/1024:.1f} MB)")
        print(f"📅 Files by age:")
        print(f"   - Last 24h: {stats['files_by_age']['1d']}")
        print(f"   - Last 7d:  {stats['files_by_age']['7d']}")
        print(f"   - Last 30d: {stats['files_by_age']['30d']}")
        print(f"   - Older:    {stats['files_by_age']['older']}")
        
        if stats['oldest_file']:
            print(f"📜 Oldest file: {stats['oldest_file']['name']}")
        if stats['newest_file']:
            print(f"🆕 Newest file: {stats['newest_file']['name']}")
    else:
        print(f"❌ Error getting stats: {stats.get('message', 'Unknown error')}")
    print()

def method1_basic_cleanup():
    """Method 1: Basic cleanup - delete old files"""
    print("=== Method 1: Basic Cleanup ===")
    
    # Clean files older than 30 days, compressed files older than 90 days
    results = cleanup_old_logs(max_age_days=30, max_compressed_age_days=90)
    
    if results['status'] == 'success':
        print(f"✅ {results['message']}")
        print(f"   - Deleted {len(results['deleted_files'])} log files")
        print(f"   - Deleted {len(results['deleted_compressed'])} compressed files")
        print(f"   - Freed {results['total_space_freed']:,} bytes")
        
        if results['deleted_files']:
            print("   Deleted log files:")
            for file in results['deleted_files'][:5]:  # Show first 5
                print(f"     • {file}")
            if len(results['deleted_files']) > 5:
                print(f"     ... and {len(results['deleted_files']) - 5} more")
    else:
        print(f"❌ Cleanup failed: {results['message']}")
        if results['errors']:
            for error in results['errors']:
                print(f"   Error: {error}")
    print()

def method2_consolidation():
    """Method 2: Consolidate logs (compress old ones)"""
    print("=== Method 2: Log Consolidation ===")
    
    # Compress files older than 7 days
    results = consolidate_logs(max_age_days=7)
    
    if results['status'] == 'success':
        print(f"✅ {results['message']}")
        print(f"   - Compressed {len(results['compressed_files'])} files")
        print(f"   - Saved {results['total_space_saved']:,} bytes")
        
        if results['compressed_files']:
            print("   Compressed files:")
            for file in results['compressed_files']:
                print(f"     • {file} → {file}.gz")
    else:
        print(f"❌ Consolidation failed: {results['message']}")
        if results['errors']:
            for error in results['errors']:
                print(f"   Error: {error}")
    print()

def method3_log_manager():
    """Method 3: Using Log Manager (recommended)"""
    print("=== Method 3: Log Manager (Recommended) ===")
    
    manager = get_log_manager()
    
    # Health check first
    print("🏥 Health Check:")
    health = manager.health_check()
    print(f"   Status: {health['status']}")
    if health['recommendations']:
        print("   Recommendations:")
        for rec in health['recommendations']:
            print(f"     • {rec}")
    print()
    
    # Manual consolidation
    print("📦 Running consolidation...")
    consolidation_results = manager.manual_consolidation()
    if consolidation_results['status'] == 'success':
        print(f"   ✅ {consolidation_results['message']}")
    else:
        print(f"   ❌ {consolidation_results['message']}")
    
    # Manual cleanup
    print("🧹 Running cleanup...")
    cleanup_results = manager.manual_cleanup()
    if cleanup_results['status'] == 'success':
        print(f"   ✅ {cleanup_results['message']}")
    else:
        print(f"   ❌ {cleanup_results['message']}")
    print()

def method4_emergency_cleanup():
    """Method 4: Emergency cleanup (when disk space is critical)"""
    print("=== Method 4: Emergency Cleanup ===")
    print("⚠️  WARNING: This is aggressive cleanup for critical disk space situations")
    
    response = input("Are you sure you want to run emergency cleanup? (yes/no): ")
    if response.lower() != 'yes':
        print("Emergency cleanup cancelled.")
        return
    
    manager = get_log_manager()
    results = manager.emergency_cleanup()
    
    print(f"🚨 Emergency cleanup completed!")
    print(f"   Total space freed: {results.get('total_space_freed', 0):,} bytes")
    
    if results.get('emergency_consolidation', {}).get('status') == 'success':
        consolidation = results['emergency_consolidation']
        print(f"   📦 Consolidated {len(consolidation['compressed_files'])} files")
    
    if results.get('emergency_cleanup', {}).get('status') == 'success':
        cleanup = results['emergency_cleanup']
        print(f"   🧹 Deleted {len(cleanup['deleted_files'])} log files")
        print(f"   🧹 Deleted {len(cleanup['deleted_compressed'])} compressed files")
    
    if 'error' in results:
        print(f"   ❌ Error during emergency cleanup: {results['error']}")
    print()

def method5_custom_cleanup():
    """Method 5: Custom cleanup with specific parameters"""
    print("=== Method 5: Custom Cleanup ===")
    
    print("Options:")
    print("1. Conservative (compress >14 days, delete >60 days)")
    print("2. Moderate (compress >7 days, delete >30 days) [Default]")
    print("3. Aggressive (compress >3 days, delete >14 days)")
    print("4. Custom")
    
    choice = input("Choose option (1-4): ").strip()
    
    if choice == "1":
        consolidate_days, delete_days, delete_compressed_days = 14, 60, 120
    elif choice == "2":
        consolidate_days, delete_days, delete_compressed_days = 7, 30, 90
    elif choice == "3":
        consolidate_days, delete_days, delete_compressed_days = 3, 14, 30
    elif choice == "4":
        try:
            consolidate_days = int(input("Days before compression: "))
            delete_days = int(input("Days before deleting logs: "))
            delete_compressed_days = int(input("Days before deleting compressed: "))
        except ValueError:
            print("❌ Invalid input. Using defaults.")
            consolidate_days, delete_days, delete_compressed_days = 7, 30, 90
    else:
        print("Using default settings.")
        consolidate_days, delete_days, delete_compressed_days = 7, 30, 90
    
    print(f"🔧 Custom cleanup: compress >{consolidate_days}d, delete >{delete_days}d, delete compressed >{delete_compressed_days}d")
    
    # Run consolidation
    consolidation_results = consolidate_logs(max_age_days=consolidate_days)
    print(f"📦 Consolidation: {consolidation_results['message']}")
    
    # Run cleanup
    cleanup_results = cleanup_old_logs(max_age_days=delete_days, max_compressed_age_days=delete_compressed_days)
    print(f"🧹 Cleanup: {cleanup_results['message']}")
    
    total_saved = consolidation_results.get('total_space_saved', 0) + cleanup_results.get('total_space_freed', 0)
    print(f"💾 Total space saved: {total_saved:,} bytes ({total_saved/1024/1024:.1f} MB)")
    print()

def main():
    """Main menu for log cleanup"""
    print("🧹 ML Trading System - Log Cleanup Tool")
    print("=" * 50)
    
    # Show current status
    show_current_log_status()
    
    while True:
        print("Available cleanup methods:")
        print("1. 🧹 Basic Cleanup (delete old files)")
        print("2. 📦 Log Consolidation (compress old files)")
        print("3. 🎯 Log Manager (recommended - consolidate + cleanup)")
        print("4. 🚨 Emergency Cleanup (aggressive, for low disk space)")
        print("5. 🔧 Custom Cleanup (choose your own settings)")
        print("6. 📊 Show Current Status")
        print("0. ❌ Exit")
        print()
        
        choice = input("Choose an option (0-6): ").strip()
        print()
        
        if choice == "1":
            method1_basic_cleanup()
        elif choice == "2":
            method2_consolidation()
        elif choice == "3":
            method3_log_manager()
        elif choice == "4":
            method4_emergency_cleanup()
        elif choice == "5":
            method5_custom_cleanup()
        elif choice == "6":
            show_current_log_status()
        elif choice == "0":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
            print()
        
        # Show updated status after cleanup
        if choice in ["1", "2", "3", "4", "5"]:
            print("📊 Updated Status:")
            show_current_log_status()

if __name__ == "__main__":
    main()