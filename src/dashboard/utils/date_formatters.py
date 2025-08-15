"""
Date formatting utilities for consistent user-friendly date displays.
Provides standardized formatting functions for the ML Trading Dashboard.
"""

from datetime import datetime, timedelta
import pytz
from typing import Optional, Union
import pandas as pd


def format_timestamp(
    timestamp: Union[datetime, pd.Timestamp, str], 
    format_type: str = "default",
    timezone: str = "US/Central"
) -> str:
    """
    Format timestamp into user-friendly string.
    
    Args:
        timestamp: The timestamp to format
        format_type: Type of format to apply
            - "default": "Jan 15, 2025 2:30 PM"
            - "short": "Jan 15, 2:30 PM"
            - "date_only": "January 15, 2025"
            - "time_only": "2:30 PM CST"
            - "relative": "2 hours ago"
            - "iso": "2025-01-15T14:30:00"
            - "market": "Jan 15 14:30" (for market hours)
        timezone: Target timezone for display
    
    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return "N/A"
    
    # Convert to datetime if needed
    if isinstance(timestamp, str):
        try:
            if 'T' in timestamp:
                dt = pd.to_datetime(timestamp)
            else:
                dt = pd.to_datetime(timestamp)
        except:
            return "Invalid Date"
    elif isinstance(timestamp, pd.Timestamp):
        dt = timestamp.to_pydatetime()
    else:
        dt = timestamp
    
    # Convert to target timezone - but avoid timezone conversion for formatting
    # This prevents incorrect year shifts due to timezone issues
    try:
        if timezone and dt.tzinfo is None:
            # Only add timezone info if explicitly needed
            # For display purposes, use the data as-is without conversion
            pass
    except Exception as e:
        # Log any timezone issues but continue with original datetime
        print(f"Timezone conversion warning: {e}")
        pass
    
    # Apply formatting based on type
    if format_type == "default":
        return dt.strftime("%b %d, %Y %I:%M %p")
    elif format_type == "short":
        return dt.strftime("%b %d, %I:%M %p")
    elif format_type == "date_only":
        return dt.strftime("%B %d, %Y")
    elif format_type == "time_only":
        tz_abbr = dt.strftime("%Z") or "CST"
        return f"{dt.strftime('%I:%M %p')} {tz_abbr}"
    elif format_type == "relative":
        return format_relative_time(dt)
    elif format_type == "iso":
        return dt.isoformat()
    elif format_type == "market":
        return dt.strftime("%b %d %H:%M")
    else:
        return dt.strftime("%b %d, %Y %I:%M %p")


def format_relative_time(dt: datetime) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago", "in 30 minutes").
    
    Args:
        dt: The datetime to format
    
    Returns:
        Relative time string
    """
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt
    
    # Future times
    if diff.total_seconds() < 0:
        diff = abs(diff)
        suffix = "from now"
    else:
        suffix = "ago"
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} second{'s' if seconds != 1 else ''} {suffix}"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} {suffix}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} {suffix}"
    elif seconds < 2592000:  # 30 days
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} {suffix}"
    elif seconds < 31536000:  # 365 days
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} {suffix}"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} {suffix}"


def format_date_range(
    start_date: Union[datetime, pd.Timestamp, str],
    end_date: Union[datetime, pd.Timestamp, str],
    format_type: str = "default"
) -> str:
    """
    Format a date range into user-friendly string.
    
    Args:
        start_date: Range start date
        end_date: Range end date
        format_type: Format type ("default", "short", "compact")
    
    Returns:
        Formatted date range string
    """
    if not start_date or not end_date:
        return "N/A"
    
    start_str = format_timestamp(start_date, "date_only")
    end_str = format_timestamp(end_date, "date_only")
    
    if format_type == "short":
        start_str = format_timestamp(start_date, "short").split(',')[0]  # Just "Jan 15"
        end_str = format_timestamp(end_date, "short").split(',')[0]
    elif format_type == "compact":
        # Convert to datetime for comparison
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        if start_dt.year == end_dt.year:
            if start_dt.month == end_dt.month:
                start_str = start_dt.strftime("%b %d")
                end_str = end_dt.strftime("%d, %Y")
            else:
                start_str = start_dt.strftime("%b %d")
                end_str = end_dt.strftime("%b %d, %Y")
        else:
            start_str = start_dt.strftime("%b %d, %Y")
            end_str = end_dt.strftime("%b %d, %Y")
    
    return f"{start_str} - {end_str}"


def format_duration(
    start_time: Union[datetime, pd.Timestamp, str],
    end_time: Union[datetime, pd.Timestamp, str] = None
) -> str:
    """
    Format duration between two times or from start_time to now.
    
    Args:
        start_time: Start time
        end_time: End time (defaults to now)
    
    Returns:
        Formatted duration string
    """
    if not start_time:
        return "N/A"
    
    start_dt = pd.to_datetime(start_time)
    end_dt = pd.to_datetime(end_time) if end_time else datetime.now()
    
    diff = end_dt - start_dt
    total_seconds = abs(diff.total_seconds())
    
    if total_seconds < 60:
        return f"{int(total_seconds)}s"
    elif total_seconds < 3600:
        return f"{int(total_seconds / 60)}m"
    elif total_seconds < 86400:
        hours = int(total_seconds / 3600)
        minutes = int((total_seconds % 3600) / 60)
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    else:
        days = int(total_seconds / 86400)
        hours = int((total_seconds % 86400) / 3600)
        return f"{days}d {hours}h" if hours > 0 else f"{days}d"


def format_market_time(dt: datetime, market_tz: str = "US/Eastern") -> str:
    """
    Format time specifically for market context.
    
    Args:
        dt: Datetime to format
        market_tz: Market timezone
    
    Returns:
        Market-formatted time string
    """
    try:
        market_time = dt.astimezone(pytz.timezone(market_tz))
        return f"{market_time.strftime('%I:%M %p')} ET"
    except:
        return dt.strftime('%I:%M %p')


def get_current_timestamp(format_type: str = "default", timezone: str = "US/Central") -> str:
    """
    Get current timestamp in specified format.
    
    Args:
        format_type: Format type for timestamp
        timezone: Target timezone
    
    Returns:
        Formatted current timestamp
    """
    now = datetime.now(pytz.timezone(timezone))
    return format_timestamp(now, format_type, timezone)


def parse_sql_timestamp(sql_result: tuple) -> dict:
    """
    Parse SQL result with min/max timestamps into user-friendly format.
    Expected format: (min_timestamp, max_timestamp, count)
    
    Args:
        sql_result: Tuple from SQL query (min_ts, max_ts, count)
    
    Returns:
        Dictionary with formatted date information
    """
    if not sql_result or len(sql_result) < 3:
        return {
            "start_date": "N/A",
            "end_date": "N/A", 
            "range": "No data available",
            "count": 0,
            "duration": "N/A"
        }
    
    min_ts, max_ts, count = sql_result
    
    return {
        "start_date": format_timestamp(min_ts, "date_only"),
        "end_date": format_timestamp(max_ts, "date_only"),
        "range": format_date_range(min_ts, max_ts, "compact"),
        "count": f"{count:,}",
        "duration": format_duration(min_ts, max_ts)
    }


# Predefined format configurations for common use cases
FORMAT_CONFIGS = {
    "dashboard_header": {"format_type": "default", "timezone": "US/Central"},
    "footer_timestamp": {"format_type": "default", "timezone": "US/Central"},
    "chart_tooltip": {"format_type": "short", "timezone": "US/Eastern"},
    "data_range": {"format_type": "compact"},
    "market_hours": {"format_type": "time_only", "timezone": "US/Eastern"},
    "last_updated": {"format_type": "relative"},
}