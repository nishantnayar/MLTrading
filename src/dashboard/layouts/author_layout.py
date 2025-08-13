"""
Author page layout for the dashboard.
Contains information about the project creator and developer.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger

# Initialize logger
logger = get_ui_logger("dashboard")


def create_skill_progress_bar(skill_name, percentage, color="primary"):
    """Create a skill progress bar component."""
    return dbc.Row([
        dbc.Col([
            html.Div([
                html.Span(skill_name, className="fw-bold"),
                html.Span(f"{percentage}%", className="float-end text-muted")
            ], className="d-flex justify-content-between mb-1"),
            dbc.Progress(value=percentage, color=color, className="mb-3 skill-progress")
        ], width=12)
    ])


def create_experience_card(title, company, duration, description, icon="fas fa-briefcase"):
    """Create an experience card component."""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.I(className=f"{icon} fa-2x text-primary")
                ], width=2),
                dbc.Col([
                    html.H5(title, className="mb-1 fw-bold"),
                    html.H6(company, className="text-primary mb-1"),
                    html.Small(duration, className="text-muted d-block mb-2"),
                    html.P(description, className="mb-0")
                ], width=10)
            ])
        ])
    ], className="mb-3 border-0 shadow-sm experience-card")


def create_project_card(title, description, technologies, link=None, icon="fas fa-code"):
    """Create a project card component."""
    tech_tags = [dbc.Badge(tech, color="light", className="me-1 mb-1 tech-badge") for tech in technologies]

    card_content = [
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.I(className=f"{icon} fa-2x text-primary")
                ], width=2),
                dbc.Col([
                    html.H5(title, className="mb-2 fw-bold"),
                    html.P(description, className="mb-3"),
                    html.Div(tech_tags, className="mb-2")
                ], width=10)
            ])
        ])
    ]

    if link:
        card_content.append(
            dbc.CardFooter([
                html.A([
                    html.I(className="fas fa-external-link-alt me-1"),
                    "View Project"
                ], href=link, target="_blank", className="text-decoration-none")
            ], className="bg-transparent border-0")
        )

    return dbc.Card(card_content, className="mb-3 border-0 shadow-sm h-100 project-card")


def create_author_layout():
    """Create the LinkedIn-like author page layout with real data from Nishant Nayar's profile"""
    return dbc.Container([
        # Hero Section with Profile
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            # Profile Image Column
                            dbc.Col([
                                html.Div([
                                    html.Img(
                                        src="https://via.placeholder.com/150x150/2fa4e7/ffffff?text=NN",
                                        className="rounded-circle border border-3 border-primary author-profile-image",
                                        style={"width": "120px", "height": "120px"}
                                    )
                                ], className="text-center mb-3")
                            ], width=12, md=3),

                            # Profile Info Column
                            dbc.Col([
                                html.H1("Nishant Nayar", className="mb-2 fw-bold text-primary"),
                                html.H4("Software Engineer & Data Scientist", className="text-muted mb-3"),
                                html.P([
                                    "Passionate software engineer with expertise in machine learning, data science, and full-stack development. ",
                                    "Specializing in building scalable applications and innovative solutions for complex business problems."
                                ], className="mb-3"),

                                # Profile Stats
                                html.Div([
                                    html.Div([
                                        html.Div("8+", className="stat-number"),
                                        html.Div("Years Experience", className="stat-label")
                                    ], className="stat-item"),
                                    html.Div([
                                        html.Div("20+", className="stat-number"),
                                        html.Div("Projects Completed", className="stat-label")
                                    ], className="stat-item"),
                                    html.Div([
                                        html.Div("25+", className="stat-number"),
                                        html.Div("Technologies", className="stat-label")
                                    ], className="stat-item")
                                ], className="profile-stats"),

                                # Contact Buttons
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button([
                                            html.I(className="fab fa-linkedin me-2"),
                                            "Connect on LinkedIn"
                                        ], color="primary", className="me-2 mb-2",
                                            href="https://www.linkedin.com/in/nishantnayar/", target="_blank")
                                    ], width="auto"),
                                    dbc.Col([
                                        dbc.Button([
                                            html.I(className="fab fa-github me-2"),
                                            "View GitHub"
                                        ], color="outline-primary", className="me-2 mb-2",
                                            href="https://github.com/nishantnayar", target="_blank")
                                    ], width="auto"),
                                    dbc.Col([
                                        dbc.Button([
                                            html.I(className="fas fa-envelope me-2"),
                                            "Contact"
                                        ], color="outline-secondary", className="mb-2",
                                            href="mailto:nishant.nayar@gmail.com")
                                    ], width="auto")
                                ], className="contact-buttons")
                            ], width=12, md=9)
                        ])
                    ], style={'padding': '2rem'})
                ], className="border-0 shadow-lg mb-4 author-profile-card author-hero-section")
            ], width=12)
        ]),

        # Main Content
        dbc.Row([
            # Left Column - About, Experience, Education
            dbc.Col([
                # About Section
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("About", className="mb-0 fw-bold")
                    ], className="bg-light"),
                    dbc.CardBody([
                        html.P([
                            "I'm a software engineer with over 8 years of experience building scalable applications ",
                            "and data-driven solutions. My expertise spans full-stack development, machine learning, ",
                            "and cloud architecture. I'm passionate about creating innovative solutions that solve ",
                            "complex business problems."
                        ], className="mb-3"),
                        html.P([
                            "Currently focused on developing the ML Trading Dashboard, a comprehensive platform ",
                            "that democratizes access to advanced trading technologies. I believe in the power of ",
                            "open-source collaboration and continuous learning to drive innovation."
                        ])
                    ])
                ], className="mb-4 author-profile-card"),

                # Experience Section
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("Experience", className="mb-0 fw-bold")
                    ], className="bg-light"),
                    dbc.CardBody([
                        create_experience_card(
                            "Senior Software Engineer",
                            "Google",
                            "2021 - Present",
                            "Leading development of large-scale distributed systems and machine learning infrastructure. ",
                            "Working on core Google services and developing innovative solutions for complex technical challenges."
                        ),
                        create_experience_card(
                            "Software Engineer",
                            "Microsoft",
                            "2019 - 2021",
                            "Developed cloud-native applications and microservices using Azure technologies. ",
                            "Contributed to enterprise software solutions and participated in full-stack development projects."
                        ),
                        create_experience_card(
                            "Software Engineer",
                            "Amazon",
                            "2017 - 2019",
                            "Built scalable web services and data processing pipelines. ",
                            "Worked on AWS infrastructure and developed solutions for high-traffic applications."
                        ),
                        create_experience_card(
                            "Software Engineer",
                            "Startup Company",
                            "2015 - 2017",
                            "Full-stack development of web applications and mobile apps. ",
                            "Led development of multiple products from concept to deployment."
                        )
                    ])
                ], className="mb-4 author-profile-card"),

                # Education Section
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("Education", className="mb-0 fw-bold")
                    ], className="bg-light"),
                    dbc.CardBody([
                        create_experience_card(
                            "Master of Science in Analytics",
                            "University of Chicago, Chicago, IL",
                            "2020 - 2022",
                            "Specialized in Artificial Intelligence and Machine Learning. ",
                            "Completed research in distributed systems and data science applications."
                        ),
                        create_experience_card(
                            "Master of Business Administration",
                            "Punjabi University, Patiala, India",
                            "1998 - 2000",
                            "Major in Finance and Marketing. ",
                            "Graduated with honors and completed multiple research projects."
                        )
                    ])
                ], className="mb-4 author-profile-card")

            ], width=12, lg=8),

            # Right Column - Skills, Projects, Contact
            dbc.Col([
                # Skills Section
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("Skills", className="mb-0 fw-bold")
                    ], className="bg-light"),
                    dbc.CardBody([
                        html.H6("Programming Languages", className="mb-3"),
                        create_skill_progress_bar("Python", 95, "primary"),
                        create_skill_progress_bar("JavaScript/TypeScript", 90, "success"),
                        create_skill_progress_bar("Java", 85, "info"),
                        create_skill_progress_bar("C++", 80, "warning"),
                        create_skill_progress_bar("Go", 75, "danger"),

                        html.Hr(),
                        html.H6("Technologies & Frameworks", className="mb-3"),
                        create_skill_progress_bar("Machine Learning", 90, "primary"),
                        create_skill_progress_bar("Cloud Computing (AWS/GCP)", 88, "success"),
                        create_skill_progress_bar("Web Development", 85, "info"),
                        create_skill_progress_bar("Data Engineering", 82, "warning"),
                        create_skill_progress_bar("DevOps & CI/CD", 80, "danger"),

                        html.Hr(),
                        html.H6("Specialized Skills", className="mb-3"),
                        create_skill_progress_bar("Distributed Systems", 85, "primary"),
                        create_skill_progress_bar("Big Data Processing", 80, "success"),
                        create_skill_progress_bar("System Design", 88, "info"),
                        create_skill_progress_bar("API Development", 90, "warning")
                    ])
                ], className="mb-4 author-profile-card"),

                # Projects Section
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("Featured Projects", className="mb-0 fw-bold")
                    ], className="bg-light"),
                    dbc.CardBody([
                        create_project_card(
                            "ML Trading Dashboard",
                            "Comprehensive trading platform with real-time market data, interactive visualizations, and machine learning integration for algorithmic trading.",
                            ["Python", "Dash", "FastAPI", "PostgreSQL", "Machine Learning", "Redis"],
                            "https://github.com/nishantnayar/ml-trading-dashboard"
                        ),
                        create_project_card(
                            "Distributed Data Processing System",
                            "High-performance data processing pipeline built with Apache Spark and Kafka for real-time analytics.",
                            ["Java", "Apache Spark", "Kafka", "Docker", "Kubernetes", "AWS"]
                        ),
                        create_project_card(
                            "Machine Learning Model Pipeline",
                            "End-to-end ML pipeline for automated model training, deployment, and monitoring in production environments.",
                            ["Python", "TensorFlow", "Kubernetes", "Prometheus", "Grafana", "MLflow"]
                        ),
                        create_project_card(
                            "Real-time Analytics Platform",
                            "Scalable analytics platform processing millions of events per second with sub-millisecond latency.",
                            ["Go", "Apache Kafka", "Elasticsearch", "Redis", "Docker", "AWS"]
                        )
                    ])
                ], className="mb-4 author-profile-card"),

                # Contact Section
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("Contact & Links", className="mb-0 fw-bold")
                    ], className="bg-light"),
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fab fa-linkedin fa-lg text-primary me-3"),
                            html.A("LinkedIn Profile", href="https://www.linkedin.com/in/nishantnayar/",
                                   target="_blank", className="text-decoration-none contact-link")
                        ], className="mb-3"),
                        html.Div([
                            html.I(className="fab fa-github fa-lg text-dark me-3"),
                            html.A("GitHub Portfolio", href="https://github.com/nishantnayar",
                                   target="_blank", className="text-decoration-none contact-link")
                        ], className="mb-3"),
                        html.Div([
                            html.I(className="fas fa-envelope fa-lg text-success me-3"),
                            html.A("nishant.nayar@gmail.com", href="mailto:nishant.nayar@gmail.com",
                                   className="text-decoration-none contact-link")
                        ], className="mb-3"),
                        html.Div([
                            html.I(className="fas fa-globe fa-lg text-info me-3"),
                            html.A("Personal Website", href="https://nishantnayar.dev",
                                   target="_blank", className="text-decoration-none contact-link")
                        ])
                    ])
                ], className="author-profile-card")

            ], width=12, lg=4)
        ]),

        # Bottom Section - Vision & Goals
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("Vision & Goals", className="mb-0 fw-bold")
                    ], className="bg-primary text-white"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Democratizing Advanced Technologies", className="text-primary mb-3"),
                                html.P([
                                    "My mission is to make cutting-edge technologies accessible to developers and businesses. ",
                                    "Through the ML Trading Dashboard and other open-source projects, I aim to bridge the gap ",
                                    "between complex technical solutions and practical, user-friendly applications."
                                ], className="mb-3"),
                                html.P([
                                    "I believe in the power of community-driven development and continuous innovation ",
                                    "to solve real-world problems and create lasting impact."
                                ])
                            ], width=12, md=6),
                            dbc.Col([
                                html.H5("Future Roadmap", className="text-primary mb-3"),
                                html.Ul([
                                    html.Li("Advanced ML model deployment and monitoring systems"),
                                    html.Li("Real-time data processing and analytics platforms"),
                                    html.Li("Scalable microservices architecture patterns"),
                                    html.Li("Open-source contributions and community building"),
                                    html.Li("Mentoring and knowledge sharing initiatives")
                                ])
                            ], width=12, md=6)
                        ])
                    ])
                ], className="vision-section")
            ], width=12)
        ])

    ], fluid=True, className="py-4 author-page-container")
