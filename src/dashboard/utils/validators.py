"""
Input validation utilities for dashboard security and data integrity.
Provides validation functions for user inputs, API parameters, and data formats.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union


class InputValidator:
    """Comprehensive input validation for dashboard operations."""

    # Validation patterns
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,5}([.-][A-Z]{1,2})?$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    # Valid options for dropdowns
    VALID_SOURCES = ['yahoo', 'alpaca', 'polygon']
    VALID_TIME_RANGES = ['1d', '1w', '1m', '3m', '6m', '1y', '2y', '5y']
    VALID_CHART_TYPES = ['line', 'candlestick', 'bar', 'area']

    @classmethod


    def validate_symbol(cls, symbol: str) -> Tuple[bool, str]:
        """
        Validate stock symbol format.

        Args:
            symbol: Stock symbol to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not symbol:
            return False, "Symbol cannot be empty"

        if not isinstance(symbol, str):
            return False, "Symbol must be a string"

        symbol = symbol.upper().strip()

        if len(symbol) > 8:
            return False, "Symbol too long (max 8 characters)"

        if not cls.SYMBOL_PATTERN.match(symbol):
            return False, "Invalid symbol format. Use 1-5 uppercase letters, optionally with dots or hyphens"

        return True, ""

    @classmethod


    def validate_date_range(cls, start_date: str, end_date: str) -> Tuple[bool, str]:
        """
        Validate date range inputs.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate date format
            if not cls.DATE_PATTERN.match(start_date):
                return False, "Invalid start date format. Use YYYY-MM-DD"

            if not cls.DATE_PATTERN.match(end_date):
                return False, "Invalid end date format. Use YYYY-MM-DD"

            # Parse dates
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            # Validate date logic
            if start > end:
                return False, "Start date cannot be after end date"

            # Check if dates are too far in the future
            if start > datetime.now() + timedelta(days=1):
                return False, "Start date cannot be in the future"

            if end > datetime.now() + timedelta(days=1):
                return False, "End date cannot be in the future"

            # Check if date range is too large (prevent performance issues)
            if (end - start).days > 3650:  # 10 years
                return False, "Date range too large (max 10 years)"

            return True, ""

        except ValueError as e:
            return False, f"Invalid date format: {str(e)}"

    @classmethod


    def validate_time_range(cls, time_range: str) -> Tuple[bool, str]:
        """
        Validate time range selection.

        Args:
            time_range: Time range code (e.g., '1d', '1m', '1y')

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not time_range:
            return False, "Time range cannot be empty"

        if not isinstance(time_range, str):
            return False, "Time range must be a string"

        if time_range not in cls.VALID_TIME_RANGES:
            return False, f"Invalid time range. Valid options: {', '.join(cls.VALID_TIME_RANGES)}"

        return True, ""

    @classmethod


    def validate_source(cls, source: str) -> Tuple[bool, str]:
        """
        Validate data source selection.

        Args:
            source: Data source name

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not source:
            return False, "Source cannot be empty"

        if not isinstance(source, str):
            return False, "Source must be a string"

        if source not in cls.VALID_SOURCES:
            return False, f"Invalid source. Valid options: {', '.join(cls.VALID_SOURCES)}"

        return True, ""

    @classmethod


    def validate_positive_integer(cls, value: Any, field_name: str = "Value", max_value: int = None) -> Tuple[bool, str]:
        """
        Validate positive integer input.

        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            max_value: Maximum allowed value

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            int_value = int(value)

            if int_value <= 0:
                return False, f"{field_name} must be a positive integer"

            if max_value and int_value > max_value:
                return False, f"{field_name} cannot exceed {max_value}"

            return True, ""

        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid integer"

    @classmethod


    def validate_portfolio_params(cls, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate portfolio-related parameters.

        Args:
            params: Dictionary of parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ['symbol', 'quantity', 'action']

        # Check required fields
        for field in required_fields:
            if field not in params:
                return False, f"Missing required field: {field}"

        # Validate symbol
        is_valid, error = cls.validate_symbol(params['symbol'])
        if not is_valid:
            return False, f"Symbol validation failed: {error}"

        # Validate quantity
        is_valid, error = cls.validate_positive_integer(params['quantity'], "Quantity", max_value=1000000)
        if not is_valid:
            return False, f"Quantity validation failed: {error}"

        # Validate action
        valid_actions = ['BUY', 'SELL', 'HOLD']
        if params['action'] not in valid_actions:
            return False, f"Invalid action. Valid options: {', '.join(valid_actions)}"

        # Validate optional price if provided
        if 'price' in params:
            try:
                price = float(params['price'])
                if price <= 0:
                    return False, "Price must be positive"
                if price > 1000000:
                    return False, "Price too high (max $1,000,000)"
            except (ValueError, TypeError):
                return False, "Price must be a valid number"

        return True, ""

    @classmethod


    def sanitize_string(cls, input_string: str, max_length: int = 100) -> str:
        """
        Sanitize string input for safe database storage.

        Args:
            input_string: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(input_string, str):
            return ""

        # Remove or escape potentially dangerous characters
        sanitized = input_string.strip()

        # Remove SQL injection patterns
        dangerous_patterns = [
            r"[';]",  # SQL terminators
            r"--",    # SQL comments
            r"/\*",   # SQL block comment start
            r"\*/",   # SQL block comment end
            r"<script",  # XSS script tags
            r"</script>",
            r"javascript:",
            r"on\w+\s*=",  # HTML event handlers
        ]

        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    @classmethod


    def validate_api_request(cls, request_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate and sanitize API request data.

        Args:
            request_data: Raw request data dictionary

        Returns:
            Tuple of (is_valid, error_message, sanitized_data)
        """
        sanitized = {}

        # Common validations for API requests
        if 'symbol' in request_data:
            is_valid, error = cls.validate_symbol(request_data['symbol'])
            if not is_valid:
                return False, f"Symbol validation failed: {error}", {}
            sanitized['symbol'] = request_data['symbol'].upper().strip()

        if 'source' in request_data:
            is_valid, error = cls.validate_source(request_data['source'])
            if not is_valid:
                return False, f"Source validation failed: {error}", {}
            sanitized['source'] = request_data['source']

        if 'time_range' in request_data:
            is_valid, error = cls.validate_time_range(request_data['time_range'])
            if not is_valid:
                return False, f"Time range validation failed: {error}", {}
            sanitized['time_range'] = request_data['time_range']

        if 'days' in request_data:
            is_valid, error = cls.validate_positive_integer(request_data['days'], "Days", max_value=3650)
            if not is_valid:
                return False, f"Days validation failed: {error}", {}
            sanitized['days'] = int(request_data['days'])

        # Sanitize string fields
        for field in ['sector', 'industry', 'company_name']:
            if field in request_data:
                sanitized[field] = cls.sanitize_string(str(request_data[field]))

        return True, "", sanitized

    @classmethod


    def validate_callback_inputs(cls, **kwargs) -> Dict[str, Any]:
        """
        Validate Dash callback inputs and provide safe defaults.

        Args:
            **kwargs: Callback input values

        Returns:
            Dictionary of validated inputs with safe defaults
        """
        validated = {}

        # Handle symbol input
        symbol = kwargs.get('symbol', 'AAPL')
        is_valid, _ = cls.validate_symbol(symbol)
        validated['symbol'] = symbol if is_valid else 'AAPL'

        # Handle time range
        time_range = kwargs.get('time_range', '1m')
        is_valid, _ = cls.validate_time_range(time_range)
        validated['time_range'] = time_range if is_valid else '1m'

        # Handle source
        source = kwargs.get('source', 'yahoo')
        is_valid, _ = cls.validate_source(source)
        validated['source'] = source if is_valid else 'yahoo'

        # Handle numeric inputs
        for field in ['n_clicks', 'days', 'limit']:
            value = kwargs.get(field, 0)
            try:
                validated[field] = max(0, int(value)) if value is not None else 0
            except (ValueError, TypeError):
                validated[field] = 0

        # Handle boolean inputs
        for field in ['hourly', 'refresh']:
            validated[field] = bool(kwargs.get(field, False))

        return validated


# Validation decorator for callback functions


def validate_inputs(**validation_rules):
    """
    Decorator to validate callback inputs automatically.

    Args:
        **validation_rules: Dictionary of field names and validation functions

    Example:
        @validate_inputs(symbol=InputValidator.validate_symbol, days=lambda x: InputValidator.validate_positive_integer(x, "Days"))


        def my_callback(symbol, days):
            # Inputs are already validated
            pass
    """


    def decorator(func):


        def wrapper(*args, **kwargs):
            # Extract arguments based on function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each specified field
            for field_name, validator in validation_rules.items():
                if field_name in bound_args.arguments:
                    value = bound_args.arguments[field_name]
                    is_valid, error = validator(value)
                    if not is_valid:
                        # Return error chart or safe default
                        from ..layouts.chart_components import create_error_chart
                        return create_error_chart('validation_error', error)

            # If all validations pass, call the original function
            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper
    return decorator

