#!/usr/bin/env python3
"""
ML Trading System - Main Runner
Convenient entry point for common operations including documentation
"""

import sys
import subprocess
from pathlib import Path


def build_unified_docs():
    """Build unified MkDocs site with mkdocstrings API documentation"""
    print("Building unified documentation with mkdocstrings...")

    result = subprocess.run(["mkdocs", "build"], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"MkDocs build failed: {result.stderr}")
        return False

    print("SUCCESS: Unified documentation built successfully")
    return True


def serve_docs():
    """Serve the documentation site with live reload"""
    print("Serving documentation with live reload...")
    
    result = subprocess.run(["mkdocs", "serve", "--dev-addr", "localhost:8001"])
    return result.returncode == 0


def build_docs_main():
    """Documentation build process"""
    print("Building MLTrading documentation with mkdocstrings...")
    print("=" * 60)

    if not build_unified_docs():
        print("ERROR: Documentation build failed")
        return False

    print("=" * 60)
    print("SUCCESS: Documentation built successfully!")
    print()
    print("Structure:")
    print("  - Guides & Tutorials: Native MkDocs pages")
    print("  - API Reference: Auto-generated from docstrings")
    print("  - All in unified Material Design theme")
    print()
    print("Commands:")
    print("  python run.py docs-serve  # Serve with live reload")
    print("  mkdocs serve             # Alternative serve command")
    print("  mkdocs build             # Build static site")

    return True


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
        print("  docs        - Build documentation")
        print("  docs-serve  - Serve documentation with live reload")
        print("  optimize-db - Optimize feature_engineered_data database performance")
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
    elif command == "docs":
        build_docs_main()
    elif command == "docs-serve":
        serve_docs()
    elif command == "optimize-db":
        subprocess.run([sys.executable, str(scripts_dir / "optimize_feature_database.py")])
    else:
        print(f"Unknown command: {command}")
        print("Run 'python run.py' for available commands")


if __name__ == "__main__":
    main()
