"""
Prefect 3.x Data Collection Workflows
Market data ingestion with schema separation and database integration
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
from prefect import flow, task, get_run_logger
from prefect.task_runners import ConcurrentTaskRunner, ThreadPoolTaskRunner
from prefect.deployments import Deployment
from prefect.client.schemas.schedules import CronSchedule
from prefect.settings import PREFECT_LOGGING_LEVEL
from prefect.logging import get_logger

# Import existing system components
from ...data.collectors.yahoo_collector import fetch_yahoo_data, fetch_stock_info, load_symbols_from_file
from ...data.storage.database import get_db_manager
from ...utils.prefect_database_integration import get_prefect_db_manager
from ...utils.logging_config import get_correlation_id, set_correlation_id, log_data_collection_event

@task(name="load-trading-symbols", retries=2, retry_delay_seconds=10)
def load_symbols_task() -> List[str]:
    """Load active trading symbols from configuration"""
    logger = get_run_logger()
    prefect_db = get_prefect_db_manager()
    
    try:
        symbols = load_symbols_from_file('config/symbols.txt')
        
        if not symbols:
            raise ValueError("No symbols loaded from configuration file")
        
        # Log to application database
        prefect_db.log_workflow_event(
            event_type='load_symbols',
            workflow_name='data_collection',
            status='success',
            metadata={'symbol_count': len(symbols), 'symbols': symbols[:10]}  # Log first 10
        )
        
        logger.info(f"Loaded {len(symbols)} trading symbols")
        return symbols
        
    except Exception as e:
        prefect_db.log_workflow_event(
            event_type='load_symbols',
            workflow_name='data_collection',
            status='failed',
            metadata={'error': str(e)}
        )
        logger.error(f"Failed to load symbols: {e}")
        raise

@task(name="collect-symbol-batch", retries=3, retry_delay_seconds=[10, 30, 60])
def collect_symbol_batch_task(symbols: List[str], period: str = "1y", interval: str = "1h") -> Dict[str, Any]:
    """Collect market data for a batch of symbols"""
    logger = get_run_logger()
    prefect_db = get_prefect_db_manager()
    
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    results = {
        'batch_id': batch_id,
        'symbols': symbols,
        'successful_collections': [],
        'failed_collections': [],
        'total_records': 0,
        'processing_time': 0
    }
    
    start_time = datetime.now()
    
    try:
        db_manager = get_db_manager()
        
        for symbol in symbols:
            try:
                # Set correlation ID for this symbol collection
                symbol_correlation_id = f"{batch_id}_{symbol}"
                set_correlation_id(symbol_correlation_id)
                
                logger.info(f"Collecting data for {symbol}")
                
                # Fetch stock info
                stock_info = fetch_stock_info(symbol)
                db_manager.insert_stock_info(stock_info)
                
                # Fetch market data
                market_data_df = fetch_yahoo_data(symbol, period, interval)
                
                if not market_data_df.empty:
                    # Prepare and insert market data
                    from ...data.collectors.yahoo_collector import prepare_data_for_insert
                    data_list = prepare_data_for_insert(market_data_df)
                    
                    if data_list:
                        db_manager.insert_market_data(data_list)
                        results['successful_collections'].append({
                            'symbol': symbol,
                            'records': len(data_list),
                            'info_updated': True
                        })
                        results['total_records'] += len(data_list)
                        
                        # Log success to application system
                        log_data_collection_event(
                            operation_type='batch_collect',
                            data_source='yahoo',
                            symbol=symbol,
                            records_processed=len(data_list),
                            status='success'
                        )
                    else:
                        results['failed_collections'].append({
                            'symbol': symbol,
                            'error': 'No data to insert'
                        })
                else:
                    results['failed_collections'].append({
                        'symbol': symbol,
                        'error': 'No market data fetched'
                    })
                    
            except Exception as e:
                logger.error(f"Failed to collect data for {symbol}: {e}")
                results['failed_collections'].append({
                    'symbol': symbol,
                    'error': str(e)
                })
                
                # Log failure
                log_data_collection_event(
                    operation_type='batch_collect',
                    data_source='yahoo',
                    symbol=symbol,
                    records_processed=0,
                    status='failed',
                    error=str(e)
                )
        
        # Calculate processing time
        results['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        # Log batch completion
        prefect_db.log_workflow_event(
            event_type='batch_collection',
            workflow_name='data_collection',
            status='success' if results['successful_collections'] else 'failed',
            metadata=results
        )
        
        logger.info(f"Batch collection completed: {len(results['successful_collections'])} successful, "
                   f"{len(results['failed_collections'])} failed")
        
        return results
        
    except Exception as e:
        results['processing_time'] = (datetime.now() - start_time).total_seconds()
        results['error'] = str(e)
        
        prefect_db.log_workflow_event(
            event_type='batch_collection',
            workflow_name='data_collection',
            status='failed',
            metadata=results
        )
        
        logger.error(f"Batch collection failed: {e}")
        raise

@task(name="validate-market-data", retries=1)
def validate_market_data_task(collection_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate collected market data quality and completeness"""
    logger = get_run_logger()
    prefect_db = get_prefect_db_manager()
    
    validation_results = {
        'is_valid': True,
        'total_symbols_processed': 0,
        'successful_collections': 0,
        'failed_collections': 0,
        'total_records': 0,
        'data_quality_issues': [],
        'validation_timestamp': datetime.now().isoformat()
    }
    
    try:
        for batch_result in collection_results:
            validation_results['total_symbols_processed'] += len(batch_result['symbols'])
            validation_results['successful_collections'] += len(batch_result['successful_collections'])
            validation_results['failed_collections'] += len(batch_result['failed_collections'])
            validation_results['total_records'] += batch_result['total_records']
        
        # Data quality checks
        success_rate = (validation_results['successful_collections'] / 
                       validation_results['total_symbols_processed']) if validation_results['total_symbols_processed'] > 0 else 0
        
        if success_rate < 0.8:  # 80% success rate threshold
            validation_results['data_quality_issues'].append(
                f"Low success rate: {success_rate:.2%} < 80%"
            )
            validation_results['is_valid'] = False
        
        if validation_results['total_records'] == 0:
            validation_results['data_quality_issues'].append("No records collected")
            validation_results['is_valid'] = False
        
        # Log validation results
        prefect_db.log_workflow_event(
            event_type='data_validation',
            workflow_name='data_collection',
            status='success' if validation_results['is_valid'] else 'warning',
            metadata=validation_results
        )
        
        logger.info(f"Data validation completed: {'PASSED' if validation_results['is_valid'] else 'FAILED'}")
        
        return validation_results
        
    except Exception as e:
        validation_results['is_valid'] = False
        validation_results['error'] = str(e)
        
        prefect_db.log_workflow_event(
            event_type='data_validation',
            workflow_name='data_collection',
            status='failed',
            metadata=validation_results
        )
        
        logger.error(f"Data validation failed: {e}")
        raise

@task(name="update-data-freshness-metrics")
def update_data_freshness_metrics_task():
    """Update data freshness metrics in the database"""
    logger = get_run_logger()
    prefect_db = get_prefect_db_manager()
    
    try:
        db_manager = get_db_manager()
        
        # Update data freshness metrics
        with db_manager.get_connection() as conn:
            # Update last_updated timestamp for successful data collection
            update_query = """
            UPDATE stock_info 
            SET last_updated = NOW()
            WHERE symbol IN (
                SELECT DISTINCT symbol 
                FROM market_data 
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            )
            """
            
            result = conn.execute(update_query)
            updated_count = result.rowcount
            conn.commit()
        
        prefect_db.log_workflow_event(
            event_type='freshness_update',
            workflow_name='data_collection',
            status='success',
            metadata={'updated_symbols': updated_count}
        )
        
        logger.info(f"Updated freshness metrics for {updated_count} symbols")
        
    except Exception as e:
        prefect_db.log_workflow_event(
            event_type='freshness_update',
            workflow_name='data_collection',
            status='failed',
            metadata={'error': str(e)}
        )
        
        logger.error(f"Failed to update data freshness metrics: {e}")
        raise

@task(name="handle-data-quality-issues")
def handle_data_quality_issues_task(validation_results: Dict[str, Any]):
    """Handle data quality issues and send alerts"""
    logger = get_run_logger()
    prefect_db = get_prefect_db_manager()
    
    try:
        if not validation_results['data_quality_issues']:
            logger.info("No data quality issues to handle")
            return
        
        # Log data quality issues
        for issue in validation_results['data_quality_issues']:
            logger.warning(f"Data quality issue: {issue}")
        
        # Send alerts through existing system
        alert_data = {
            'alert_type': 'data_quality',
            'severity': 'HIGH' if not validation_results['is_valid'] else 'MEDIUM',
            'issues': validation_results['data_quality_issues'],
            'metrics': {
                'success_rate': validation_results['successful_collections'] / validation_results['total_symbols_processed'],
                'total_records': validation_results['total_records']
            }
        }
        
        prefect_db.log_workflow_event(
            event_type='quality_alert',
            workflow_name='data_collection',
            status='success',
            metadata=alert_data
        )
        
        logger.info(f"Handled {len(validation_results['data_quality_issues'])} data quality issues")
        
    except Exception as e:
        prefect_db.log_workflow_event(
            event_type='quality_alert',
            workflow_name='data_collection',
            status='failed',
            metadata={'error': str(e)}
        )
        
        logger.error(f"Failed to handle data quality issues: {e}")
        raise

@flow(name="Market Data Collection", log_prints=True)
def market_data_collection_flow(
    period: str = "1y",
    interval: str = "1h",
    batch_size: int = 20,
    max_workers: int = 5
) -> Dict[str, Any]:
    """
    Comprehensive market data collection workflow with validation
    Integrates with existing Yahoo collector while adding workflow orchestration
    """
    logger = get_run_logger()
    prefect_db = get_prefect_db_manager()
    
    # Set workflow correlation ID
    workflow_correlation_id = f"market_data_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    set_correlation_id(workflow_correlation_id)
    
    flow_start_time = datetime.now()
    
    try:
        logger.info(f"Starting market data collection workflow: {workflow_correlation_id}")
        
        # Load active trading symbols
        symbols = load_symbols_task()
        
        if not symbols:
            raise ValueError("No symbols to process")
        
        # Split symbols into batches
        symbol_batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
        logger.info(f"Processing {len(symbols)} symbols in {len(symbol_batches)} batches")
        
        # Collect data for all symbol batches in parallel
        collection_tasks = []
        for batch in symbol_batches:
            task_future = collect_symbol_batch_task.submit(
                symbols=batch,
                period=period,
                interval=interval,
                task_runner=ConcurrentTaskRunner(max_workers=max_workers)
            )
            collection_tasks.append(task_future)
        
        # Wait for all collection tasks to complete
        collection_results = [task.result() for task in collection_tasks]
        
        # Validate collected data
        validation_results = validate_market_data_task(collection_results)
        
        if validation_results['is_valid']:
            # Update data freshness metrics
            update_data_freshness_metrics_task()
            logger.info("Market data collection completed successfully")
        else:
            # Handle data quality issues
            handle_data_quality_issues_task(validation_results)
            logger.warning("Market data collection completed with quality issues")
        
        # Compile workflow results
        workflow_results = {
            'workflow_id': workflow_correlation_id,
            'status': 'success' if validation_results['is_valid'] else 'partial_success',
            'symbols_processed': len(symbols),
            'batches_processed': len(symbol_batches),
            'total_records_collected': validation_results['total_records'],
            'success_rate': validation_results['successful_collections'] / validation_results['total_symbols_processed'],
            'processing_time_seconds': (datetime.now() - flow_start_time).total_seconds(),
            'validation_results': validation_results
        }
        
        # Log workflow completion
        prefect_db.log_workflow_event(
            event_type='workflow_completion',
            workflow_name='market_data_collection',
            status=workflow_results['status'],
            metadata=workflow_results
        )
        
        return workflow_results
        
    except Exception as e:
        workflow_results = {
            'workflow_id': workflow_correlation_id,
            'status': 'failed',
            'error': str(e),
            'processing_time_seconds': (datetime.now() - flow_start_time).total_seconds()
        }
        
        prefect_db.log_workflow_event(
            event_type='workflow_failure',
            workflow_name='market_data_collection',
            status='failed',
            metadata=workflow_results
        )
        
        logger.error(f"Market data collection workflow failed: {e}")
        raise

# Deployment configuration for scheduled execution
market_data_deployment = Deployment.build_from_flow(
    flow=market_data_collection_flow,
    name="market-data-collection",
    schedule=CronSchedule(cron="*/15 9-16 * * 1-5", timezone="America/New_York"),
    work_queue_name="data-collection-pool",
    parameters={
        "period": "1y",
        "interval": "1h",
        "batch_size": 20,
        "max_workers": 5
    },
    description="Scheduled market data collection every 15 minutes during market hours",
    tags=["market-data", "yahoo-finance", "scheduled"]
)

if __name__ == "__main__":
    # Deploy the workflow
    market_data_deployment.apply()
    print("Market data collection workflow deployed successfully")