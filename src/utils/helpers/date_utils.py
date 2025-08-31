import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger

# Initialize logger
logger = get_ui_logger("utils")

def get_welcome_message(name="Nishant"):
    """
    Generate a personalized welcome message based on the current time.

    Args:
        name (str): User's name for personalization

    Returns:
        str: Personalized welcome message
    """
    current_hour = datetime.now().hour

    if 5 <= current_hour < 12:
        greeting = "Good Morning"
    elif 12 <= current_hour < 17:
        greeting = "Good Afternoon"
    elif 17 <= current_hour < 21:
        greeting = "Good Evening"
    else:
        greeting = "Good Night"

    return f"Welcome {name}, {greeting}"

def format_datetime_display(date_string, format_type="user_friendly"):
    """
    Format datetime string for display purposes.

    Args:
        date_string (str): Date string in format 'YYYY-MM-DD HH:MM:SS'
        format_type (str): Format type - 'user_friendly', 'compact', 'detailed', 'time_only'

    Returns:
        str: Formatted date string
    """
    try:
        # Parse the input date string
        if isinstance(date_string, str):
            dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        elif isinstance(date_string, datetime):
            dt = date_string
        else:
            logger.error(f"Invalid date format: {date_string}")
            return "Invalid Date"

        # Format based on type
        if format_type == "user_friendly":
            # Format: "2nd Aug, 2025 4:14 PM"
            day = dt.day
            suffix = get_day_suffix(day)
            month = dt.strftime('%b')
            year = dt.year
            time = dt.strftime('%I:%M %p')
            return f"{day}{suffix} {month}, {year} {time}"

        elif format_type == "compact":
            # Format: "Aug 2, 2025 4:14 PM"
            return dt.strftime('%b %d, %Y %I:%M %p')

        elif format_type == "detailed":
            # Format: "August 2nd, 2025 at 4:14 PM"
            day = dt.day
            suffix = get_day_suffix(day)
            month = dt.strftime('%B')
            year = dt.year
            time = dt.strftime('%I:%M %p')
            return f"{month} {day}{suffix}, {year} at {time}"

        elif format_type == "time_only":
            # Format: "4:14 PM"
            return dt.strftime('%I:%M %p')

        elif format_type == "date_only":
            # Format: "2nd Aug, 2025"
            day = dt.day
            suffix = get_day_suffix(day)
            month = dt.strftime('%b')
            year = dt.year
            return f"{day}{suffix} {month}, {year}"

        else:
            logger.warning(f"Unknown format type: {format_type}, using user_friendly")
            return format_datetime_display(date_string, "user_friendly")

    except Exception as e:
        logger.error(f"Error formatting date {date_string}: {e}")
        return "Invalid Date"

def get_day_suffix(day):
    """Get the appropriate suffix for a day number."""
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return suffix

def get_current_time_formatted(format_type="user_friendly"):
    """
    Get current time formatted for display.

    Args:
        format_type (str): Format type for the date

    Returns:
        str: Formatted current time
    """
    current_time = datetime.now()
    return format_datetime_display(current_time, format_type)

def format_timestamp_for_logs(timestamp):
    """
    Format timestamp for log display.

    Args:
        timestamp (str): Timestamp string

    Returns:
        str: Formatted timestamp for logs
    """
    return format_datetime_display(timestamp, "detailed")

def format_time_for_charts(timestamp):
    """
    Format time for chart display (more compact).

    Args:
        timestamp (str): Timestamp string

    Returns:
        str: Formatted time for charts
    """
    return format_datetime_display(timestamp, "compact")

def is_recent_time(timestamp, minutes=5):
    """
    Check if a timestamp is recent (within specified minutes).

    Args:
        timestamp (str): Timestamp string
        minutes (int): Number of minutes to consider "recent"

    Returns:
        bool: True if timestamp is recent
    """
    try:
        if isinstance(timestamp, str):
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            return False

        current_time = datetime.now()
        time_diff = current_time - dt

        return time_diff.total_seconds() <= (minutes * 60)

    except Exception as e:
        logger.error(f"Error checking if time is recent: {e}")
        return False
