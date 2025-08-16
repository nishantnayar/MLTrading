#!/usr/bin/env python3
"""
Quick log cleanup commands - copy and paste these into your Python console
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))

# Import the log management functions
from src.utils.log_manager import get_log_manager
from src.utils.logging_config import get_log_statistics

print("🧹 Quick Log Cleanup Commands")
print("=" * 40)

# 1. CHECK CURRENT STATUS
print("\n📊 1. Check current log status:")
print("stats = get_log_statistics()")
print("print(f'Files: {stats[\"total_log_files\"]}, Size: {stats[\"total_size\"]:,} bytes')")

# 2. QUICK CLEANUP
print("\n🧹 2. Quick cleanup (recommended):")
print("manager = get_log_manager()")
print("cleanup = manager.manual_cleanup()")
print("consolidation = manager.manual_consolidation()")
print("print(f'Cleanup: {cleanup[\"message\"]}')")
print("print(f'Consolidation: {consolidation[\"message\"]}')")

# 3. EMERGENCY CLEANUP
print("\n🚨 3. Emergency cleanup (aggressive):")
print("manager = get_log_manager()")
print("emergency = manager.emergency_cleanup()")
print("print(f'Emergency cleanup freed: {emergency[\"total_space_freed\"]:,} bytes')")

# 4. HEALTH CHECK
print("\n🏥 4. Health check:")
print("manager = get_log_manager()")
print("health = manager.health_check()")
print("print(f'Status: {health[\"status\"]}')")
print("if health['recommendations']: print('Recommendations:', health['recommendations'])")

# 5. CUSTOM CLEANUP
print("\n🔧 5. Custom cleanup:")
print("from src.utils.logging_config import consolidate_logs, cleanup_old_logs")
print("# Compress files older than 3 days")
print("consolidate_logs(max_age_days=3)")
print("# Delete files older than 14 days")
print("cleanup_old_logs(max_age_days=14, max_compressed_age_days=30)")

print("\n" + "=" * 40)
print("💡 TIP: Run the interactive cleanup script with:")
print("python clean_logs_example.py")