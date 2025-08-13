"""
Unit tests for dashboard layouts.
Tests layout components, chart components, and layout generation.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.layouts.dashboard_layout import create_dashboard_content
from src.dashboard.layouts.help_layout import create_help_layout
from src.dashboard.layouts.logs_layout import create_logs_layout
from src.dashboard.layouts.author_layout import create_author_layout
from src.dashboard.layouts.chart_components import (
    create_empty_chart,
    create_loading_chart,
    create_horizontal_bar_chart,
    create_candlestick_chart
)


class TestDashboardLayout:
    """Test suite for dashboard layout components."""
    
    def test_create_dashboard_content(self):
        """Test dashboard content creation."""
        content = create_dashboard_content()
        
        # Check that content is created
        assert content is not None
        assert hasattr(content, 'children')
        
        # Content should have multiple children (cards, charts, etc.)
        assert len(content.children) > 0
    
    def test_create_dashboard_content_basic_structure(self):
        """Test dashboard content creation basic structure."""
        content = create_dashboard_content()
        
        # Should create content without errors
        assert content is not None
        assert hasattr(content, 'children')
        
        # Should have some content
        assert len(content.children) > 0


class TestHelpLayout:
    """Test suite for help layout."""
    
    def test_create_help_layout(self):
        """Test help layout creation."""
        help_content = create_help_layout()
        
        # Check that help content is created
        assert help_content is not None
        assert hasattr(help_content, 'children')
        
        # Help content should contain multiple sections
        assert len(help_content.children) > 0
    
    def test_help_layout_structure(self):
        """Test help layout has expected structure."""
        help_content = create_help_layout()
        
        # Should have main container
        assert help_content is not None
        
        # Container should have children (help sections)
        children = help_content.children
        assert len(children) > 0
        
        # First child should typically be a title or header
        first_child = children[0]
        assert first_child is not None


class TestLogsLayout:
    """Test suite for logs layout."""
    
    @patch('src.dashboard.layouts.logs_layout.Path')
    def test_create_logs_layout(self, mock_path):
        """Test logs layout creation."""
        # Mock log file path
        mock_path.return_value.exists.return_value = True
        
        logs_content = create_logs_layout()
        
        # Check that logs content is created
        assert logs_content is not None
        assert hasattr(logs_content, 'children')
        
        # Logs content should contain log viewer components
        assert len(logs_content.children) > 0
    
    @patch('src.dashboard.layouts.logs_layout.Path')
    @patch('src.dashboard.layouts.logs_layout.open', new_callable=mock_open, 
           read_data="2023-01-01 10:00:00 INFO Test log message\n")
    def test_create_logs_layout_with_file(self, mock_file, mock_path):
        """Test logs layout creation with actual log file."""
        # Mock log file exists
        mock_path.return_value.exists.return_value = True
        
        logs_content = create_logs_layout()
        
        # Should create logs content without errors
        assert logs_content is not None
        assert hasattr(logs_content, 'children')
    
    @patch('src.dashboard.layouts.logs_layout.Path')
    def test_create_logs_layout_no_file(self, mock_path):
        """Test logs layout creation when log file doesn't exist."""
        # Mock log file doesn't exist
        mock_path.return_value.exists.return_value = False
        
        logs_content = create_logs_layout()
        
        # Should still create content (with "no logs" message)
        assert logs_content is not None
        assert hasattr(logs_content, 'children')


class TestAuthorLayout:
    """Test suite for author layout."""
    
    def test_create_author_layout(self):
        """Test author layout creation."""
        author_content = create_author_layout()
        
        # Check that author content is created
        assert author_content is not None
        assert hasattr(author_content, 'children')
        
        # Author content should contain author information
        assert len(author_content.children) > 0
    
    def test_author_layout_structure(self):
        """Test author layout has expected structure."""
        author_content = create_author_layout()
        
        # Should have main container
        assert author_content is not None
        
        # Container should have children (author info sections)
        children = author_content.children
        assert len(children) > 0
        
        # Should contain profile information
        first_child = children[0]
        assert first_child is not None


class TestChartComponents:
    """Test suite for chart components."""
    
    def test_create_empty_chart(self):
        """Test empty chart creation."""
        chart = create_empty_chart("Test Title")
        
        # Check that chart is created
        assert chart is not None
        assert hasattr(chart, 'data')
        assert hasattr(chart, 'layout')
        
        # Check title is set correctly
        assert chart.layout.title.text == "Test Title"
    
    def test_create_loading_chart(self):
        """Test loading chart creation."""
        chart = create_loading_chart("Loading test data...")
        
        # Check that chart is created
        assert chart is not None
        assert hasattr(chart, 'data')
        assert hasattr(chart, 'layout')
        assert len(chart.layout.annotations) > 0
    
    def test_create_horizontal_bar_chart(self):
        """Test horizontal bar chart creation."""
        data = {
            "categories": ["A", "B", "C"],
            "counts": [10, 15, 8]
        }
        
        chart = create_horizontal_bar_chart(data, "Test Bar Chart")
        
        # Check that chart is created
        assert chart is not None
        assert hasattr(chart, 'data')
        assert len(chart.data) > 0
        assert chart.data[0].orientation == 'h'
    
    def test_create_horizontal_bar_chart_empty_data(self):
        """Test horizontal bar chart with empty data."""
        data = {"categories": [], "counts": []}
        
        chart = create_horizontal_bar_chart(data, "Empty Chart")
        
        # Should return empty chart
        assert chart is not None
        assert len(chart.data) == 0  # Empty chart has no data traces
    
    def test_create_candlestick_chart_empty_data(self):
        """Test candlestick chart with empty data."""
        import pandas as pd
        empty_data = pd.DataFrame()
        
        chart = create_candlestick_chart(empty_data, "AAPL", "1M")
        
        # Should return empty chart
        assert chart is not None
        assert len(chart.data) == 0  # Empty chart has no data traces


class TestLayoutIntegration:
    """Integration tests for layout components."""
    
    def test_all_layouts_return_valid_components(self):
        """Test that all layout functions return valid Dash components."""
        layouts = [
            create_dashboard_content,
            create_help_layout,
            create_author_layout
        ]
        
        for layout_func in layouts:
            try:
                component = layout_func()
                assert component is not None
                assert hasattr(component, 'children')
            except Exception as e:
                pytest.fail(f"Layout function {layout_func.__name__} failed: {e}")
    
    @patch('src.dashboard.layouts.logs_layout.Path')
    def test_logs_layout_returns_valid_component(self, mock_path):
        """Test logs layout returns valid component."""
        mock_path.return_value.exists.return_value = False
        
        try:
            component = create_logs_layout()
            assert component is not None
            assert hasattr(component, 'children')
        except Exception as e:
            pytest.fail(f"Logs layout failed: {e}")
    
    def test_layout_components_have_required_attributes(self):
        """Test that layout components have required Dash attributes."""
        layouts = {
            "dashboard": create_dashboard_content,
            "help": create_help_layout,
            "author": create_author_layout
        }
        
        for name, layout_func in layouts.items():
            component = layout_func()
            
            # Should have children attribute
            assert hasattr(component, 'children'), f"{name} layout missing children"
            
            # Children should be iterable or a single component
            children = component.children
            if children is not None:
                # Should be iterable (list) or have attributes (single component)
                assert hasattr(children, '__iter__') or hasattr(children, 'children'), \
                    f"{name} layout children invalid structure"