import pytest
import subprocess
import os
from pathlib import Path

def test_cli_script_exists():
    """Test that the CLI script exists and is executable."""
    script_path = Path(__file__).parent.parent.parent / "dreamos" / "core" / "cli.py"
    assert script_path.exists(), f"CLI script not found at {script_path}"
    assert os.access(script_path, os.X_OK), f"CLI script not executable at {script_path}"

def test_cli_help():
    """Test CLI help command."""
    script_path = Path(__file__).parent.parent.parent / "dreamos" / "core" / "cli.py"
    result = subprocess.run(
        ["python", str(script_path), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"CLI help command failed: {result.stderr}"
    assert "usage:" in result.stdout.lower(), "Help output should contain usage information"

def test_cli_version():
    """Test CLI version command."""
    script_path = Path(__file__).parent.parent.parent / "dreamos" / "core" / "cli.py"
    result = subprocess.run(
        ["python", str(script_path), "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"CLI version command failed: {result.stderr}"
    assert "version" in result.stdout.lower(), "Version output should contain version information"

def test_cli_invalid_command():
    """Test CLI with invalid command."""
    script_path = Path(__file__).parent.parent.parent / "dreamos" / "core" / "cli.py"
    result = subprocess.run(
        ["python", str(script_path), "invalid_command"],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0, "Invalid command should return non-zero exit code"
    assert "error" in result.stderr.lower(), "Error message should be displayed for invalid command" 
