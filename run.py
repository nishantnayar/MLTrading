#!/usr/bin/env python3
"""
ML Trading System - Main Runner
Convenient entry point for common operations
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Main runner with command options"""

    if len(sys.argv) < 2:
        print("ML Trading System Runner")
        print("Usage: python run.py [command]")
        print("")
        print("Available commands:")
        print("  ui          - Start the dashboard")
        print("  tests       - Run all tests")
        print("  regression  - Run regression tests")
        print("  collector   - Run Yahoo data collector")
        print("  prefect     - Setup Prefect")
        print("  cleanup     - Clean repository")
        return

    command = sys.argv[1].lower()
    scripts_dir = Path(__file__).parent / "scripts"

    if command == "ui":
        subprocess.run([sys.executable, str(scripts_dir / "run_ui.py")])
    elif command == "tests":
        subprocess.run([sys.executable, str(scripts_dir / "run_tests.py")])
    elif command == "regression":
        subprocess.run([sys.executable, str(scripts_dir / "run_regression_tests.py")])
    elif command == "collector":
        subprocess.run([sys.executable, str(scripts_dir / "run_yahoo_collector.py")])
    elif command == "prefect":
        subprocess.run([sys.executable, str(scripts_dir / "setup_prefect.py")])
    elif command == "cleanup":
        subprocess.run([sys.executable, str(scripts_dir / "comprehensive_cleanup.py")])
    else:
        print(f"Unknown command: {command}")
        print("Run 'python run.py' for available commands")


if __name__ == "__main__":
    main()
