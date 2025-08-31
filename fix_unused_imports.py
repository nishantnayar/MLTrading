#!/usr/bin/env python3
"""
Targeted script to remove unused imports based on flake8 F401 errors.
"""

import os
import re
from pathlib import Path


def remove_specific_unused_imports():
    """Remove specific unused imports that were identified by flake8."""
    
    # Specific unused import removals based on flake8 output
    removals = [
        # Dashboard callbacks
        ("src/dashboard/callbacks/chart_callbacks.py", [
            "import plotly.graph_objs as go",
            "from dash import Input, Output, State, callback_context",
            "from ..config import CHART_COLORS, TIME_RANGE_DAYS",
            "from ..layouts.chart_components import create_empty_chart, create_error_chart",
            "from ..utils.validators import InputValidator"
        ]),
        ("src/dashboard/callbacks/comparison_callbacks.py", [
            "from plotly.subplots import make_subplots",
            "import pandas as pd",
            "from datetime import datetime, timedelta"
        ]),
        ("src/dashboard/callbacks/detailed_analysis_callbacks.py", [
            "import plotly.express as px",
            "import pandas as pd"
        ]),
        ("src/dashboard/callbacks/interactive_chart_callbacks.py", [
            "import plotly.graph_objs as go",
            "import pandas as pd",
            "from typing import List, Dict, Any, Optional",
            "from datetime import datetime, timedelta",
            "from ..utils.date_formatters import format_timestamp"
        ]),
        ("src/dashboard/callbacks/overview_callbacks.py", [
            "import dash",
            "from dash import dcc, State"
        ]),
        ("src/dashboard/callbacks/trading_callbacks.py", [
            "import dash_bootstrap_components as dbc",
            "from datetime import datetime",
            "import json"
        ]),
        
        # Dashboard components
        ("src/dashboard/components/lazy_loader.py", [
            "from dash import dcc, State",
            "from typing import Dict, Any, Optional",
            "from ..config import CHART_COLORS"
        ]),
        ("src/dashboard/components/pipeline_status.py", [
            "from datetime import timedelta",
            "from typing import Optional, Any"
        ]),
        ("src/dashboard/components/shared_components.py", [
            "from ..config import CARD_STYLE_ELEVATED, CHART_COLORS"
        ]),
        
        # Dashboard layouts
        ("src/dashboard/layouts/analytics_components.py", [
            "import plotly.express as px",
            "from ..services.batch_data_service import BatchDataService"
        ]),
        ("src/dashboard/layouts/chart_components.py", [
            "import plotly.express as px",
            "from dash import dcc"
        ]),
        ("src/dashboard/layouts/dashboard_layout.py", [
            "from ..config import DEFAULT_CHART_HEIGHT, DEFAULT_TIME_RANGE, DEFAULT_SYMBOL, TIME_RANGE_OPTIONS",
            "from ..components.shared_components import create_chart_card, create_control_group, create_button_group",
            "from ..components.pipeline_status import create_pipeline_status_card, create_data_freshness_indicator, create_system_health_summary"
        ]),
        ("src/dashboard/layouts/help_layout.py", [
            "import dash",
            "from dash import dcc"
        ]),
        ("src/dashboard/layouts/interactive_chart.py", [
            "from dash import Input, Output, State, callback_context",
            "from typing import Any, Optional",
            "from ..config import CHART_COLORS"
        ]),
        ("src/dashboard/layouts/logs_layout.py", [
            "from dash import callback_context",
            "import json"
        ]),
        ("src/dashboard/layouts/tests_layout.py", [
            "import json",
            "import os"
        ]),
        ("src/dashboard/layouts/trading_layout.py", [
            "import plotly.graph_objs as go",
            "from ..config import CHART_COLORS"
        ]),
        
        # Dashboard services
        ("src/dashboard/services/analytics_service.py", [
            "from typing import Optional"
        ]),
        ("src/dashboard/services/base_service.py", [
            "from typing import Optional"
        ]),
        ("src/dashboard/services/batch_data_service.py", [
            "from typing import Optional, Set"
        ]),
        ("src/dashboard/services/feature_data_service.py", [
            "import numpy as np",
            "from typing import List, Optional, Tuple",
            "from datetime import datetime, timedelta"
        ]),
        ("src/dashboard/services/technical_indicators.py", [
            "from typing import Optional, Tuple"
        ]),
        ("src/dashboard/services/unified_data_service.py", [
            "from datetime import timedelta"
        ]),
        
        # Dashboard utils
        ("src/dashboard/utils/date_formatters.py", [
            "from datetime import timedelta",
            "from typing import Optional"
        ]),
        ("src/dashboard/utils/log_viewer.py", [
            "import dash",
            "from dash import Input, Output, State",
            "import pandas as pd",
            "import json",
            "import logging"
        ]),
        ("src/dashboard/utils/validators.py", [
            "from typing import List, Optional, Union"
        ])
    ]
    
    for file_path, imports_to_remove in removals:
        if os.path.exists(file_path):
            print(f"Processing {file_path}...")
            remove_imports_from_file(file_path, imports_to_remove)


def remove_imports_from_file(file_path, imports_to_remove):
    """Remove specific imports from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            should_remove = False
            
            # Check if this line matches any import to remove
            for import_to_remove in imports_to_remove:
                if line.strip() == import_to_remove:
                    should_remove = True
                    print(f"  - Removing: {import_to_remove}")
                    break
                # Also check for partial matches in multi-line imports
                elif import_to_remove.startswith("from ") and line.strip().startswith("from "):
                    # Handle cases like "from ..config import A, B" where we want to remove specific imports
                    if "import" in import_to_remove and "import" in line:
                        # Extract the import part
                        import_part = import_to_remove.split("import ", 1)[1]
                        if import_part in line:
                            # Remove the specific import from the line
                            new_line = remove_specific_import_from_line(line, import_part)
                            if new_line != line:
                                print(f"  - Modified: {line.strip()} -> {new_line.strip()}")
                                new_lines.append(new_line + '\n')
                                should_remove = True
                                break
            
            if not should_remove:
                new_lines.append(lines[i])
            i += 1
        
        # Write back the modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")


def remove_specific_import_from_line(line, import_to_remove):
    """Remove a specific import from a line containing multiple imports."""
    # Handle comma-separated imports
    if "," in line and import_to_remove in line:
        # Split by 'import' to get the imports part
        parts = line.split("import ", 1)
        if len(parts) == 2:
            prefix = parts[0] + "import "
            imports_part = parts[1]
            
            # Split imports and remove the unwanted one
            imports = [imp.strip() for imp in imports_part.split(",")]
            filtered_imports = [imp for imp in imports if import_to_remove.strip() not in imp]
            
            if len(filtered_imports) < len(imports):
                if filtered_imports:
                    return prefix + ", ".join(filtered_imports)
                else:
                    # All imports removed, remove the entire line
                    return ""
    
    return line


if __name__ == "__main__":
    remove_specific_unused_imports()
    print("Unused import removal completed!")