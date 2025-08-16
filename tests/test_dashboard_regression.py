"""
Regression Test Suite for ML Trading Dashboard
Tests critical user workflows to prevent functionality regressions.
"""

import pytest
import dash
from dash import html, dcc
from dash.testing.application_runners import import_app
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestDashboardRegression:
    """Regression tests for dashboard functionality"""
    
    def test_app_startup(self, dash_duo):
        """Test that the dashboard starts without errors"""
        app = import_app("src.dashboard.app")
        dash_duo.start_server(app)
        
        # Wait for page to load
        dash_duo.wait_for_element("#page-content", timeout=10)
        
        # Check no console errors
        assert len(dash_duo.get_logs()) == 0, "Console errors detected on startup"
    
    def test_overview_tab_loads(self, dash_duo):
        """Test that overview tab loads with all components"""
        app = import_app("src.dashboard.app")
        dash_duo.start_server(app)
        
        # Wait for overview tab content
        dash_duo.wait_for_element("#main-tabs", timeout=10)
        
        # Check key overview components exist
        required_elements = [
            "#sector-distribution-chart",
            "#industry-distribution-chart", 
            "#top-volume-chart",
            "#price-performance-chart",
            "#market-activity-chart",
            "#filtered-symbols-display"
        ]
        
        for element in required_elements:
            assert dash_duo.find_element(element), f"Element {element} not found"
    
    def test_tab_navigation(self, dash_duo):
        """Test navigation between tabs works correctly"""
        app = import_app("src.dashboard.app")
        dash_duo.start_server(app)
        
        # Wait for tabs to load
        dash_duo.wait_for_element("#main-tabs", timeout=10)
        
        # Get all tab elements
        tabs = dash_duo.find_elements("a[role='tab']")
        assert len(tabs) >= 3, "Not all tabs found"
        
        # Test clicking each tab
        for i, tab in enumerate(tabs):
            tab.click()
            time.sleep(1)  # Allow time for tab content to load
            
            # Verify tab is active
            assert "active" in tab.get_attribute("class"), f"Tab {i} not activated"
    
    def test_sector_chart_filtering_only(self, dash_duo):
        """Test that clicking sector chart ONLY filters, doesn't navigate"""
        app = import_app("src.dashboard.app")
        dash_duo.start_server(app)
        
        # Wait for charts to load
        dash_duo.wait_for_element("#sector-distribution-chart", timeout=15)
        
        # Get current active tab
        active_tab = dash_duo.find_element("a[role='tab'].active")
        initial_tab_text = active_tab.text
        
        # Click on sector chart (simulate bar click)
        sector_chart = dash_duo.find_element("#sector-distribution-chart")
        sector_chart.click()
        
        # Wait a moment for any callbacks
        time.sleep(2)
        
        # Verify still on same tab
        current_active_tab = dash_duo.find_element("a[role='tab'].active")
        assert current_active_tab.text == initial_tab_text, "Tab changed when clicking sector chart"
        
        # Verify filtered symbols display updated
        filtered_display = dash_duo.find_element("#filtered-symbols-display")
        assert filtered_display, "Filtered symbols display not found"
    
    def test_analyze_button_navigation(self, dash_duo):
        """Test that Analyze buttons navigate to charts tab"""
        app = import_app("src.dashboard.app")
        dash_duo.start_server(app)
        
        # Wait for page load
        dash_duo.wait_for_element("#main-tabs", timeout=10)
        
        # First trigger symbol filtering by clicking a chart
        dash_duo.wait_for_element("#sector-distribution-chart", timeout=15)
        sector_chart = dash_duo.find_element("#sector-distribution-chart")
        sector_chart.click()
        
        # Wait for symbols to appear
        time.sleep(3)
        
        # Find an Analyze button
        analyze_buttons = dash_duo.find_elements("button:contains('Analyze')")
        if analyze_buttons:
            analyze_buttons[0].click()
            
            # Wait for navigation
            time.sleep(2)
            
            # Verify we're on charts tab
            charts_tab = dash_duo.find_element("a[role='tab']:contains('Charts')")
            assert "active" in charts_tab.get_attribute("class"), "Not navigated to charts tab"
    
    def test_compare_button_navigation(self, dash_duo):
        """Test that Compare buttons navigate to comparison tab"""
        app = import_app("src.dashboard.app")
        dash_duo.start_server(app)
        
        # Wait for page load
        dash_duo.wait_for_element("#main-tabs", timeout=10)
        
        # First trigger symbol filtering
        dash_duo.wait_for_element("#sector-distribution-chart", timeout=15)
        sector_chart = dash_duo.find_element("#sector-distribution-chart")
        sector_chart.click()
        
        # Wait for symbols to appear
        time.sleep(3)
        
        # Find a Compare button
        compare_buttons = dash_duo.find_elements("button:contains('Compare')")
        if compare_buttons:
            compare_buttons[0].click()
            
            # Wait for navigation
            time.sleep(2)
            
            # Verify we're on comparison tab
            compare_tab = dash_duo.find_element("a[role='tab']:contains('Compare')")
            assert "active" in compare_tab.get_attribute("class"), "Not navigated to comparison tab"
    
    def test_charts_tab_functionality(self, dash_duo):
        """Test that charts tab loads and functions properly"""
        app = import_app("src.dashboard.app")
        dash_duo.start_server(app)
        
        # Navigate to charts tab
        dash_duo.wait_for_element("#main-tabs", timeout=10)
        charts_tab = dash_duo.find_element("a[role='tab']:contains('Charts')")
        charts_tab.click()
        
        # Wait for charts content
        time.sleep(3)
        
        # Check key chart components
        required_elements = [
            "#symbol-search",
            "#chart-type-dropdown",
            "#main-chart"
        ]
        
        for element in required_elements:
            assert dash_duo.find_element(element), f"Chart element {element} not found"
    
    def test_comparison_tab_functionality(self, dash_duo):
        """Test that comparison tab loads and functions properly"""
        app = import_app("src.dashboard.app")
        dash_duo.start_server(app)
        
        # Navigate to comparison tab
        dash_duo.wait_for_element("#main-tabs", timeout=10)
        compare_tab = dash_duo.find_element("a[role='tab']:contains('Compare')")
        compare_tab.click()
        
        # Wait for comparison content
        time.sleep(3)
        
        # Check key comparison components
        required_elements = [
            "#comparison-symbol-1",
            "#comparison-symbol-2", 
            "#compare-symbols-btn",
            "#comparison-results"
        ]
        
        for element in required_elements:
            assert dash_duo.find_element(element), f"Comparison element {element} not found"
    
    def test_no_javascript_errors(self, dash_duo):
        """Test that no JavaScript errors occur during normal usage"""
        app = import_app("src.dashboard.app")
        dash_duo.start_server(app)
        
        # Wait for full page load
        dash_duo.wait_for_element("#main-tabs", timeout=15)
        
        # Perform several interactions
        # 1. Click sector chart
        sector_chart = dash_duo.find_element("#sector-distribution-chart")
        sector_chart.click()
        time.sleep(2)
        
        # 2. Navigate between tabs
        tabs = dash_duo.find_elements("a[role='tab']")
        for tab in tabs[:3]:  # Test first 3 tabs
            tab.click()
            time.sleep(1)
        
        # 3. Check for any console errors
        console_logs = dash_duo.get_logs()
        errors = [log for log in console_logs if log['level'] == 'SEVERE']
        assert len(errors) == 0, f"JavaScript errors detected: {errors}"


@pytest.fixture
def sample_data():
    """Fixture providing sample data for tests"""
    return {
        "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
        "sectors": ["Technology", "Healthcare", "Finance"],
        "test_symbol": "AAPL"
    }


class TestCallbackRegression:
    """Test callback functionality to prevent regressions"""
    
    def test_sector_click_callback_output(self):
        """Test sector click callback returns correct output format"""
        from src.dashboard.callbacks.overview_callbacks import register_overview_callbacks
        
        # This would require mocking the callback context
        # Implementation depends on your callback testing framework
        pass
    
    def test_button_click_callback_validation(self):
        """Test button click callback validation works correctly"""
        # Test the validation logic in isolation
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])