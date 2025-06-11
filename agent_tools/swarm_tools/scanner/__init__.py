"""
Project Scanner
----------
Analyzes the Dream.OS codebase for code metrics, dependencies, and generates various reports.
Automatically runs on git push via pre-push hook.
"""

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="agent_tools.swarm_tools.scanner")

from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging

from .scanner import Scanner, ScanResults
from .analyzers.bridge_analyzer import BridgeAnalyzer
from .analyzers.ui_analyzer import UIAnalyzer
from .analyzers.feedback_analyzer import FeedbackAnalyzer
from .analyzers.codex_analyzer import CodexAnalyzer
from .analyzers.discord_analyzer import DiscordAnalyzer
from .reporters.json_reporter import JSONReporter
from .utils.ast_utils import ASTUtils
from .utils.file_utils import FileUtils
from .utils.code_utils import CodeUtils
from .utils.pattern_utils import PatternUtils

__all__ = [
    'Scanner',
    'ScanResults',
    'BridgeAnalyzer',
    'UIAnalyzer',
    'FeedbackAnalyzer',
    'CodexAnalyzer',
    'DiscordAnalyzer',
    'JSONReporter',
    'ASTUtils',
    'FileUtils',
    'CodeUtils',
    'PatternUtils'
]
