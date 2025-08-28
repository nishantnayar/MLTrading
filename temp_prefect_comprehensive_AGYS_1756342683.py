
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.processors.feature_engineering import FeatureEngineerPhase1And2

try:
    engineer = FeatureEngineerPhase1And2()
    success = engineer.process_symbol_phase3_comprehensive("AGYS", initial_run=False)
    print("SUCCESS" if success else "FAILED")
    sys.exit(0 if success else 1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
