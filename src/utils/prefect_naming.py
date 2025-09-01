"""
Prefect Flow Run Naming Utilities
Provides consistent and user-friendly naming for Prefect flow runs
"""

from datetime import datetime
from typing import Optional
import pytz


def generate_friendly_flow_name(
        flow_type: str,
        context: Optional[str] = None,
        timezone: str = "America/New_York"
) -> str:
    """
    Generate a user-friendly flow run name

    Args:
        flow_type: Type of flow (e.g., 'yahoo-data', 'portfolio-analysis')
        context: Additional context (e.g., 'manual', 'scheduled', 'retry')
        timezone: Timezone for timestamp

    Returns:
        Formatted flow run name
    """
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)

    # Format timestamp
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")

    # Build name components
    name_parts = [flow_type, date_str, f"{time_str}EST"]

    if context:
        name_parts.append(context)

    return "-".join(name_parts)


def generate_market_context_name(
        flow_type: str = "yahoo-data",
        timezone: str = "America/New_York"
) -> str:
    """
    Generate a flow name with market context

    Args:
        flow_type: Base flow type name
        timezone: Market timezone

    Returns:
        Flow name with market status context
    """
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    current_time = now.time()

    # Market hours (9:30 AM - 4:00 PM EST)
    from datetime import time
    MARKET_OPEN = time(9, 30)
    MARKET_CLOSE = time(16, 0)

    is_weekday = now.weekday() < 5
    is_market_hours = MARKET_OPEN <= current_time <= MARKET_CLOSE
    market_open = is_weekday and is_market_hours

    # Determine context
    if market_open:
        context = "market-open"
    elif is_weekday:
        if current_time < MARKET_OPEN:
            context = "pre-market"
        else:
            context = "after-market"
    else:
        context = "weekend"

    return generate_friendly_flow_name(flow_type, context, timezone)


def generate_manual_trigger_name(
        flow_type: str,
        user_context: Optional[str] = None,
        timezone: str = "America/New_York"
) -> str:
    """
    Generate a name for manually triggered flows

    Args:
        flow_type: Base flow type
        user_context: User-provided context (e.g., 'testing', 'backfill')
        timezone: Timezone for timestamp

    Returns:
        Manual trigger flow name
    """
    context_parts = ["manual"]
    if user_context:
        # Clean user context (replace spaces with hyphens, lowercase)
        clean_context = user_context.lower().replace(" ", "-").replace("_", "-")
        # Remove special characters except hyphens
        clean_context = "".join(c for c in clean_context if c.isalnum() or c == "-")
        context_parts.append(clean_context)

    context = "-".join(context_parts)
    return generate_friendly_flow_name(flow_type, context, timezone)


# Predefined naming functions for common flows


def yahoo_market_hours_name() -> str:
    """Generate name for Yahoo market hours collection"""
    return generate_market_context_name("yahoo-data")


def yahoo_ondemand_name() -> str:
    """Generate name for Yahoo on-demand collection"""
    return generate_friendly_flow_name("yahoo-ondemand", "manual")


def portfolio_analysis_name() -> str:
    """Generate name for portfolio analysis"""
    return generate_friendly_flow_name("portfolio-analysis", "daily")


# Example usage and testing
if __name__ == "__main__":
    print("=== Prefect Flow Naming Examples ===")
    print(f"Yahoo market hours: {yahoo_market_hours_name()}")
    print(f"Yahoo on-demand: {yahoo_ondemand_name()}")
    print(f"Portfolio analysis: {portfolio_analysis_name()}")
    print()
    print("=== Manual Trigger Examples ===")
    print(f"Testing run: {generate_manual_trigger_name('yahoo-data', 'testing')}")
    print(f"Backfill run: {generate_manual_trigger_name('yahoo-data', 'backfill 2025-01')}")
    print(f"User research: {generate_manual_trigger_name('portfolio-analysis', 'user research')}")
