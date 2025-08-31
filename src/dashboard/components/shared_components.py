"""
Shared UI components for the ML Trading Dashboard.
Consolidates commonly used UI patterns and components.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from ..config import (
    CARD_STYLE,
    CARD_STYLE_NONE,
    CARD_STYLE_HOVER,
    CARD_STYLE_ELEVATED,
    DEFAULT_CHART_HEIGHT,
    CHART_COLORS
)


def create_chart_card(chart_id, height=DEFAULT_CHART_HEIGHT, config=None):
    """
    Create a standardized card container for charts.

    Args:
        chart_id (str): The ID for the chart component
        height (str): Height of the chart (default from config)
        config (dict): Optional Plotly config for the chart

    Returns:
        dbc.Card: Chart card component
    """
    chart_config = config or {'displayModeBar': True, 'displaylogo': False}

    return dbc.Card([
        dbc.CardBody([
            dcc.Graph(
                id=chart_id,
                style={'height': height},
                config=chart_config
            )
        ], className="p-0")
    ], style=CARD_STYLE_NONE)


def create_metric_card(title, value, subtitle=None, color_class="text-primary", card_style=None, value_id=None, enhanced=False):
    """
    Create a standardized metric display card.

    Args:
        title (str): The title/label for the metric
        value (str): The main value to display
        subtitle (str, optional): Additional subtitle text
        color_class (str): CSS class for value color
        card_style (dict, optional): Override card styling
        value_id (str, optional): ID for the value element (for dynamic updates)
        enhanced (bool): Use enhanced styling with hover effects

    Returns:
        dbc.Card: Metric card component
    """
    style = card_style or (CARD_STYLE_HOVER if enhanced else CARD_STYLE)

    card_content = [
        html.H6(title, className="text-muted mb-2 text-uppercase", style={"font-size": "0.75rem", "letter-spacing": "0.05em"})
    ]

    # Create value element with optional ID
    value_style = {"font-weight": "600", "font-size": "1.5rem"}
    if value_id:
        card_content.append(html.H4(value, id=value_id, className=f"{color_class} mb-0", style=value_style))
    else:
        card_content.append(html.H4(value, className=f"{color_class} mb-0", style=value_style))

    if subtitle:
        card_content.append(html.Small(subtitle, className="text-muted mt-1"))

    card_class = "metric-card hover-lift" if enhanced else ""

    return dbc.Card([
        dbc.CardBody(card_content)
    ], style=style, className=card_class)


def create_section_header(title, subtitle=None, icon_class=None, actions=None, style="normal"):
    """
    Create a standardized section header with optional subtitle and actions.

    Args:
        title (str): Main heading text
        subtitle (str, optional): Subtitle text
        icon_class (str, optional): Font Awesome icon class
        actions (list, optional): List of action components (buttons, etc.)
        style (str): Header style - "normal", "gradient", or "section"

    Returns:
        html.Div: Section header component
    """
    header_content = []

    # Title with optional icon and styling
    title_content = []
    if icon_class:
        title_content.append(html.I(className=f"{icon_class} me-2"))
    title_content.append(title)

    # Determine title class based on style
    title_class = "mb-2" if subtitle else "mb-0"
    if style == "gradient":
        title_class += " text-gradient"
    elif style == "section":
        title_class += " chart-title section-header"

    header_content.append(
        html.H5(title_content, className=title_class)
    )

    # Optional subtitle
    if subtitle:
        header_content.append(
            html.P(subtitle, className="text-muted mb-0")
        )

    # Wrap in flex container if actions are provided
    container_class = "mb-3"
    if style == "section":
        container_class += " section-spacing"

    if actions:
        return html.Div([
            html.Div(header_content),
            html.Div(actions, className="d-flex gap-2")
        ], className=f"d-flex justify-content-between align-items-center {container_class}")
    else:
        return html.Div(header_content, className=container_class)


def create_info_card(title, content, icon_class="fas fa-info-circle", card_color="light"):
    """
    Create a standardized information card (used in help, about sections).

    Args:
        title (str): Card title
        content: Card content (can be HTML components or string)
        icon_class (str): Font Awesome icon class
        card_color (str): Bootstrap color variant

    Returns:
        dbc.Card: Information card component
    """
    header_class = f"bg-{card_color}"
    if card_color in ["primary", "success", "danger", "warning", "info"]:
        header_class += " text-white"

    return dbc.Card([
        dbc.CardHeader([
            html.I(className=f"{icon_class} me-2"),
            html.H5(title, className="mb-0")
        ], className=header_class),
        dbc.CardBody(content)
    ], className="mb-4 shadow-sm")


def create_control_group(label, component, width=None):
    """
    Create a standardized form control group with label.

    Args:
        label (str): Label text
        component: The form component (dropdown, input, etc.)
        width (int, optional): Bootstrap column width

    Returns:
        dbc.Col: Control group column
    """
    content = [
        html.Label(label, className="text-primary-emphasis mb-1"),
        component
    ]

    if width:
        return dbc.Col(content, width=width)
    else:
        return html.Div(content, className="mb-2")


def create_button_group(buttons, justify="start", gap="2"):
    """
    Create a standardized button group with consistent spacing.

    Args:
        buttons (list): List of button components
        justify (str): Bootstrap justify-content value
        gap (str): Bootstrap gap value

    Returns:
        html.Div: Button group container
    """
    return html.Div(
        buttons,
        className=f"d-flex justify-content-{justify} gap-{gap}"
    )


def create_loading_card(message="Loading...", height="400px"):
    """
    Create a loading placeholder card.

    Args:
        message (str): Loading message
        height (str): Card height

    Returns:
        dbc.Card: Loading card component
    """
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                dbc.Spinner(color="primary", size="lg"),
                html.P(message, className="text-muted mt-3 mb-0")
            ], className="text-center py-5")
        ])
    ], style={**CARD_STYLE_NONE, "height": height})


def create_empty_state_card(title, message, icon_class="fas fa-chart-line", height="400px"):
    """
    Create an empty state card for when no data is available.

    Args:
        title (str): Empty state title
        message (str): Empty state message
        icon_class (str): Font Awesome icon class
        height (str): Card height

    Returns:
        dbc.Card: Empty state card component
    """
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon_class} fa-3x text-muted mb-3"),
                html.H5(title, className="text-muted mb-2"),
                html.P(message, className="text-muted mb-0")
            ], className="text-center py-5")
        ])
    ], style={**CARD_STYLE_NONE, "height": height})

