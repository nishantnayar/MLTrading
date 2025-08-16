#!/usr/bin/env python3
"""
Regression Test Runner for ML Trading Dashboard
Runs automated tests and provides manual test checklist
"""

import subprocess
import sys
import time
from pathlib import Path
import webbrowser
from datetime import datetime

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print formatted section"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def run_automated_tests():
    """Run automated regression tests"""
    print_section("Running Automated Tests")
    
    try:
        # Install required testing packages if not present
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "dash[testing]", "selenium"], 
                      check=False, capture_output=True)
        
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_dashboard_regression.py", 
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All automated tests PASSED!")
            return True
        else:
            print("❌ Some automated tests FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Error running automated tests: {e}")
        return False

def start_dashboard_for_manual_testing():
    """Start dashboard server for manual testing"""
    print_section("Starting Dashboard for Manual Testing")
    
    try:
        # Start dashboard in background
        import subprocess
        import os
        
        # Change to project directory
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        print("Starting dashboard server...")
        print("Dashboard will be available at: http://localhost:8050")
        print("Press Ctrl+C to stop the server when manual testing is complete")
        
        # Start server
        subprocess.run([sys.executable, "src/dashboard/app.py"])
        
    except KeyboardInterrupt:
        print("\n✅ Dashboard server stopped")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

def show_manual_test_checklist():
    """Display manual test checklist"""
    print_section("Manual Test Checklist")
    
    checklist_path = Path("tests/regression_test_manual.md")
    if checklist_path.exists():
        print(f"📋 Manual test checklist: {checklist_path.absolute()}")
        print("\nOpening manual test checklist...")
        
        # Try to open in default browser/editor
        try:
            webbrowser.open(f"file://{checklist_path.absolute()}")
        except:
            print("Could not open automatically. Please open manually:")
            print(f"   {checklist_path.absolute()}")
    else:
        print("❌ Manual test checklist not found!")

def generate_test_report(automated_passed):
    """Generate test report"""
    print_section("Test Report")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# Regression Test Report
**Date**: {timestamp}
**Automated Tests**: {'✅ PASSED' if automated_passed else '❌ FAILED'}

## Automated Test Results
- Dashboard startup: {'✅' if automated_passed else '❌'}
- Tab navigation: {'✅' if automated_passed else '❌'} 
- Chart functionality: {'✅' if automated_passed else '❌'}
- Button interactions: {'✅' if automated_passed else '❌'}

## Manual Testing Required
Please complete the manual test checklist:
- [ ] Chart click behavior (no unwanted navigation)
- [ ] Symbol filtering functionality  
- [ ] Analyze/Compare button navigation
- [ ] Cross-tab data persistence
- [ ] Error handling scenarios

## Next Steps
{'1. Fix failing automated tests' if not automated_passed else '1. ✅ Automated tests passing'}
2. Complete manual testing checklist
3. Verify all critical user flows
4. Test in different browsers (optional)
"""
    
    report_path = Path("test_report.md")
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"📊 Test report generated: {report_path.absolute()}")
    return report_path

def main():
    """Main test runner"""
    print_header("ML Trading Dashboard - Regression Test Suite")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Run automated tests
    automated_passed = run_automated_tests()
    
    # Step 2: Generate report
    report_path = generate_test_report(automated_passed)
    
    # Step 3: Show manual testing options
    print_section("Manual Testing Options")
    print("Choose an option:")
    print("1. Start dashboard for manual testing")
    print("2. Show manual test checklist only") 
    print("3. Skip manual testing")
    
    try:
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice == "1":
            show_manual_test_checklist()
            time.sleep(2)  # Give time to open checklist
            start_dashboard_for_manual_testing()
        elif choice == "2":
            show_manual_test_checklist()
        elif choice == "3":
            print("Skipping manual testing")
        else:
            print("Invalid choice. Showing checklist only.")
            show_manual_test_checklist()
            
    except KeyboardInterrupt:
        print("\n\nTest runner interrupted by user")
    
    # Final summary
    print_header("Test Suite Complete")
    print(f"📊 Report: {report_path.absolute()}")
    print(f"📋 Manual Checklist: tests/regression_test_manual.md")
    
    if automated_passed:
        print("✅ Automated tests passed - Ready for manual testing")
    else:
        print("❌ Fix automated test failures before manual testing")

if __name__ == "__main__":
    main()