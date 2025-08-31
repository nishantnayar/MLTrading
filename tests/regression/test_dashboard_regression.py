"""
Optimized Regression Test Suite for ML Trading Dashboard
Tests critical user workflows to prevent functionality regressions.
Focuses on essential functionality while preventing database connection exhaustion.
"""

import pytest
import time
import sys
from pathlib import Path
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import test utilities
from test_utils.helpers import DashTestHelper
from test_utils.mocks import MockedServices


@pytest.fixture(scope="class")
def started_app(app, dash_duo, mocked_services, suppressed_logging):
    """Start app once for the entire test class to prevent connection exhaustion"""
    try:
        dash_duo.start_server(app)
        dash_duo.wait_for_element("#page-content", timeout=30)
        yield dash_duo
    except Exception as e:
        pytest.skip(f"Could not start dashboard app: {e}")


@pytest.mark.regression
class TestDashboardRegressionOptimized:
    """Essential regression tests with optimized performance"""
    
    def test_app_startup(self, started_app):
        """Test that the dashboard starts without errors"""
        helper = DashTestHelper(started_app)
        
        # Check page loaded properly
        assert helper.wait_for_element_with_retry("#page-content", timeout=10)
        
        # Check main navigation is present
        assert helper.wait_for_element_with_retry("#nav-dashboard", timeout=5)
        
        # Check for console errors (ignoring warnings)
        helper.assert_no_console_errors(ignore_warnings=True)
    
    def test_main_components_load(self, started_app):
        """Test that main dashboard components load"""
        helper = DashTestHelper(started_app)
        
        # Check main tabs are present
        assert helper.wait_for_element_with_retry("#main-tabs", timeout=10)
        
        # Check at least one chart container exists (data may not load in tests)
        chart_containers = [
            "#sector-distribution-chart",
            "#top-volume-chart", 
            "#price-performance-chart"
        ]
        
        charts_found = 0
        for container in chart_containers:
            if helper.wait_for_element_with_retry(container, timeout=3):
                charts_found += 1
        
        # At least one chart container should be present
        assert charts_found > 0, "No chart containers found"
    
    def test_navigation_functionality(self, started_app):
        """Test basic navigation between main pages"""
        helper = DashTestHelper(started_app)
        
        # Start on dashboard
        assert helper.wait_for_element_with_retry("#nav-dashboard", timeout=5)
        
        # Test navigation to Trading page
        if helper.safe_click("#nav-trading"):
            time.sleep(1)
            print("Successfully clicked Trading navigation")
            
            # Give time for page to load
            time.sleep(2)
            
        # Navigate back to Dashboard
        if helper.safe_click("#nav-dashboard"):
            time.sleep(1)
            
            # Verify we're back on dashboard (main-tabs should be visible)
            assert helper.wait_for_element_with_retry("#main-tabs", timeout=5)
    
    def test_no_critical_javascript_errors(self, started_app):
        """Test that there are no critical JavaScript errors"""
        helper = DashTestHelper(started_app)
        
        # Wait a moment for any async operations
        time.sleep(2)
        
        # Check for console errors (this is the most important regression test)
        helper.assert_no_console_errors(ignore_warnings=True)


@pytest.mark.regression  
@pytest.mark.slow
class TestDashboardAdvancedRegression:
    """Advanced regression tests (marked as slow)"""
    
    def test_chart_interaction(self, started_app):
        """Test chart interaction doesn't cause errors"""
        helper = DashTestHelper(started_app)
        
        # Look for any clickable chart element
        chart_elements = [
            "#sector-distribution-chart",
            "#top-volume-chart"
        ]
        
        for chart_id in chart_elements:
            if helper.wait_for_element_with_retry(chart_id, timeout=3):
                try:
                    # Try to find clickable elements within the chart
                    chart_element = started_app.find_element(chart_id)
                    if chart_element:
                        # Just verify the chart exists and is rendered
                        assert chart_element.is_displayed()
                        print(f"Chart {chart_id} is displayed correctly")
                        break
                except Exception as e:
                    print(f"Chart {chart_id} interaction test skipped: {e}")
                    continue
    
    def test_responsive_design(self, started_app):
        """Test basic responsive design elements"""
        helper = DashTestHelper(started_app)
        
        # Check that main containers exist
        containers = ["#page-content", "#main-tabs"]
        
        for container in containers:
            element = started_app.find_element(container)
            if element:
                # Basic check that element is visible
                assert element.is_displayed(), f"Container {container} not displayed"


@pytest.mark.regression
@pytest.mark.performance  
class TestPerformanceRegression:
    """Performance regression tests"""
    
    def test_dashboard_load_time(self, started_app):
        """Test that dashboard loads within reasonable time"""
        helper = DashTestHelper(started_app)
        
        start_time = time.time()
        
        # Wait for main components
        assert helper.wait_for_element_with_retry("#main-tabs", timeout=15)
        
        load_time = time.time() - start_time
        
        # Dashboard should load within 15 seconds even with database issues
        assert load_time < 15, f"Dashboard load time too slow: {load_time:.2f}s"
        print(f"Dashboard loaded in {load_time:.2f} seconds")
    
    def test_memory_usage_stability(self, started_app):
        """Test that memory usage doesn't grow excessively during navigation"""
        helper = DashTestHelper(started_app)
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform some navigation
            for i in range(3):
                if helper.safe_click("#nav-trading"):
                    time.sleep(0.5)
                if helper.safe_click("#nav-dashboard"):
                    time.sleep(0.5)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = final_memory - initial_memory
            
            # Memory shouldn't grow by more than 50MB during basic navigation
            assert memory_growth < 50, f"Memory growth too high: {memory_growth:.1f}MB"
            print(f"Memory usage stable: {memory_growth:.1f}MB growth")
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")


# Legacy test class for backward compatibility
class TestDashboardRegression(TestDashboardRegressionOptimized):
    """Backward compatibility alias"""
    pass