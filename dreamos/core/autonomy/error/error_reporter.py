"""
Error Reporter
-------------
Handles error reporting and notifications.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from .error_tracker import ErrorTracker, ErrorSeverity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorReporter:
    """Handles error reporting and notifications."""
    
    def __init__(self, error_tracker: ErrorTracker, report_dir: Path):
        """Initialize error reporter.
        
        Args:
            error_tracker: Error tracker instance
            report_dir: Directory for error reports
        """
        self.error_tracker = error_tracker
        self.report_dir = report_dir
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, agent_id: Optional[str] = None,
                       severity: Optional[ErrorSeverity] = None) -> Dict[str, Any]:
        """Generate error report.
        
        Args:
            agent_id: Optional agent ID filter
            severity: Optional severity filter
            
        Returns:
            Error report
        """
        errors = self.error_tracker.get_errors(agent_id, severity)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_errors": len(errors),
            "by_severity": self._count_by_severity(errors),
            "by_agent": self._count_by_agent(errors),
            "by_type": self._count_by_type(errors),
            "errors": errors
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """Save error report.
        
        Args:
            report: Error report
            filename: Optional filename
            
        Returns:
            Path to saved report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_report_{timestamp}.json"
        
        report_path = self.report_dir / filename
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        return report_path
    
    def _count_by_severity(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count errors by severity.
        
        Args:
            errors: List of errors
            
        Returns:
            Count by severity
        """
        counts = {}
        for error in errors:
            severity = error["severity"]
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _count_by_agent(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count errors by agent.
        
        Args:
            errors: List of errors
            
        Returns:
            Count by agent
        """
        counts = {}
        for error in errors:
            agent_id = error["agent_id"]
            counts[agent_id] = counts.get(agent_id, 0) + 1
        return counts
    
    def _count_by_type(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count errors by type.
        
        Args:
            errors: List of errors
            
        Returns:
            Count by type
        """
        counts = {}
        for error in errors:
            error_type = error["error_type"]
            counts[error_type] = counts.get(error_type, 0) + 1
        return counts 