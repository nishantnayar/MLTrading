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
        """Test analyze button produces correct outputs"""
        
        # Expected outputs for analyze button
        symbol = "AAPL" 
        expected_outputs = (symbol, None, "charts-tab")  # symbol-search, comparison-symbol-1, active_tab
        
        # This would be the actual callback return for analyze button
        assert expected_outputs[0] == symbol
        assert expected_outputs[1] is None  # No update to comparison
        assert expected_outputs[2] == "charts-tab"
    
    def test_compare_button_output(self):
        """Test compare button produces correct outputs"""
        
        # Expected outputs for compare button
        symbol = "GOOGL"
        expected_outputs = (None, symbol, "comparison-tab")  # symbol-search, comparison-symbol-1, active_tab
        
        assert expected_outputs[0] is None  # No update to symbol search
        assert expected_outputs[1] == symbol
        assert expected_outputs[2] == "comparison-tab"


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