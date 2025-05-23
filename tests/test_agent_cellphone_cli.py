"""
Test suite for agent_cellphone.py CLI functionality.
"""

import pytest
import subprocess
import sys
from pathlib import Path

def run_cli_command(args):
    """Run the CLI command and return the result."""
    # Add the project root to Python path
    project_root = Path(__file__).parent.parent
    cli_script = project_root / "dreamos" / "core" / "cell_phone_cli.py"
    cmd = [sys.executable, str(cli_script)] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

def test_cli_help():
    """Test the help command."""
    result = run_cli_command(["--help"])
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "--to" in result.stdout
    assert "--message" in result.stdout
    assert "--priority" in result.stdout
    assert "--mode" in result.stdout
    assert "--welcome" in result.stdout

def test_cli_required_args():
    """Test that required arguments are enforced."""
    result = run_cli_command([])
    assert result.returncode != 0
    assert "error: the following arguments are required:" in result.stderr
    assert "--to" in result.stderr

def test_cli_welcome_message():
    """Test sending a welcome message."""
    result = run_cli_command(["--welcome", "--to", "Agent-2"])
    assert result.returncode == 0
    assert "Message sent to Agent-2" in result.stdout
    assert "Welcome to Dream.OS!" in result.stdout
    assert "Status:" in result.stdout

def test_cli_custom_message():
    """Test sending a custom message."""
    result = run_cli_command(["--to", "Agent-3", "--message", "Test message", "--priority", "2"])
    assert result.returncode == 0
    assert "Message sent to Agent-3" in result.stdout
    assert "Test message" in result.stdout
    assert "Status:" in result.stdout

def test_cli_invalid_priority():
    """Test handling of invalid priority."""
    result = run_cli_command(["--to", "Agent-4", "--message", "Test", "--priority", "6"])
    assert result.returncode != 0
    assert "Error: Priority must be between 0 and 5" in result.stderr

def test_cli_invalid_mode():
    """Test handling of invalid mode."""
    result = run_cli_command(["--to", "Agent-5", "--message", "Test", "--mode", "INVALID"])
    assert result.returncode != 0
    assert "invalid choice" in result.stderr

def test_cli_message_with_mode():
    """Test sending a message with a specific mode."""
    result = run_cli_command(["--to", "Agent-6", "--message", "Test message", "--mode", "RESUME"])
    assert result.returncode == 0
    assert "Message sent to Agent-6" in result.stdout
    assert "[RESUME]" in result.stdout
    assert "Status:" in result.stdout

def test_cli_concurrent_messages():
    """Test sending multiple messages concurrently."""
    import concurrent.futures
    
    def send_message(agent_id):
        return run_cli_command(["--to", f"Agent-{agent_id}", "--message", f"Test {agent_id}"])
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(send_message, range(7, 10)))
    
    assert all(r.returncode == 0 for r in results)
    assert all("Message sent to" in r.stdout for r in results)
    assert all("Status:" in r.stdout for r in results) 