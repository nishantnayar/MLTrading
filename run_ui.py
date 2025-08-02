#!/usr/bin/env python3
"""
Launcher script for ML Trading UI
Runs both FastAPI backend and Dash frontend
"""

import subprocess
import sys
import time
import threading
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger

def run_api():
    """Run the FastAPI backend"""
    logger.info("Starting FastAPI backend...")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "src.api.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ], cwd=project_root)

def run_dashboard():
    """Run the Dash frontend"""
    logger.info("Starting Dash dashboard...")
    subprocess.run([
        sys.executable, "src/dashboard/app.py"
    ], cwd=project_root)

def main():
    global logger
    logger = get_ui_logger("launcher")
    
    logger.info("ML Trading UI Launcher starting")
    print("ML Trading UI Launcher")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src").exists():
        logger.error("Not in project root directory")
        print("Error: Please run this script from the project root directory")
        sys.exit(1)
    
    logger.info("Starting services...")
    print("Starting services...")
    print("- FastAPI backend will run on http://localhost:8000")
    print("- Dash dashboard will run on http://localhost:8050")
    print("- Press Ctrl+C to stop all services")
    print()
    
    try:
        # Start API in a separate thread
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        logger.info("API thread started")
        
        # Give API a moment to start
        time.sleep(2)
        
        # Start dashboard in main thread
        run_dashboard()
        
    except KeyboardInterrupt:
        logger.info("Shutting down services...")
        print("\nShutting down services...")
        sys.exit(0)

if __name__ == "__main__":
    main() 