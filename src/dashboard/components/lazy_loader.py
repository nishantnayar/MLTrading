"""
Lazy loading components for dashboard optimization.
Implements deferred loading of heavy analysis components.
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from typing import Dict, Any, Callable, Optional
import time

from ..config import CHART_COLORS
from ...utils.logging_config import get_ui_logger

logger = get_ui_logger("lazy_loader")


class LazyComponent:
    """Base class for lazy-loaded components."""

    def __init__(self, component_id: str, loader_func: Callable, loading_text: str = "Loading..."):
        self.component_id = component_id
        self.loader_func = loader_func
        self.loading_text = loading_text
        self.is_loaded = False
        self.cached_content = None

    def create_placeholder(self) -> html.Div:
        """Create placeholder component that triggers lazy loading."""
        return html.Div([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Spinner(
                                html.Div(id=f"{self.component_id}-content"),
                                size="sm",
                                color="primary"
                            )
                        ], width=12)
                    ]),
                    html.Div(
                        id=f"{self.component_id}-trigger",
                        style={'display': 'none'}
                    )
                ])
            ], className="h-100")
        ], id=f"{self.component_id}-container")

    def register_callback(self, app: dash.Dash):
        """Register callback for lazy loading."""
        @app.callback(
            Output(f"{self.component_id}-content", "children"),
            [Input(f"{self.component_id}-trigger", "children")],
            prevent_initial_call=True
        )
        def load_component(trigger):
            """Load component when triggered."""
            if self.cached_content is not None:
                logger.debug(f"Returning cached content for {self.component_id}")
                return self.cached_content

            try:
                start_time = time.time()
                logger.info(f"Lazy loading component: {self.component_id}")

                content = self.loader_func()
                self.cached_content = content
                self.is_loaded = True

                load_time = time.time() - start_time
                logger.info(f"Lazy loaded {self.component_id} in {load_time:.2f}s")

                return content

            except Exception as e:
                logger.error(f"Error lazy loading {self.component_id}: {e}")
                return dbc.Alert([
                    html.H5("Error Loading Component", className="alert-heading"),
                    html.P(f"Failed to load {self.component_id}: {str(e)}")
                ], color="danger")


class LazyAnalyticsComponents:
    """Factory for creating lazy-loaded analytics components."""

    @staticmethod
    def create_performance_analysis() -> LazyComponent:
        """Create lazy-loaded performance analysis component."""
        def load_performance_analysis():
            from ..layouts.analytics_components import create_performance_analysis_layout
            return create_performance_analysis_layout()

        return LazyComponent(
            "performance-analysis",
            load_performance_analysis,
            "Loading performance analysis..."
        )

    @staticmethod
    def create_correlation_matrix() -> LazyComponent:
        """Create lazy-loaded correlation matrix component."""
        def load_correlation_matrix():
            from ..layouts.analytics_components import create_correlation_matrix_layout
            return create_correlation_matrix_layout()

        return LazyComponent(
            "correlation-matrix",
            load_correlation_matrix,
            "Loading correlation analysis..."
        )

    @staticmethod
    def create_volatility_analysis() -> LazyComponent:
        """Create lazy-loaded volatility analysis component."""
        def load_volatility_analysis():
            from ..layouts.analytics_components import create_volatility_analysis_layout
            return create_volatility_analysis_layout()

        return LazyComponent(
            "volatility-analysis",
            load_volatility_analysis,
            "Loading volatility analysis..."
        )

    @staticmethod
    def create_risk_metrics() -> LazyComponent:
        """Create lazy-loaded risk metrics component."""
        def load_risk_metrics():
            from ..layouts.analytics_components import create_risk_metrics_layout
            return create_risk_metrics_layout()

        return LazyComponent(
            "risk-metrics",
            load_risk_metrics,
            "Loading risk metrics..."
        )


class LazyTabContainer:
    """Container for organizing lazy-loaded components in tabs."""

    def __init__(self, container_id: str):
        self.container_id = container_id
        self.tabs = {}
        self.lazy_components = {}

    def add_tab(self, tab_id: str, tab_label: str, lazy_component: LazyComponent):
        """Add a lazy-loaded tab."""
        self.tabs[tab_id] = {
            'label': tab_label,
            'component': lazy_component
        }
        self.lazy_components[tab_id] = lazy_component

    def create_tab_container(self) -> dbc.Tabs:
        """Create tabbed container with lazy-loaded content."""
        tab_items = []

        for tab_id, tab_info in self.tabs.items():
            tab_items.append(
                dbc.Tab(
                    tab_info['component'].create_placeholder(),
                    label=tab_info['label'],
                    tab_id=tab_id
                )
            )

        return dbc.Tabs(
            tab_items,
            id=f"{self.container_id}-tabs",
            active_tab=list(self.tabs.keys())[0] if self.tabs else None
        )

    def register_callbacks(self, app: dash.Dash):
        """Register all lazy loading callbacks."""
        # Register individual component callbacks
        for component in self.lazy_components.values():
            component.register_callback(app)

        # Register tab activation callback
        @app.callback(
            [Output(f"{comp.component_id}-trigger", "children") for comp in self.lazy_components.values()],
            [Input(f"{self.container_id}-tabs", "active_tab")],
            prevent_initial_call=True
        )
        def trigger_tab_load(active_tab):
            """Trigger loading of active tab content."""
            if not active_tab or active_tab not in self.lazy_components:
                return [dash.no_update] * len(self.lazy_components)

            # Only trigger the active tab
            outputs = []
            for tab_id, component in self.lazy_components.items():
                if tab_id == active_tab and not component.is_loaded:
                    outputs.append("trigger_load")
                    logger.info(f"Triggering lazy load for tab: {tab_id}")
                else:
                    outputs.append(dash.no_update)

            return outputs


def create_intersection_observer_script() -> html.Script:
    """Create JavaScript for intersection observer-based lazy loading."""
    js_code = """
    document.addEventListener('DOMContentLoaded', function() {
        // Intersection Observer for lazy loading
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const triggerElement = entry.target.querySelector('[id$="-trigger"]');
                    if (triggerElement && !triggerElement.hasAttribute('data-loaded')) {
                        triggerElement.textContent = 'trigger_load';
                        triggerElement.setAttribute('data-loaded', 'true');
                        observer.unobserve(entry.target);
                    }
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });

        // Observe all lazy components
        document.querySelectorAll('[id$="-container"]').forEach(el => {
            if (el.id.includes('lazy-') || el.id.includes('performance-') ||
                el.id.includes('correlation-') || el.id.includes('volatility-') ||
                el.id.includes('risk-')) {
                observer.observe(el);
            }
        });
    });
    """

    return html.Script(js_code)


def create_optimized_analytics_dashboard() -> html.Div:
    """Create an optimized analytics dashboard with lazy loading."""

    # Create lazy tab container
    analytics_tabs = LazyTabContainer("analytics")

    # Add lazy-loaded analytics components
    analytics_tabs.add_tab(
        "performance",
        "Performance Analysis",
        LazyAnalyticsComponents.create_performance_analysis()
    )

    analytics_tabs.add_tab(
        "correlation",
        "Correlation Matrix",
        LazyAnalyticsComponents.create_correlation_matrix()
    )

    analytics_tabs.add_tab(
        "volatility",
        "Volatility Analysis",
        LazyAnalyticsComponents.create_volatility_analysis()
    )

    analytics_tabs.add_tab(
        "risk",
        "Risk Metrics",
        LazyAnalyticsComponents.create_risk_metrics()
    )

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("Advanced Analytics", className="text-center mb-4"),
                analytics_tabs.create_tab_container()
            ])
        ]),
        create_intersection_observer_script()
    ], id="optimized-analytics-dashboard")


def register_lazy_loading_callbacks(app: dash.Dash, analytics_tabs: LazyTabContainer):
    """Register all lazy loading callbacks."""
    analytics_tabs.register_callbacks(app)
