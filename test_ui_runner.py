#!/usr/bin/env python3
"""
Quick test runner to verify the UI test functionality works.
This simulates what the Tests tab in the UI would do.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_test_suite(test_type="all"):
    """Run a specific test suite and return formatted results."""
    print(f"🧪 Running {test_type} tests...")
    print("=" * 50)
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Determine test path
    if test_type == "all":
        cmd.append("tests/")
    elif test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "dashboard":
        cmd.append("tests/unit/dashboard/")
    elif test_type == "volume":
        cmd.append("tests/unit/dashboard/test_volume_analysis.py")
    elif test_type == "indicators":
        cmd.append("tests/unit/indicators/test_technical_indicators.py")
    elif test_type == "summary":
        cmd.append("tests/unit/dashboard/test_technical_summary.py")
    
    # Add verbose output
    cmd.extend(["-v", "--tb=short"])
    
    # Change to project directory
    project_dir = Path(__file__).parent
    
    try:
        # Execute tests
        start_time = datetime.now()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=300  # 5 minute timeout
        )
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Parse output
        output = result.stdout + result.stderr
        total_tests, passed_tests, failed_tests, skipped_tests = parse_test_results(output)
        
        # Print results summary
        print(f"\n📊 Test Results Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⏭️ Skipped: {skipped_tests}")
        print(f"   ⏱️ Duration: {duration.total_seconds():.2f}s")
        print(f"   📅 Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print status
        if failed_tests > 0:
            print(f"\n🚨 Status: FAILED ({failed_tests} failures)")
            success = False
        elif skipped_tests > 0:
            print(f"\n⚠️ Status: PASSED WITH WARNINGS ({skipped_tests} skipped)")
            success = True
        else:
            print(f"\n🎉 Status: ALL TESTS PASSED")
            success = True
        
        print("=" * 50)
        
        # Show recent output (last 20 lines)
        print("\n📝 Recent Output:")
        output_lines = output.split('\n')
        for line in output_lines[-20:]:
            if line.strip():
                print(f"   {line}")
        
        return success, {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'skipped': skipped_tests,
            'duration': f"{duration.total_seconds():.2f}s",
            'status': 'PASSED' if success else 'FAILED'
        }
        
    except subprocess.TimeoutExpired:
        print("⏰ Test execution timed out after 5 minutes!")
        return False, {'error': 'timeout'}
    except Exception as e:
        print(f"❌ Error executing tests: {str(e)}")
        return False, {'error': str(e)}


def parse_test_results(output):
    """Parse pytest output to extract test statistics."""
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    skipped_tests = 0
    
    try:
        lines = output.split('\n')
        
        for line in lines:
            # Look for summary line like "109 passed, 2 skipped in 2.52s"
            if " passed" in line and " in " in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if i + 1 < len(parts):
                            if parts[i + 1] == "passed":
                                passed_tests = int(part)
                            elif parts[i + 1] == "failed":
                                failed_tests = int(part)
                            elif parts[i + 1] == "skipped":
                                skipped_tests = int(part)
                break
        
        total_tests = passed_tests + failed_tests + skipped_tests
        
    except Exception:
        # If parsing fails, try to count individual test results
        for line in output.split('\n'):
            if '::' in line and 'PASSED' in line:
                passed_tests += 1
            elif '::' in line and 'FAILED' in line:
                failed_tests += 1
            elif '::' in line and 'SKIPPED' in line:
                skipped_tests += 1
        
        total_tests = passed_tests + failed_tests + skipped_tests
    
    return total_tests, passed_tests, failed_tests, skipped_tests


def main():
    """Main function to run different test suites."""
    print("🚀 ML Trading Test Suite Runner")
    print("Testing the new UI test functionality...\n")
    
    # Test different suites
    test_suites = [
        ("volume", "Volume Analysis Tests"),
        ("indicators", "Technical Indicators Tests"),
        ("summary", "Technical Summary Tests"),
    ]
    
    overall_results = {
        'total_tests': 0,
        'total_passed': 0,
        'total_failed': 0,
        'total_skipped': 0,
        'suites_run': 0,
        'suites_passed': 0
    }
    
    for suite_type, suite_name in test_suites:
        print(f"\n🔍 Testing {suite_name}...")
        success, results = run_test_suite(suite_type)
        
        overall_results['suites_run'] += 1
        if success:
            overall_results['suites_passed'] += 1
        
        if 'error' not in results:
            overall_results['total_tests'] += results.get('total', 0)
            overall_results['total_passed'] += results.get('passed', 0)
            overall_results['total_failed'] += results.get('failed', 0)
            overall_results['total_skipped'] += results.get('skipped', 0)
        
        print("\n" + "─" * 50)
    
    # Final summary
    print(f"\n🏁 OVERALL TEST SUMMARY")
    print("=" * 50)
    print(f"   Test Suites Run: {overall_results['suites_run']}")
    print(f"   Suites Passed: {overall_results['suites_passed']}")
    print(f"   Total Tests: {overall_results['total_tests']}")
    print(f"   ✅ Total Passed: {overall_results['total_passed']}")
    print(f"   ❌ Total Failed: {overall_results['total_failed']}")
    print(f"   ⏭️ Total Skipped: {overall_results['total_skipped']}")
    
    if overall_results['total_failed'] == 0:
        print(f"\n🎉 ALL TEST SUITES PASSED! The UI test functionality is working correctly.")
        return 0
    else:
        print(f"\n🚨 Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())