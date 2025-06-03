"""
Test Fix Orchestrator
--------------------
Systematically fixes test issues based on error analysis.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import shutil
import os

class TestFixOrchestrator:
    def __init__(self, analysis_file: str = "test_error_analysis.json"):
        self.analysis_file = analysis_file
        self.analysis_data = self._load_analysis()
        self.backup_dir = Path("test_backups")
        
    def _load_analysis(self) -> Dict[str, Any]:
        """Load test error analysis data."""
        with open(self.analysis_file) as f:
            return json.load(f)
    
    def _backup_file(self, file_path: str) -> None:
        """Create backup of file before modification."""
        src = Path(file_path)
        if not src.exists():
            return
            
        self.backup_dir.mkdir(exist_ok=True)
        dst = self.backup_dir / f"{src.stem}_{src.suffix}.bak"
        shutil.copy2(src, dst)
    
    def fix_log_config(self) -> None:
        """Fix LogConfig initialization issues."""
        print("\nFixing LogConfig initialization...")
        
        # Backup files
        for file in self.analysis_data["error_categories"]["configuration_errors"]["errors"][0]["files"]:
            self._backup_file(file)
        
        # Update LogConfig class
        config_file = "social/utils/log_config.py"
        self._backup_file(config_file)
        
        with open(config_file, "r") as f:
            content = f.read()
        
        # Add max_size parameter
        if "max_size" not in content:
            content = content.replace(
                "def __init__(self, log_dir: str = 'logs',",
                "def __init__(self, log_dir: str = 'logs', max_size: int = 10 * 1024 * 1024,"
            )
            content = content.replace(
                "self.log_dir = log_dir",
                "self.log_dir = log_dir\n        self.max_size = max_size"
            )
            
            with open(config_file, "w") as f:
                f.write(content)
    
    def fix_devlog_manager(self) -> None:
        """Implement missing DevlogManager.send_embed method."""
        print("\nImplementing DevlogManager.send_embed...")
        
        devlog_file = "dreamos/core/devlog.py"
        self._backup_file(devlog_file)
        
        with open(devlog_file, "r") as f:
            content = f.read()
        
        # Add send_embed method
        if "def send_embed" not in content:
            embed_method = """
    def send_embed(self, title: str, description: str, color: int = 0x00ff00) -> None:
        \"\"\"Send an embed message to the devlog channel.
        
        Args:
            title: Embed title
            description: Embed description
            color: Embed color (hex)
        \"\"\"
        if not self.channel:
            return
            
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.now().isoformat()
        }
        
        self.channel.send(embed=embed)
"""
            # Find class definition
            class_pos = content.find("class DevlogManager")
            if class_pos != -1:
                # Find last method
                last_method = content.rfind("def ", 0, class_pos)
                if last_method != -1:
                    content = content[:last_method] + embed_method + content[last_method:]
                    
                    with open(devlog_file, "w") as f:
                        f.write(content)
    
    def fix_log_metrics(self) -> None:
        """Add missing attributes to LogMetrics."""
        print("\nAdding missing LogMetrics attributes...")
        
        metrics_file = "social/core/log_metrics.py"
        self._backup_file(metrics_file)
        
        with open(metrics_file, "r") as f:
            content = f.read()
        
        # Add missing attributes
        if "last_error_message" not in content:
            content = content.replace(
                "def __init__(self):",
                """def __init__(self):
        self.last_error_message = None
        self.error_count = 0
        self.warning_count = 0
        self.last_error_time = None"""
            )
            
            with open(metrics_file, "w") as f:
                f.write(content)
    
    def fix_file_permissions(self) -> None:
        """Fix file permission issues."""
        print("\nFixing file permissions...")
        
        log_dir = Path("logs")
        if log_dir.exists():
            # Ensure directory is writable
            os.chmod(log_dir, 0o777)
            
            # Fix permissions for all log files
            for file in log_dir.rglob("*.log"):
                os.chmod(file, 0o666)
    
    def run_tests(self) -> None:
        """Run test suite to verify fixes."""
        print("\nRunning test suite...")
        subprocess.run(["python", "-m", "pytest", "-v"])
    
    def fix_all(self) -> None:
        """Apply all fixes in priority order."""
        print("Starting test fixes...")
        
        # Apply fixes in priority order
        for fix in self.analysis_data["priority_fixes"]:
            if fix["priority"] == "high":
                if "LogConfig" in fix["description"]:
                    self.fix_log_config()
                elif "DevlogManager" in fix["description"]:
                    self.fix_devlog_manager()
                elif "LogMetrics" in fix["description"]:
                    self.fix_log_metrics()
                elif "permission" in fix["description"].lower():
                    self.fix_file_permissions()
        
        # Run tests to verify fixes
        self.run_tests()

def main():
    """Main entry point."""
    orchestrator = TestFixOrchestrator()
    orchestrator.fix_all()

if __name__ == "__main__":
    main() 