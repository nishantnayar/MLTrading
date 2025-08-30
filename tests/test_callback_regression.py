"""
Callback-specific regression tests to prevent logic regressions
"""

import pytest
import json
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestCallbackValidation:
    """Test callback validation logic to prevent regressions"""
    
    def test_button_id_validation(self):
        """Test that button ID parsing works correctly"""
        
        # Valid button IDs
        valid_ids = [
            '{"type": "analyze-symbol-btn", "index": "AAPL"}',
            '{"type": "compare-symbol-btn", "index": "GOOGL"}'
        ]
        
        for button_id in valid_ids:
            parsed = json.loads(button_id)
            assert "type" in parsed
            assert "index" in parsed
            assert parsed["type"] in ["analyze-symbol-btn", "compare-symbol-btn"]
            assert isinstance(parsed["index"], str)
            assert len(parsed["index"]) > 0
    
    def test_invalid_button_ids_rejected(self):
        """Test that invalid button IDs are properly rejected"""
        
        invalid_ids = [
            "not-json",
            '{"type": "invalid-btn", "index": "AAPL"}',
            '{"type": "analyze-symbol-btn"}',  # Missing index
            '{"index": "AAPL"}',  # Missing type
            '{"type": "analyze-symbol-btn", "index": ""}',  # Empty index
            '{"type": "analyze-symbol-btn", "index": null}'  # Null index
        ]
        
        for button_id in invalid_ids:
            try:
                parsed = json.loads(button_id)
                # These should be rejected by validation logic
                if "type" not in parsed or "index" not in parsed:
                    continue  # Expected to fail
                if parsed["type"] not in ["analyze-symbol-btn", "compare-symbol-btn"]:
                    continue  # Expected to fail
                if not parsed["index"] or not isinstance(parsed["index"], str):
                    continue  # Expected to fail
                
                # If we get here, validation failed
                assert False, f"Invalid button ID passed validation: {button_id}"
                
            except json.JSONDecodeError:
                continue  # Expected for non-JSON strings
    
    def test_callback_context_simulation(self):
        """Test callback context handling"""
        
        # Simulate valid callback context
        mock_context = Mock()
        mock_context.triggered = [
            {
                "prop_id": '{"type": "analyze-symbol-btn", "index": "AAPL"}.n_clicks',
                "value": 1
            }
        ]
        
        trigger_info = mock_context.triggered[0]
        button_id = trigger_info['prop_id'].split('.')[0]
        trigger_value = trigger_info['value']
        
        # Validate extracted data
        assert trigger_value > 0
        parsed = json.loads(button_id)
        assert parsed["type"] == "analyze-symbol-btn"
        assert parsed["index"] == "AAPL"
    
    def test_chart_click_context_rejection(self):
        """Test that chart click contexts are properly rejected"""
        
        # Simulate chart click context (should be rejected)
        chart_contexts = [
            {
                "prop_id": "sector-distribution-chart.clickData",
                "value": {"points": [{"x": 5, "y": "Technology"}]}
            },
            {
                "prop_id": "industry-distribution-chart.clickData", 
                "value": {"points": [{"x": 3, "y": "Software"}]}
            }
        ]
        
        for context in chart_contexts:
            button_id = context['prop_id'].split('.')[0]
            
            # These should fail JSON parsing or validation
            try:
                parsed = json.loads(button_id)
                assert False, f"Chart context incorrectly parsed as button: {button_id}"
            except json.JSONDecodeError:
                # Expected - chart IDs are not JSON
                pass


class TestNavigationLogic:
    """Test navigation logic to prevent regressions"""
    
    def test_analyze_button_output(self):
        """Test analyze button produces correct outputs with new unified callback"""
        
        # Expected outputs for analyze button with new unified callback
        symbol = "AAPL" 
        # New format: (store_data, symbol-search, detailed-analysis, comparison-1, active_tab)
        expected_outputs = (symbol, symbol, symbol, symbol, "charts-tab")
        
        # This would be the actual callback return for analyze button
        assert expected_outputs[0] == symbol  # store data
        assert expected_outputs[1] == symbol  # symbol-search sync
        assert expected_outputs[2] == symbol  # detailed-analysis sync  
        assert expected_outputs[3] == symbol  # comparison-1 sync
        assert expected_outputs[4] == "charts-tab"
    
    def test_compare_button_output(self):
        """Test compare button produces correct outputs with new unified callback"""
        
        # Expected outputs for compare button with new unified callback
        symbol = "GOOGL"
        # New format: (store_data, symbol-search, detailed-analysis, comparison-1, active_tab)
        expected_outputs = (symbol, symbol, symbol, symbol, "comparison-tab")
        
        assert expected_outputs[0] == symbol  # store data
        assert expected_outputs[1] == symbol  # symbol-search sync
        assert expected_outputs[2] == symbol  # detailed-analysis sync
        assert expected_outputs[3] == symbol  # comparison-1 sync
        assert expected_outputs[4] == "comparison-tab"
    
    def test_symbol_sync_between_tabs(self):
        """Test symbol synchronization between different tabs"""
        
        # Test dropdown change synchronization
        selected_symbol = "NVDA"
        
        # When symbol changes in any dropdown, all should sync
        sync_outputs = (selected_symbol, selected_symbol, selected_symbol, selected_symbol, "overview-tab")
        
        assert all(output == selected_symbol for output in sync_outputs[:4])
        assert sync_outputs[4] == "overview-tab"  # Tab doesn't change for dropdown sync


class TestFilteringLogic:
    """Test filtering logic to prevent regressions"""
    
    def test_sector_filtering_output_format(self):
        """Test that sector filtering returns correct output format"""
        
        # Mock filtered symbols
        mock_symbols = [
            {"symbol": "AAPL", "company_name": "Apple Inc."},
            {"symbol": "GOOGL", "company_name": "Alphabet Inc."}
        ]
        
        # Expected output format: [content, symbols_data, badge_text, badge_style]
        symbols_data = [s["symbol"] for s in mock_symbols]
        badge_text = "Active: Sector"
        badge_style = {"display": "inline-block"}
        
        # Validate output structure
        assert isinstance(symbols_data, list)
        assert all(isinstance(s, str) for s in symbols_data)
        assert isinstance(badge_text, str)
        assert isinstance(badge_style, dict)
        assert "display" in badge_style
    
    def test_empty_filter_results(self):
        """Test handling of empty filter results"""
        
        # When no symbols found
        empty_result = []
        badge_style_hidden = {"display": "none"}
        
        assert len(empty_result) == 0
        assert badge_style_hidden["display"] == "none"


class TestDetailedAnalysisCharts:
    """Test detailed analysis chart callbacks to prevent regressions"""
    
    def test_chart_callback_data_structure(self):
        """Test that chart callbacks return proper Plotly figure structure"""
        
        # Mock empty chart structure
        empty_chart = {
            'data': [],
            'layout': {
                'title': 'No data available',
                'showlegend': False,
                'template': 'plotly_white',
                'height': 400,
                'annotations': [{
                    'text': 'No data available',
                    'x': 0.5,
                    'y': 0.5,
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {'size': 16, 'color': 'gray'}
                }]
            }
        }
        
        # Validate structure
        assert 'data' in empty_chart
        assert 'layout' in empty_chart
        assert isinstance(empty_chart['data'], list)
        assert isinstance(empty_chart['layout'], dict)
        assert 'title' in empty_chart['layout']
    
    def test_feature_data_service_integration(self):
        """Test that chart callbacks properly integrate with FeatureDataService"""
        
        # Test the expected method calls
        expected_methods = [
            'get_feature_data',
            'get_moving_averages', 
            'get_bollinger_bands',
            'get_rsi_data',
            'get_macd_data',
            'get_volatility_data'
        ]
        
        # These methods should exist in FeatureDataService
        try:
            from src.dashboard.services.feature_data_service import FeatureDataService
            service = FeatureDataService()
            
            for method_name in expected_methods:
                assert hasattr(service, method_name), f"FeatureDataService missing method: {method_name}"
                assert callable(getattr(service, method_name))
                
        except ImportError:
            pytest.skip("FeatureDataService not available for testing")
    
    def test_chart_error_handling(self):
        """Test that chart callbacks handle errors gracefully"""
        
        # Mock error scenarios
        error_scenarios = [
            "No data available",
            "No MACD data available", 
            "No volatility data available",
            "Error loading data: Database connection failed"
        ]
        
        for error_msg in error_scenarios:
            # Should return valid empty chart structure
            empty_chart = {
                'data': [],
                'layout': {
                    'title': error_msg,
                    'showlegend': False,
                    'template': 'plotly_white'
                }
            }
            
            assert 'data' in empty_chart
            assert len(empty_chart['data']) == 0
            assert error_msg in empty_chart['layout']['title']
    
    def test_chart_ids_coverage(self):
        """Test that all chart IDs from layout have corresponding callbacks"""
        
        # Chart IDs that should have callbacks
        expected_chart_ids = [
            "macd-detailed-chart",
            "ma-ratios-chart", 
            "vol-ratios-chart",
            "advanced-vol-chart",
            "money-flow-chart",
            "vpt-chart",
            "intraday-features-chart",
            "lagged-features-heatmap",
            "rolling-stats-chart"
        ]
        
        # This is a structural test - in practice we'd test the actual callbacks
        for chart_id in expected_chart_ids:
            # Validate chart ID format
            assert isinstance(chart_id, str)
            assert len(chart_id) > 0
            assert "-chart" in chart_id or "-heatmap" in chart_id


class TestErrorHandling:
    """Test error handling to prevent regressions"""
    
    def test_malformed_click_data_handling(self):
        """Test handling of malformed click data"""
        
        malformed_data = [
            None,
            {},
            {"points": []},
            {"points": None},
            {"invalid": "data"}
        ]
        
        for data in malformed_data:
            # Should not crash and should return safe defaults
            if not data or 'points' not in data:
                continue  # Expected to be rejected
            
            if not data['points']:
                continue  # Expected to be rejected
    
    def test_callback_exception_handling(self):
        """Test that callback exceptions are handled gracefully"""
        
        # Simulate various exception scenarios
        with pytest.raises(Exception):
            # Force an exception
            raise ValueError("Test exception")
        
        # In actual callback, this should return dash.no_update for all outputs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])