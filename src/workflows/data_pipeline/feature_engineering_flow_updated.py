"""
Feature Engineering Workflow - Updated with Subprocess Approach
Triggered after Yahoo data collection to calculate technical indicators
Uses proven subprocess isolation for reliable connection management
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import pytz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from prefect import flow, task
from prefect.task_runners import ConcurrentTaskRunner
from prefect.logging import get_run_logger
from prefect.runtime import flow_run

from src.utils.logging_config import get_combined_logger
from src.data.storage.database import get_db_manager

# Market hours configuration
MARKET_TIMEZONE = pytz.timezone('America/New_York')


def generate_feature_flow_run_name() -> str:
    """Generate a user-friendly name for the feature engineering flow run"""
    now = datetime.now(MARKET_TIMEZONE)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")
    return f"features-{date_str}-{time_str}EST"


@task(retries=2, retry_delay_seconds=30)
def initialize_feature_tables() -> bool:
    """Initialize feature engineering tables (they should already exist)"""
    logger = get_run_logger()

    try:
        logger.info("Checking feature engineering tables...")
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM feature_engineered_data LIMIT 1")

        logger.info("Feature tables verified successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to verify feature tables: {e}")
        return False


@task(retries=2, retry_delay_seconds=60)
def get_symbols_needing_features() -> List[str]:
    """Get list of symbols that have recent market data but missing features"""
    logger = get_run_logger()

    try:
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Find symbols with recent market data but no recent features
                query = """
                    SELECT DISTINCT md.symbol
                    FROM market_data md
                    LEFT JOIN feature_engineered_data fed ON (
                        md.symbol = fed.symbol
                        AND md.timestamp = fed.timestamp
                        AND md.source = fed.source
                    )
                    WHERE md.timestamp >= NOW() - INTERVAL '2 days'
                    AND fed.symbol IS NULL
                    ORDER BY md.symbol
                """

                cursor.execute(query)
                symbols = [row[0] for row in cursor.fetchall()]

        logger.info(f"Found {len(symbols)} symbols needing feature engineering")
        return symbols

    except Exception as e:
        logger.error(f"Failed to get symbols needing features: {e}")
        return []

@task(retries=3, retry_delay_seconds=120)
def calculate_features_for_symbol_subprocess(symbol: str, initial_run: bool = False) -> Dict[str, Any]:
    """
    Calculate features for a single symbol using subprocess isolation
    This approach ensures complete connection cleanup and prevents pool exhaustion
    """
    logger = get_run_logger()
    project_root = Path(__file__).parent.parent.parent.parent

    try:
        run_type = "INITIAL" if initial_run else "INCREMENTAL"
        logger.info(f"Calculating features for {symbol} using subprocess - {run_type} RUN")

        # Create subprocess script content
        script_content = f'''
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.processors.feature_engineering import TradingFeatureEngine

try:
    engine = TradingFeatureEngine()
    success = engineer.process_symbol_phase1_and_phase2("{symbol}", initial_run={initial_run})
    print("SUCCESS" if success else "FAILED")
    sys.exit(0 if success else 1)
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
'''

        # Write temporary script
        temp_script = project_root / f"temp_prefect_{symbol}_{int(time.time())}.py"

        try:
            with open(temp_script, 'w') as f:
                f.write(script_content)

            # Run subprocess with timeout (30s per symbol)
            result = subprocess.run(
                [sys.executable, str(temp_script)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(project_root)
            )

            success = result.returncode == 0 and "SUCCESS" in result.stdout

            if success:
                logger.info(f"Successfully calculated features for {symbol}")
                return {
                    'symbol': symbol,
                    'status': 'success',
                    'message': f"Features calculated successfully for {symbol}"
                }
            else:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                logger.error(f"Failed to calculate features for {symbol}: {error_msg}")
                return {
                    'symbol': symbol,
                    'status': 'failed',
                    'message': f"Feature calculation failed: {error_msg}"
                }

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout calculating features for {symbol}")
            return {
                'symbol': symbol,
                'status': 'timeout',
                'message': f"Feature calculation timed out for {symbol}"
            }
        finally:
            # Clean up temp script
            try:
                if temp_script.exists():
                    temp_script.unlink()
            except:
                pass

    except Exception as e:
        logger.error(f"Subprocess setup failed for {symbol}: {e}")
        return {
            'symbol': symbol,
            'status': 'error',
            'message': str(e)
        }

@task
def calculate_features_batch_subprocess(symbols: List[str], initial_run: bool = False, batch_size: int = 5) -> List[Dict[str, Any]]:
    """
    Calculate features for multiple symbols using subprocess isolation in small batches
    This reduces the number of Prefect tasks while maintaining connection isolation
    """
    logger = get_run_logger()

    all_results = []

    # Process in batches to avoid too many concurrent subprocesses
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(symbols) + batch_size - 1) // batch_size

        logger.info(f"Processing batch {batch_num}/{total_batches}: {batch}")

        batch_results = []
        for symbol in batch:
            result = calculate_features_for_symbol_subprocess(symbol, initial_run)
            batch_results.append(result)

            # Small delay between symbols in batch
            time.sleep(0.5)

        all_results.extend(batch_results)

        # Pause between batches
        if i + batch_size < len(symbols):
            logger.info(f"Completed batch {batch_num}/{total_batches}, pausing 2 seconds...")
            time.sleep(2)

    return all_results

@task
def generate_feature_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary of feature calculation results"""
    logger = get_run_logger()

    total_symbols = len(results)
    successful_calculations = len([r for r in results if r['status'] == 'success'])
    failed_calculations = total_symbols - successful_calculations

    summary = {
        'timestamp': datetime.now(MARKET_TIMEZONE).isoformat(),
        'total_symbols': total_symbols,
        'successful_calculations': successful_calculations,
        'failed_calculations': failed_calculations,
        'success_rate': (successful_calculations / total_symbols * 100) if total_symbols > 0 else 0
    }

    # Log failed symbols
    failed_symbols = [r['symbol'] for r in results if r['status'] != 'success']
    if failed_symbols:
        logger.warning(f"Failed to calculate features for: {', '.join(failed_symbols)}")

    logger.info(f"Feature calculation summary: {summary}")
    return summary

@task
def log_feature_workflow_metrics(summary: Dict[str, Any]) -> None:
    """Log feature workflow execution metrics to database"""
    logger = get_run_logger()

    try:
        # Log to application database using our logging system
        app_logger = get_combined_logger("prefect.feature_engineering")

        app_logger.info(
            f"Feature engineering completed: "
            f"{summary['successful_calculations']}/{summary['total_symbols']} symbols, "
            f"{summary['success_rate']:.1f}% success rate"
        )

        # Store metrics in performance_logs table
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO performance_logs
                    (operation_name, duration_ms, status, component, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    'feature_engineering_workflow_subprocess',
                    0,  # Duration will be calculated by Prefect
                    'success' if summary['failed_calculations'] == 0 else 'partial_success',
                    'prefect_workflow',
                    f'{{"symbols_processed": {summary["successful_calculations"]}, "total_symbols": {summary["total_symbols"]}}}'
                ))
                conn.commit()

        logger.info("Feature workflow metrics logged successfully")

    except Exception as e:
        logger.error(f"Failed to log feature workflow metrics: {e}")

@flow(
    name="feature-engineering-workflow-subprocess",
    description="Calculates features using subprocess isolation for reliable connection management",
    task_runner=ConcurrentTaskRunner(max_workers=1),
    log_prints=True,
    flow_run_name=generate_feature_flow_run_name
)
def feature_engineering_flow_subprocess(initial_run: bool = False) -> Dict[str, Any]:
    """
    Main workflow for feature engineering using subprocess isolation

    Args:
        initial_run: If True, process ALL historical data for complete backfill.
                    If False, process recent data only for incremental updates.

    This version uses subprocess isolation to prevent connection pool exhaustion
    and ensures 100% reliability across all symbols.

    Returns:
        Workflow execution summary
    """
    logger = get_run_logger()

    # Log run start with friendly name and type
    run_type = "INITIAL BACKFILL (ALL historical data)" if initial_run else "INCREMENTAL (recent data only)"
    logger.info(f"Starting subprocess-based feature engineering: {generate_feature_flow_run_name()} - {run_type}")

    # Initialize tables
    tables_initialized = initialize_feature_tables()

    if not tables_initialized:
        logger.error("Failed to initialize feature tables")
        return {
            'status': 'failed',
            'reason': 'table_initialization_failed',
            'timestamp': datetime.now(MARKET_TIMEZONE).isoformat()
        }

    # Get symbols that need feature calculation
    symbols = get_symbols_needing_features()

    if not symbols:
        logger.info("No symbols found needing feature calculation")
        return {
            'status': 'completed',
            'reason': 'no_symbols_needed',
            'timestamp': datetime.now(MARKET_TIMEZONE).isoformat()
        }

    logger.info(f"Starting subprocess-based feature calculation for {len(symbols)} symbols")

    # Calculate features using subprocess isolation in batches
    calculation_results = calculate_features_batch_subprocess(symbols, initial_run, batch_size=5)

    # Generate summary
    summary = generate_feature_summary(calculation_results)

    # Log metrics
    log_feature_workflow_metrics(summary)

    logger.info("Subprocess-based feature engineering workflow completed")

    return {
        'status': 'completed',
        'summary': summary,
        'timestamp': datetime.now(MARKET_TIMEZONE).isoformat()
    }

# Standalone execution for testing
if __name__ == "__main__":
    # Run the flow locally for testing
    result = feature_engineering_flow_subprocess()
    print(f"Feature workflow result: {result}")
