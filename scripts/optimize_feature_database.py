#!/usr/bin/env python3
"""
Database optimization script for feature_engineered_data table.
Applies performance optimizations, creates indexes, and sets up monitoring.

Usage:
    python scripts/optimize_feature_database.py [--dry-run] [--benchmark]
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.data.storage.database import DatabaseManager
from src.utils.database_performance_monitor import get_performance_monitor
from src.utils.logging_config import get_ui_logger

logger = get_ui_logger("database_optimizer")


def read_sql_file(file_path: Path) -> str:
    """Read SQL file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"SQL file not found: {file_path}")
        return ""


def apply_optimizations(db_manager: DatabaseManager, dry_run: bool = False) -> bool:
    """
    Apply database optimizations for feature_engineered_data table.
    
    Args:
        db_manager: Database manager instance
        dry_run: If True, only show what would be done without executing
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read optimization SQL
        sql_file = Path(__file__).parent.parent / 'src' / 'data' / 'storage' / 'optimize_feature_engineered_data.sql'
        optimization_sql = read_sql_file(sql_file)
        
        if not optimization_sql:
            logger.error("Could not read optimization SQL file")
            return False
        
        logger.info("=" * 60)
        logger.info("FEATURE_ENGINEERED_DATA OPTIMIZATION")
        logger.info("=" * 60)
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be applied")
            logger.info("\\nSQL to be executed:")
            logger.info("-" * 40)
            print(optimization_sql)
            return True
        
        # Apply optimizations
        with db_manager.get_connection_context() as conn:
            with conn.cursor() as cur:
                
                # Check if table exists
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = 'feature_engineered_data'
                """)
                
                if cur.fetchone()[0] == 0:
                    logger.error("feature_engineered_data table does not exist")
                    return False
                
                # Get current table stats before optimization
                logger.info("Getting baseline statistics...")
                cur.execute("SELECT COUNT(*) FROM feature_engineered_data")
                row_count = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM pg_indexes 
                    WHERE tablename = 'feature_engineered_data'
                """)
                index_count_before = cur.fetchone()[0]
                
                logger.info(f"Table stats before optimization:")
                logger.info(f"  - Rows: {row_count:,}")
                logger.info(f"  - Indexes: {index_count_before}")
                
                # Execute optimization SQL in chunks
                sql_statements = optimization_sql.split(';')
                executed_count = 0
                
                for i, statement in enumerate(sql_statements):
                    statement = statement.strip()
                    if not statement or statement.startswith('--'):
                        continue
                    
                    try:
                        logger.info(f"Executing statement {i+1}/{len(sql_statements)}: {statement[:50]}...")
                        start_time = time.time()
                        cur.execute(statement)
                        execution_time = time.time() - start_time
                        logger.info(f"  ✓ Completed in {execution_time:.2f}s")
                        executed_count += 1
                        
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.warning(f"  ⚠ Already exists: {statement[:30]}...")
                        else:
                            logger.error(f"  ✗ Failed: {e}")
                            continue
                
                # Commit all changes
                conn.commit()
                
                # Get stats after optimization
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM pg_indexes 
                    WHERE tablename = 'feature_engineered_data'
                """)
                index_count_after = cur.fetchone()[0]
                
                logger.info("\\nOptimization Results:")
                logger.info(f"  - SQL statements executed: {executed_count}")
                logger.info(f"  - Indexes before: {index_count_before}")
                logger.info(f"  - Indexes after: {index_count_after}")
                logger.info(f"  - New indexes created: {index_count_after - index_count_before}")
                
                return True
                
    except Exception as e:
        logger.error(f"Error applying optimizations: {e}")
        return False


def run_benchmarks(db_manager: DatabaseManager) -> Dict[str, Any]:
    """Run performance benchmarks before and after optimization"""
    logger.info("Running performance benchmarks...")
    
    monitor = get_performance_monitor()
    
    # Run benchmark queries
    benchmarks = monitor.benchmark_common_queries()
    
    if benchmarks:
        logger.info("\\nBenchmark Results:")
        for test_name, execution_time in benchmarks.items():
            if execution_time >= 0:
                logger.info(f"  {test_name}: {execution_time:.3f}s")
            else:
                logger.warning(f"  {test_name}: FAILED")
    
    return benchmarks


def generate_optimization_report(db_manager: DatabaseManager) -> Dict[str, Any]:
    """Generate comprehensive optimization report"""
    logger.info("Generating optimization report...")
    
    monitor = get_performance_monitor()
    report = monitor.generate_performance_report()
    
    # Print key metrics
    logger.info("\\nOptimization Report Summary:")
    
    table_stats = report.get('table_statistics', {})
    if table_stats:
        size_info = table_stats.get('table_size', {})
        data_info = table_stats.get('data_distribution', {})
        
        logger.info(f"  Table Size: {size_info.get('total_size', 'Unknown')}")
        logger.info(f"  Total Rows: {data_info.get('total_rows', 'Unknown'):,}")
        logger.info(f"  Unique Symbols: {data_info.get('unique_symbols', 'Unknown')}")
        logger.info(f"  RSI Coverage: {data_info.get('rsi_coverage_pct', 0):.1f}%")
    
    # Show recommendations
    recommendations = report.get('recommendations', [])
    if recommendations:
        logger.info("\\nOptimization Recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):
            logger.info(f"  {i}. [{rec['priority']}] {rec['description']}")
    
    return report


def main():
    """Main optimization script"""
    parser = argparse.ArgumentParser(description='Optimize feature_engineered_data table')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without executing')
    parser.add_argument('--benchmark', action='store_true',
                       help='Run performance benchmarks')
    parser.add_argument('--report', action='store_true',
                       help='Generate optimization report')
    
    args = parser.parse_args()
    
    logger.info("Starting feature database optimization...")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Run benchmarks before optimization (if requested)
        if args.benchmark:
            logger.info("\\n" + "="*50)
            logger.info("PRE-OPTIMIZATION BENCHMARKS")
            logger.info("="*50)
            pre_benchmarks = run_benchmarks(db_manager)
        
        # Apply optimizations
        if not args.report:  # Skip optimization if only generating report
            success = apply_optimizations(db_manager, dry_run=args.dry_run)
            if not success:
                logger.error("Optimization failed")
                return 1
        
        # Run benchmarks after optimization (if requested)
        if args.benchmark and not args.dry_run:
            logger.info("\\n" + "="*50)
            logger.info("POST-OPTIMIZATION BENCHMARKS") 
            logger.info("="*50)
            post_benchmarks = run_benchmarks(db_manager)
            
            # Compare results
            logger.info("\\nPerformance Comparison:")
            for test_name in pre_benchmarks.keys():
                pre_time = pre_benchmarks.get(test_name, -1)
                post_time = post_benchmarks.get(test_name, -1)
                
                if pre_time > 0 and post_time > 0:
                    improvement = ((pre_time - post_time) / pre_time) * 100
                    logger.info(f"  {test_name}: {improvement:+.1f}% change ({pre_time:.3f}s → {post_time:.3f}s)")
        
        # Generate report
        if args.report or args.benchmark:
            logger.info("\\n" + "="*50)
            logger.info("OPTIMIZATION REPORT")
            logger.info("="*50)
            report = generate_optimization_report(db_manager)
        
        logger.info("\\nOptimization completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\\nOptimization cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())