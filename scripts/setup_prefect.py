#!/usr/bin/env python3
"""
Prefect 3.x Setup Script for ML Trading System
Initializes Prefect with PostgreSQL schema separation
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from scripts.load_env import load_environment
    if not load_environment():
        print("Please set up your .env file before running this script")
        sys.exit(1)
except ImportError:
    print("Loading environment from system variables...")

from src.utils.prefect_database_integration import (
    get_prefect_db_manager, 
    initialize_prefect_database
)
from src.utils.logging_config import get_combined_logger

# Initialize logger
logger = get_combined_logger("mltrading.prefect.setup")

def check_prerequisites() -> Dict[str, bool]:
    """Check if all prerequisites are met for Prefect setup"""
    checks = {
        'python_version': sys.version_info >= (3, 8),
        'postgres_available': False,
        'prefect_installed': False,
        'env_variables': False
    }
    
    # Check Python version
    if not checks['python_version']:
        logger.error(f"Python 3.8+ required, found {sys.version}")
    
    # Check if Prefect is installed
    try:
        import prefect
        checks['prefect_installed'] = True
        version = prefect.__version__
        logger.info(f"Prefect version: {version}")
        
        # Check if version is 3.4.x or higher
        major, minor = map(int, version.split('.')[:2])
        if major < 3 or (major == 3 and minor < 4):
            logger.warning(f"Prefect 3.4+ recommended, found {version}")
        else:
            logger.info("Prefect version is compatible with enhanced features")
            
    except ImportError:
        logger.error("Prefect not installed. Run: pip install prefect>=3.4.14")
    
    # Check PostgreSQL connection
    try:
        db_manager = get_prefect_db_manager()
        health = db_manager.health_check()
        checks['postgres_available'] = health['overall_status'] == 'healthy'
        
        if checks['postgres_available']:
            logger.info("PostgreSQL connection verified")
        else:
            logger.error("PostgreSQL connection failed")
            
    except Exception as e:
        logger.error(f"PostgreSQL connection error: {e}")
    
    # Check environment variables
    required_env_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        checks['env_variables'] = False
    else:
        checks['env_variables'] = True
        logger.info("All required environment variables found")
    
    return checks

def setup_database_schema() -> bool:
    """Set up the Prefect database schema"""
    logger.info("Setting up Prefect database schema...")
    
    try:
        success = initialize_prefect_database()
        
        if success:
            # Verify schema setup
            db_manager = get_prefect_db_manager()
            verification = db_manager.verify_schema_separation()
            
            logger.info(f"Schema verification results: {verification}")
            
            if verification['prefect_schema']['exists']:
                logger.info("Prefect schema setup completed successfully")
                return True
            else:
                logger.error("Prefect schema verification failed")
                return False
        else:
            logger.error("Database schema initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"Database schema setup failed: {e}")
        return False

def configure_prefect_server() -> bool:
    """Configure and start Prefect server"""
    logger.info("Configuring Prefect server...")
    
    try:
        # Set Prefect configuration
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'mltrading')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        # Prefect database URL with schema specification
        prefect_db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?options=-csearch_path%3Dprefect"
        
        # Set environment variables for Prefect
        os.environ['PREFECT_API_DATABASE_CONNECTION_URL'] = prefect_db_url
        os.environ['PREFECT_API_URL'] = 'http://localhost:4200/api'
        
        logger.info("Prefect server configuration completed")
        logger.info(f"Database URL: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Prefect server configuration failed: {e}")
        return False

def create_work_pools() -> bool:
    """Create Prefect work pools for different workflow types"""
    logger.info("Creating Prefect work pools...")
    
    work_pools = [
        {
            'name': 'ml-trading-pool',
            'type': 'process',
            'description': 'Main work pool for ML trading workflows'
        },
        {
            'name': 'data-collection-pool',
            'type': 'process', 
            'description': 'Work pool for data collection workflows'
        },
        {
            'name': 'signal-generation-pool',
            'type': 'process',
            'description': 'Work pool for signal generation workflows'
        },
        {
            'name': 'risk-management-pool',
            'type': 'process',
            'description': 'Work pool for risk management workflows'
        }
    ]
    
    try:
        for pool in work_pools:
            # Create work pool using Prefect CLI
            cmd = [
                'prefect', 'work-pool', 'create',
                pool['name'],
                '--type', pool['type']
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Created work pool: {pool['name']}")
            else:
                # Work pool might already exist
                if 'already exists' in result.stderr:
                    logger.info(f"Work pool already exists: {pool['name']}")
                else:
                    logger.warning(f"Failed to create work pool {pool['name']}: {result.stderr}")
        
        return True
        
    except Exception as e:
        logger.error(f"Work pool creation failed: {e}")
        return False

def deploy_example_workflow() -> bool:
    """Deploy an example workflow to test the setup"""
    logger.info("Deploying example workflow...")
    
    try:
        # Import the market data collection workflow
        from src.workflows.data_pipeline.data_collection_flows import (
            market_data_collection_flow,
            market_data_deployment
        )
        
        # Apply the deployment
        deployment_id = market_data_deployment.apply()
        
        logger.info(f"Example workflow deployed successfully")
        logger.info(f"Deployment name: market-data-collection")
        return True
        
    except ImportError as e:
        logger.warning(f"Could not import workflow (this is OK for initial setup): {e}")
        logger.info("Skipping workflow deployment - will be available after Prefect server starts")
        return True
    except Exception as e:
        logger.error(f"Example workflow deployment failed: {e}")
        return False

def start_prefect_server() -> bool:
    """Start the Prefect server"""
    logger.info("Starting Prefect server...")
    
    try:
        # Start Prefect server in background
        cmd = ['prefect', 'server', 'start', '--host', '0.0.0.0', '--port', '4200']
        
        logger.info("Starting Prefect server at http://localhost:4200")
        logger.info("Run this command in a separate terminal to start the server:")
        logger.info(f"  {' '.join(cmd)}")
        
        # Don't actually start the server here, just provide instructions
        return True
        
    except Exception as e:
        logger.error(f"Prefect server start failed: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("=== Prefect 3.x Setup for ML Trading System ===")
    
    # Check prerequisites
    logger.info("1. Checking prerequisites...")
    checks = check_prerequisites()
    
    failed_checks = [check for check, passed in checks.items() if not passed]
    if failed_checks:
        logger.error(f"Prerequisites not met: {failed_checks}")
        logger.error("Please fix the issues above before continuing")
        return False
    
    logger.info("All prerequisites met")
    
    # Setup database schema
    logger.info("2. Setting up database schema...")
    if not setup_database_schema():
        logger.error("Database schema setup failed")
        return False
    
    # Configure Prefect server
    logger.info("3. Configuring Prefect server...")
    if not configure_prefect_server():
        logger.error("Prefect server configuration failed")
        return False
    
    # Skip work pool creation - requires running Prefect server
    logger.info("4. Skipping work pool creation - will create after server starts")
    logger.info("Work pools will be created when you start the Prefect server")
    
    # Skip workflow deployment - requires running Prefect server  
    logger.info("5. Skipping workflow deployment - will be available after server starts")
    logger.info("Workflows will be deployed when you start the Prefect server")
    
    # Provide server start instructions
    logger.info("6. Server startup instructions...")
    start_prefect_server()
    
    logger.info("\n=== Setup Complete ===")
    logger.info("Next steps:")
    logger.info("1. Start Prefect server: prefect server start --host 0.0.0.0 --port 4200")
    logger.info("2. Create work pools (in another terminal after server starts):")
    logger.info("   prefect work-pool create ml-trading-pool --type process")
    logger.info("   prefect work-pool create data-collection-pool --type process")
    logger.info("   prefect work-pool create signal-generation-pool --type process")
    logger.info("   prefect work-pool create risk-management-pool --type process")
    logger.info("3. Start worker: prefect worker start --pool ml-trading-pool")
    logger.info("4. Access UI: http://localhost:4200")
    logger.info("5. Monitor workflows and check database schemas")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)