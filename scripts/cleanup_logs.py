#!/usr/bin/env python3
"""
Log Cleanup and Database Connection Management Script
Provides utilities to clean up logs and monitor database connection health
"""

import os
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path

# Add the project root directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logging_config import (
    cleanup_old_logs, consolidate_logs, get_log_statistics,
    get_combined_logger
)
from src.utils.resilient_database_logging import (
    get_all_logger_stats, cleanup_resilient_loggers
)
from src.utils.db_pool_monitor import ConnectionPoolMonitor, create_optimized_db_manager
from src.data.storage.database import get_db_manager

logger = get_combined_logger("mltrading.log_cleanup_script")


def cleanup_logs_command(args):
    """Execute log cleanup"""
    logger.info("Starting log cleanup...")
    
    logs_dir = Path(args.logs_dir) if args.logs_dir else Path("logs")
    
    # Consolidate old logs
    if args.consolidate:
        logger.info("Consolidating old logs...")
        consolidate_results = consolidate_logs(logs_dir, max_age_days=args.consolidate_days)
        print(f"Consolidation: {consolidate_results['message']}")
        
        if consolidate_results.get('errors'):
            for error in consolidate_results['errors']:
                print(f"  Error: {error}")
    
    # Clean up old logs
    if args.cleanup:
        logger.info("Cleaning up old logs...")
        cleanup_results = cleanup_old_logs(
            logs_dir, 
            max_age_days=args.cleanup_days,
            max_compressed_age_days=args.cleanup_compressed_days
        )
        print(f"Cleanup: {cleanup_results['message']}")
        
        if cleanup_results.get('errors'):
            for error in cleanup_results['errors']:
                print(f"  Error: {error}")
    
    logger.info("Log cleanup completed")


def stats_command(args):
    """Show log and database statistics"""
    print("=== Log Statistics ===")
    
    logs_dir = Path(args.logs_dir) if args.logs_dir else Path("logs")
    log_stats = get_log_statistics(logs_dir)
    
    if log_stats['status'] == 'success':
        print(f"Total log files: {log_stats['total_log_files']}")
        print(f"Total compressed files: {log_stats['total_compressed_files']}")
        print(f"Total size: {log_stats['total_size'] / (1024*1024):.2f} MB")
        
        if log_stats.get('oldest_file'):
            oldest_date = datetime.fromtimestamp(log_stats['oldest_file']['mtime'])
            print(f"Oldest file: {log_stats['oldest_file']['name']} ({oldest_date})")
        
        if log_stats.get('newest_file'):
            newest_date = datetime.fromtimestamp(log_stats['newest_file']['mtime'])
            print(f"Newest file: {log_stats['newest_file']['name']} ({newest_date})")
        
        print("\nFiles by age:")
        for age_group, count in log_stats['files_by_age'].items():
            print(f"  {age_group}: {count} files")
    else:
        print(f"Error: {log_stats['message']}")
    
    print("\n=== Resilient Logger Statistics ===")
    resilient_stats = get_all_logger_stats()
    
    for logger_name, stats in resilient_stats.items():
        print(f"\n{logger_name.upper()} Logger:")
        print(f"  Queued: {stats['logs_queued']}")
        print(f"  Written to DB: {stats['logs_written_to_db']}")
        print(f"  Dropped: {stats['logs_dropped']}")
        print(f"  DB Errors: {stats['database_errors']}")
        print(f"  Queue Size: {stats['queue_size']}")
        print(f"  Thread Alive: {stats['thread_alive']}")
        
        if 'circuit_breaker' in stats:
            cb_stats = stats['circuit_breaker']
            print(f"  Circuit Breaker: {cb_stats['state']}")
            print(f"  Failures: {cb_stats['failure_count']}")
            print(f"  Successes: {cb_stats['success_count']}")


def monitor_command(args):
    """Monitor database connection pool"""
    print("=== Database Connection Pool Monitor ===")
    
    try:
        db_manager = get_db_manager()
        monitor = ConnectionPoolMonitor(db_manager)
        
        print(f"Monitoring every {args.interval} seconds. Press Ctrl+C to stop.")
        
        while True:
            status = monitor.get_pool_status()
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] Connection Pool Status:")
            
            if 'max_connections' in status:
                print(f"  Pool: {status['used_connections']}/{status['max_connections']} used")
                print(f"  Available: {status['available_connections']}")
                
                usage_pct = (status['used_connections'] / status['max_connections']) * 100
                if usage_pct > 80:
                    print(f"  ⚠️  HIGH USAGE: {usage_pct:.1f}%")
                elif usage_pct > 60:
                    print(f"  ⚡ Medium usage: {usage_pct:.1f}%")
                else:
                    print(f"  ✅ Normal usage: {usage_pct:.1f}%")
            else:
                print(f"  Status: {status.get('pool_status', 'unknown')}")
            
            print(f"  Connection errors: {status['connection_errors']}")
            
            if 'last_error' in status:
                print(f"  Last error: {status['last_error']}")
            
            # Test connection
            connection_ok = monitor.test_connection()
            print(f"  Connection test: {'✅ OK' if connection_ok else '❌ FAILED'}")
            
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        print(f"Error: {e}")


def optimize_command(args):
    """Optimize database connections for logging workload"""
    print("=== Database Connection Optimization ===")
    
    try:
        # Clean up resilient loggers
        print("Cleaning up resilient loggers...")
        cleanup_resilient_loggers()
        
        # Create optimized database manager
        print("Creating optimized database manager...")
        optimized_db = create_optimized_db_manager()
        
        # Test the optimized setup
        print("Testing optimized connection pool...")
        monitor = ConnectionPoolMonitor(optimized_db)
        status = monitor.get_pool_status()
        
        print(f"Optimized pool configuration:")
        if 'max_connections' in status:
            print(f"  Min connections: {status.get('min_connections', 'unknown')}")
            print(f"  Max connections: {status['max_connections']}")
            print(f"  Available: {status['available_connections']}")
        
        connection_ok = monitor.test_connection()
        print(f"Connection test: {'✅ OK' if connection_ok else '❌ FAILED'}")
        
        print("✅ Database optimization completed")
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")


def main():
    parser = argparse.ArgumentParser(description="Log cleanup and database connection management")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old log files')
    cleanup_parser.add_argument('--logs-dir', help='Logs directory path')
    cleanup_parser.add_argument('--consolidate', action='store_true', help='Consolidate old logs')
    cleanup_parser.add_argument('--consolidate-days', type=int, default=7, help='Days before consolidation')
    cleanup_parser.add_argument('--cleanup', action='store_true', help='Delete old log files')
    cleanup_parser.add_argument('--cleanup-days', type=int, default=30, help='Days before deletion')
    cleanup_parser.add_argument('--cleanup-compressed-days', type=int, default=90, help='Days before deleting compressed files')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show log and database statistics')
    stats_parser.add_argument('--logs-dir', help='Logs directory path')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor database connection pool')
    monitor_parser.add_argument('--interval', type=int, default=10, help='Monitoring interval in seconds')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize database connections')
    
    args = parser.parse_args()
    
    if args.command == 'cleanup':
        cleanup_logs_command(args)
    elif args.command == 'stats':
        stats_command(args)
    elif args.command == 'monitor':
        monitor_command(args)
    elif args.command == 'optimize':
        optimize_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()