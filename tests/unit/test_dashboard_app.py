"""
Unit tests for the main dashboard application.
Tests the core app structure, navigation, and layout components.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.app import (
    create_navigation, 
    create_header, 
    create_footer,
    display_page,
    handle_initial_load
)


class TestDashboardApp:
    """Test suite for dashboard app components."""
    
    def test_create_navigation(self):
        """Test navigation component creation."""
        nav = create_navigation()
        
        # Check that navigation is created
        assert nav is not None
        assert hasattr(nav, 'children')
        
        # Navigation should contain the expected structure
        container = nav.children
        assert container is not None
        assert hasattr(container, 'children')
        
        # Should contain NavbarBrand and Nav
        nav_children = container.children
        assert len(nav_children) == 2
    
    def test_create_header(self):
        """Test header component creation."""
        header = create_header()
        
        # Check that header is created
        assert header is not None
        assert hasattr(header, 'children')
        
        # Header should contain a column
        col = header.children[0]
        assert col is not None
        assert hasattr(col, 'children')
        
        # Column should contain a div with header content
        header_div = col.children[0]
        assert header_div is not None
        assert hasattr(header_div, 'children')
        assert len(header_div.children) == 2  # H2 and P elements
    
    def test_create_footer(self):
        """Test footer component creation."""
        footer = create_footer()
        
        # Check that footer is created
        assert footer is not None
        assert hasattr(footer, 'children')
        
        # Footer should contain a column
        col = footer.children[0]
        assert col is not None
        assert hasattr(col, 'children')
        
        # Column should contain a div with footer content
        footer_div = col.children[0]
        assert footer_div is not None
        assert hasattr(footer_div, 'children')
        assert len(footer_div.children) == 2  # Two span elements
    
    @patch('src.dashboard.app.callback_context')
    @patch('src.dashboard.app.create_dashboard_content')
    @patch('src.dashboard.app.create_help_layout')
    @patch('src.dashboard.app.create_logs_layout')
    @patch('src.dashboard.app.create_author_layout')
    def test_display_page_default(self, mock_author, mock_logs, mock_help, 
                                  mock_dashboard, mock_ctx):
        """Test default page display (dashboard)."""
        # Mock callback context with no triggers
        mock_ctx.triggered = []
        mock_dashboard.return_value = "dashboard_content"
        
        result = display_page(None, None, None, None, None, None, None)
        
        mock_dashboard.assert_called_once()
        assert result == "dashboard_content"
    
    @patch('src.dashboard.app.callback_context')
    @patch('src.dashboard.app.create_help_layout')
    def test_display_page_help(self, mock_help, mock_ctx):
        """Test help page display."""
        # Mock callback context with help button trigger
        mock_ctx.triggered = [{'prop_id': 'nav-help.n_clicks'}]
        mock_help.return_value = "help_content"
        
        result = display_page(None, None, 1, None, None, None, None)
        
        mock_help.assert_called_once()
        assert result == "help_content"
    
    @patch('src.dashboard.app.callback_context')
    @patch('src.dashboard.app.create_logs_layout')
    def test_display_page_logs(self, mock_logs, mock_ctx):
        """Test logs page display."""
        # Mock callback context with logs button trigger
        mock_ctx.triggered = [{'prop_id': 'nav-logs.n_clicks'}]
        mock_logs.return_value = "logs_content"
        
        result = display_page(None, None, None, None, 1, None, None)
        
        mock_logs.assert_called_once()
        assert result == "logs_content"
    
    @patch('src.dashboard.app.callback_context')
    @patch('src.dashboard.app.create_author_layout')
    def test_display_page_author(self, mock_author, mock_ctx):
        """Test author page display."""
        # Mock callback context with author button trigger
        mock_ctx.triggered = [{'prop_id': 'nav-author.n_clicks'}]
        mock_author.return_value = "author_content"
        
        result = display_page(None, None, None, None, None, 1, None)
        
        mock_author.assert_called_once()
        assert result == "author_content"
    
    def test_handle_initial_load_first_run(self):
        """Test initial load handling on first run."""
        result = handle_initial_load(0)
        assert result is False  # Keep interval enabled for initial load
    
    def test_handle_initial_load_after_first_run(self):
        """Test initial load handling after first run."""
        result = handle_initial_load(1)
        assert result is True  # Disable interval after first run
    
    def test_handle_initial_load_multiple_runs(self):
        """Test initial load handling after multiple runs."""
        result = handle_initial_load(5)
        assert result is True  # Still disabled after multiple runs


class TestDashboardAppIntegration:
    """Integration tests for dashboard app."""
    
    @patch('src.dashboard.app.dash.Dash')
    def test_app_initialization(self, mock_dash):
        """Test that the app initializes properly."""
        # Mock the Dash app
        mock_app_instance = MagicMock()
        mock_dash.return_value = mock_app_instance
        
        # Import should work without errors
        try:
            import src.dashboard.app as app_module
            assert app_module.app is not None
        except Exception as e:
            pytest.fail(f"App initialization failed: {e}")
    
    def test_layout_structure(self):
        """Test that the app layout has the expected structure."""
        from src.dashboard.app import app
        
        # App should have a layout
        assert app.layout is not None
        assert hasattr(app.layout, 'children')
        
        # Layout should contain the main components
        layout_children = app.layout.children
        assert len(layout_children) >= 5  # Location, Interval, Navigation, Header, Content, Footer