"""
Project Scanner Module

A comprehensive tool for analyzing Python projects, with a focus on agent-based architectures.
Provides dependency analysis, code quality metrics, and agent categorization.
"""

from .scanner import Scanner
from .models.analysis import ProjectAnalysis, FileAnalysis, ClassInfo
from .analyzers.dependency_analyzer import DependencyAnalyzer
from .analyzers.quality_analyzer import QualityAnalyzer

__all__ = [
    'Scanner',
    'ProjectAnalysis',
    'FileAnalysis',
    'ClassInfo',
    'DependencyAnalyzer',
    'QualityAnalyzer'
]

"""Project Scanner - A modular and extensible project analysis tool.""" 