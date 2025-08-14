#!/usr/bin/env python3
"""
Run fast tests for quick development feedback.
This script runs only the tests marked with @pytest.mark.fast
"""

import subprocess
import sys
import os

def run_fast_tests():
    """Run only the fast tests."""
    print("🚀 Running Fast Tests for Quick Development Feedback")
    print("=" * 60)
    
    # Change to project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Run only fast tests
    cmd = [
        sys.executable, "-m", "pytest",
        "-m", "fast",
        "-v",
        "--tb=short",
        "--durations=10",
        "--durations-min=0.1"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_fast_tests()
    sys.exit(0 if success else 1)
