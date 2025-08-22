#!/usr/bin/env python3
"""
Test runner for ML Trading System.
Provides easy access to run different types of tests.
"""

import subprocess
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_unit_tests():
    """Run unit tests."""
    print("[UNIT] Running Unit Tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/unit/", 
        "-v", 
        "--tb=short",
        "--disable-warnings"  # Reduce noise from deprecation warnings
    ], cwd=Path(__file__).parent)
    return result.returncode == 0


def run_integration_tests():
    """Run integration tests."""
    print("[INTEGRATION] Running Integration Tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/integration/", 
        "-v", 
        "--tb=short"
    ], cwd=Path(__file__).parent)
    return result.returncode == 0


def run_api_tests():
    """Run API integration tests."""
    print("[API] Running API Integration Tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/integration/test_api_integration.py", 
        "-v", 
        "--tb=short"
    ], cwd=Path(__file__).parent)
    return result.returncode == 0


def run_all_tests():
    """Run all tests."""
    print("[ALL] Running All Tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", 
        "--tb=short",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term"
    ], cwd=Path(__file__).parent)
    return result.returncode == 0


def run_dashboard_tests():
    """Run dashboard-specific unit tests."""
    print("[DASHBOARD] Running Dashboard Tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/unit/", 
        "-k", "dashboard",
        "-v", 
        "--tb=short",
        "--disable-warnings"
    ], cwd=Path(__file__).parent)
    return result.returncode == 0


def run_quick_api_check():
    """Run a quick API health check."""
    print("[QUICK] Quick API Health Check...")
    try:
        from tests.integration.test_api_integration import run_api_tests
        return run_api_tests()
    except ImportError:
        print("Could not import API test module")
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="ML Trading Test Runner")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "api", "dashboard", "all", "quick"], 
        default="quick",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    print("ML Trading Test Runner")
    print("=" * 40)
    
    success = False
    
    if args.type == "unit":
        success = run_unit_tests()
    elif args.type == "integration":
        success = run_integration_tests()
    elif args.type == "api":
        success = run_api_tests()
    elif args.type == "dashboard":
        success = run_dashboard_tests()
    elif args.type == "all":
        success = run_all_tests()
    elif args.type == "quick":
        success = run_quick_api_check()
    
    if success:
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("\n[ERROR] Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 