import dash
from dash import html, dcc, callback_context, Input, Output, State
import dash_bootstrap_components as dbc
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger, log_dashboard_event
from src.dashboard.pages.home import layout as home_layout, register_callbacks as register_home_callbacks
from src.dashboard.pages.logs import create_layout, register_callbacks as register_logs_callbacks
from src.dashboard.pages.settings import layout as settings_layout

# Initialize logger
logger = get_ui_logger("dashboard")

# Debug: Print layout types
print(f"Home layout type: {type(home_layout)}")
print(f"Logs layout type: {type(create_layout())}")
print(f"Settings layout type: {type(settings_layout)}")

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# Add custom JavaScript for theme switching
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
                <script>
            // Theme switching functionality
            function toggleTheme() {
                const body = document.body;
                const currentTheme = body.getAttribute('data-theme');
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                body.setAttribute('data-theme', newTheme);
                
                // Store theme preference in localStorage
                localStorage.setItem('theme', newTheme);
            }
            
            // Sidebar functionality
            function toggleSidebar() {
                const sidebar = document.getElementById('sidebar-container');
                const mainContent = document.getElementById('main-content');
                const toggleIcon = document.getElementById('sidebar-toggle-icon');
                
                if (sidebar.classList.contains('sidebar-collapsed')) {
                    sidebar.classList.remove('sidebar-collapsed');
                    sidebar.classList.add('sidebar-expanded');
                    mainContent.classList.add('expanded');
                    toggleIcon.className = 'fas fa-chevron-left';
                    localStorage.setItem('sidebar', 'expanded');
                } else {
                    sidebar.classList.remove('sidebar-expanded');
                    sidebar.classList.add('sidebar-collapsed');
                    mainContent.classList.remove('expanded');
                    toggleIcon.className = 'fas fa-chevron-right';
                    localStorage.setItem('sidebar', 'collapsed');
                }
            }
            
            // Apply saved theme and sidebar state on page load
            document.addEventListener('DOMContentLoaded', function() {
                // Theme setup
                const savedTheme = localStorage.getItem('theme') || 'light';
                document.body.setAttribute('data-theme', savedTheme);
                
                // Update theme toggle button icon
                const themeToggle = document.getElementById('theme-toggle');
                if (themeToggle) {
                    const icon = themeToggle.querySelector('i');
                    if (icon) {
                        icon.className = savedTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
                    }
                }
                
                // Sidebar setup (default to collapsed)
                const savedSidebar = localStorage.getItem('sidebar') || 'collapsed';
                const sidebar = document.getElementById('sidebar-container');
                const mainContent = document.getElementById('main-content');
                const toggleIcon = document.getElementById('sidebar-toggle-icon');
                
                if (savedSidebar === 'expanded') {
                    sidebar.classList.remove('sidebar-collapsed');
                    sidebar.classList.add('sidebar-expanded');
                    mainContent.classList.add('expanded');
                    toggleIcon.className = 'fas fa-chevron-left';
                } else {
                    sidebar.classList.remove('sidebar-expanded');
                    sidebar.classList.add('sidebar-collapsed');
                    mainContent.classList.remove('expanded');
                    toggleIcon.className = 'fas fa-chevron-right';
                }
            });
            
            // Listen for button clicks
            document.addEventListener('click', function(e) {
                if (e.target.closest('#theme-toggle')) {
                    toggleTheme();
                }
                if (e.target.closest('#sidebar-toggle')) {
                    toggleSidebar();
                }
            });
            
            // Mobile sidebar handling
            function handleMobileSidebar() {
                const sidebar = document.getElementById('sidebar-container');
                const isMobile = window.innerWidth <= 768;
                
                if (isMobile) {
                    sidebar.classList.add('mobile-open');
                } else {
                    sidebar.classList.remove('mobile-open');
                }
            }
            
            // Handle window resize
            window.addEventListener('resize', handleMobileSidebar);
            
            // Initial mobile check
            document.addEventListener('DOMContentLoaded', function() {
                handleMobileSidebar();
            });
        </script>
    </body>
</html>
'''



# Define the main layout with navigation
app.layout = html.Div([
    # Theme Toggle Button
    html.Div([
        html.Button([
            html.I(className="fas fa-sun", id="theme-icon")
        ], id="theme-toggle", className="theme-toggle", n_clicks=0)
    ]),
    
    # Collapsible Sidebar
    html.Div([
        # Sidebar Toggle Button
        html.Button([
            html.I(className="fas fa-chevron-right", id="sidebar-toggle-icon")
        ], id="sidebar-toggle", className="sidebar-toggle", n_clicks=0),
        
        # Sidebar Content
        html.Div([
            html.Ul([
                html.Li([
                    html.A([
                        html.I(className="fas fa-chart-line sidebar-nav-icon"),
                        html.Span("Dashboard", className="sidebar-nav-text")
                    ], href="#", id="nav-dashboard", className="sidebar-nav-link active", **{"data-tooltip": "Dashboard"})
                ], className="sidebar-nav-item"),
                html.Li([
                    html.A([
                        html.I(className="fas fa-file-alt sidebar-nav-icon"),
                        html.Span("Logs", className="sidebar-nav-text")
                    ], href="#", id="nav-logs", className="sidebar-nav-link", **{"data-tooltip": "Logs"})
                ], className="sidebar-nav-item"),
                html.Li([
                    html.A([
                        html.I(className="fas fa-cog sidebar-nav-icon"),
                        html.Span("Settings", className="sidebar-nav-text")
                    ], href="#", id="nav-settings", className="sidebar-nav-link", **{"data-tooltip": "Settings"})
                ], className="sidebar-nav-item")
            ], className="sidebar-nav")
        ], className="sidebar-content")
    ], id="sidebar-container", className="sidebar-container sidebar-collapsed"),
    
    # Main Content Area
    html.Div([
        # Header
        html.Div([
            html.H1("ML Trading Dashboard", className="text-center mb-2"),
            html.Div([
                html.Span("●", className="status-indicator status-online"),
                html.Span("System Online", className="ms-2")
            ], className="text-center text-muted")
        ], className="dashboard-header"),
        
        # Page Content
        html.Div(id="page-content")
        
    ], id="main-content", className="main-content")
])

# Callback to update page content
@app.callback(
    Output("page-content", "children"),
    [Input("nav-dashboard", "n_clicks"),
     Input("nav-logs", "n_clicks"),
     Input("nav-settings", "n_clicks")]
)
def update_page_content(dashboard_clicks, logs_clicks, settings_clicks):
    try:
        ctx = callback_context
        if not ctx.triggered:
            return home_layout
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if button_id == "nav-dashboard":
            return home_layout
        elif button_id == "nav-logs":
            return create_layout()
        elif button_id == "nav-settings":
            return settings_layout
        else:
            return home_layout
    except Exception as e:
        logger.error(f"Page content callback error: {e}")
        return home_layout

# Callback to update navigation active states
@app.callback(
    [Output("nav-dashboard", "className"),
     Output("nav-logs", "className"),
     Output("nav-settings", "className")],
    [Input("nav-dashboard", "n_clicks"),
     Input("nav-logs", "n_clicks"),
     Input("nav-settings", "n_clicks")]
)
def update_nav_active_states(dashboard_clicks, logs_clicks, settings_clicks):
    try:
        ctx = callback_context
        if not ctx.triggered:
            return "sidebar-nav-link active", "sidebar-nav-link", "sidebar-nav-link"
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if button_id == "nav-dashboard":
            return "sidebar-nav-link active", "sidebar-nav-link", "sidebar-nav-link"
        elif button_id == "nav-logs":
            return "sidebar-nav-link", "sidebar-nav-link active", "sidebar-nav-link"
        elif button_id == "nav-settings":
            return "sidebar-nav-link", "sidebar-nav-link", "sidebar-nav-link active"
        else:
            return "sidebar-nav-link active", "sidebar-nav-link", "sidebar-nav-link"
    except Exception as e:
        logger.error(f"Navigation active states callback error: {e}")
        return "sidebar-nav-link active", "sidebar-nav-link", "sidebar-nav-link"

# Configure app to suppress callback exceptions
app.config.suppress_callback_exceptions = True

# Sidebar toggle callback
@app.callback(
    [Output("sidebar-container", "className"),
     Output("main-content", "className"),
     Output("sidebar-toggle-icon", "className")],
    [Input("sidebar-toggle", "n_clicks")],
    prevent_initial_call=True
)
def toggle_sidebar(n_clicks):
    try:
        if n_clicks is None:
            n_clicks = 0
        
        # Toggle between collapsed and expanded
        if n_clicks % 2 == 0:
            # Collapsed (default)
            return "sidebar-container sidebar-collapsed", "main-content", "fas fa-chevron-right"
        else:
            # Expanded
            return "sidebar-container sidebar-expanded", "main-content expanded", "fas fa-chevron-left"
    except Exception as e:
        logger.error(f"Sidebar toggle callback error: {e}")
        return "sidebar-container sidebar-collapsed", "main-content", "fas fa-chevron-right"

# Theme toggle callback - simplified to avoid conflicts
@app.callback(
    Output("theme-icon", "className"),
    [Input("theme-toggle", "n_clicks")],
    prevent_initial_call=True
)
def toggle_theme(n_clicks):
    try:
        if n_clicks is None:
            n_clicks = 0
        
        # Toggle between light and dark themes
        if n_clicks % 2 == 0:
            # Light theme (default)
            return "fas fa-sun"
        else:
            # Dark theme
            return "fas fa-moon"
    except Exception as e:
        logger.error(f"Theme toggle callback error: {e}")
        return "fas fa-sun"  # Default to light theme

# Register page-specific callbacks
register_home_callbacks(app)
register_logs_callbacks(app)

if __name__ == '__main__':
    logger.info("Starting Dash dashboard on 0.0.0.0:8050")
    app.run(debug=True, host='0.0.0.0', port=8050)
