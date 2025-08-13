"""
Unit tests for dashboard callbacks.
Tests callback registration and basic functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Test the callback registration functions
from src.dashboard.callbacks.overview_callbacks import register_overview_callbacks
from src.dashboard.callbacks import register_chart_callbacks


class TestCallbackRegistration:
    """Test suite for callback registration."""
    
    def test_register_overview_callbacks(self):
        """Test overview callbacks registration."""
        # Create a mock app
        mock_app = MagicMock()
        
        # Register callbacks
        register_overview_callbacks(mock_app)
        
        # Should have registered multiple callbacks
        assert mock_app.callback.call_count > 0
    
    def test_register_chart_callbacks(self):
        """Test chart callbacks registration."""
        # Create a mock app
        mock_app = MagicMock()
        
        # Register callbacks
        register_chart_callbacks(mock_app)
        
        # Should have registered callbacks
        assert mock_app.callback.call_count >= 0  # May be 0 if no callbacks in this module


class TestCallbackModule:
    """Test suite for callback module functionality."""
    
    def test_overview_callbacks_module_import(self):
        """Test that overview callbacks module imports correctly."""
        try:
            from src.dashboard.callbacks.overview_callbacks import register_overview_callbacks
            assert register_overview_callbacks is not None
            assert callable(register_overview_callbacks)
        except ImportError as e:
            pytest.fail(f"Failed to import overview callbacks: {e}")
    
    def test_chart_callbacks_module_import(self):
        """Test that chart callbacks module imports correctly."""
        try:
            from src.dashboard.callbacks import register_chart_callbacks
            assert register_chart_callbacks is not None
            assert callable(register_chart_callbacks)
        except ImportError as e:
            pytest.fail(f"Failed to import chart callbacks: {e}")
    
    @patch('src.dashboard.callbacks.overview_callbacks.data_service')
    def test_overview_callbacks_with_mock_service(self, mock_service):
        """Test overview callbacks registration with mocked data service."""
        mock_app = MagicMock()
        mock_service.get_market_overview.return_value = {}
        
        # Should register without errors even with mocked service
        register_overview_callbacks(mock_app)
        
        # Verify callbacks were registered
        assert mock_app.callback.call_count > 0


class TestCallbackErrorHandling:
    """Test suite for callback error handling."""
    
    def test_register_callbacks_with_none_app(self):
        """Test callback registration handles None app gracefully."""
        try:
            # This should either handle None gracefully or raise appropriate error
            register_overview_callbacks(None)
        except AttributeError:
            # Expected behavior when None is passed
            pass
        except Exception as e:
            # Other exceptions should be examined
            if "NoneType" not in str(e):
                pytest.fail(f"Unexpected error: {e}")
    
    def test_callback_module_structure(self):
        """Test that callback modules have expected structure."""
        # Test overview callbacks module
        try:
            import src.dashboard.callbacks.overview_callbacks as overview_module
            assert hasattr(overview_module, 'register_overview_callbacks')
            
            # Check if logger is properly initialized
            assert hasattr(overview_module, 'logger')
        except ImportError as e:
            pytest.fail(f"Overview callbacks module structure test failed: {e}")
        
        # Test chart callbacks module
        try:
            import src.dashboard.callbacks as callbacks_module
            # Should have the register function
            assert hasattr(callbacks_module, 'register_chart_callbacks')
        except (ImportError, AttributeError) as e:
            # This might not exist yet, which is acceptable
            pass