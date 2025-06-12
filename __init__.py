# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

from . import analyze_dirs
from . import conftest
from . import find_duplicates
from . import fix_imports
from . import fix_test_imports
from . import move_tests
from . import pyautogui
from . import pygetwindow
try:
    from . import run_overnight  # type: ignore
except ImportError:  # pragma: no cover - optional fallback
    run_overnight = None  # type: ignore
try:
    from . import run_scanner  # type: ignore
except ImportError:  # pragma: no cover - optional fallback
    run_scanner = None  # type: ignore
from . import scan_missing_imports
from . import setup

__all__ = [
    'analyze_dirs',
    'conftest',
    'find_duplicates',
    'fix_imports',
    'fix_test_imports',
    'move_tests',
    'pyautogui',
    'pygetwindow',
    'run_overnight',
    'run_scanner',
    'scan_missing_imports',
    'setup',
]
