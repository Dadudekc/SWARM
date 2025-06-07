"""
Global pytest configuration.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add tests directory to Python path
tests_dir = project_root / "tests"
sys.path.insert(0, str(tests_dir)) 