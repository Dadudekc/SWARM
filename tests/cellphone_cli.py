"""
Test suite for agent_cellphone.py CLI functionality.
"""

import pytest
import subprocess
import sys
from pathlib import Path
import concurrent.futures
import json
import os
from concurrent.futures import ThreadPoolExecutor

def setup_test_environment():
    """Set up test environment with necessary directories and files."""
    # Create test directories
    runtime_dir = Path("runtime")
    for dir_path in [
        runtime_dir / "config",
        runtime_dir / "agent_memory" / "Agent-test_agent",
        runtime_dir / "queue",
        runtime_dir / "mailbox" / "Agent-test_agent",
        Path("test_logs")
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Handle coordinates file - preserve existing coordinates
    coords_file = runtime_dir / "config" / "cursor_agent_coords.json"
    test_coords = {
        "Agent-test_agent": {
            "input_box": {"x": 100, "y": 100},
            "copy_button": {"x": 200, "y": 100},
            "input_box_initial": {"x": 100, "y": 100},
            "initial_spot": {"x": 100, "y": 100},
            "response_region": {"x": 100, "y": 100, "width": 500, "height": 300}
        }
    }
    
    # Load existing coordinates if file exists
    if coords_file.exists():
        try:
            existing_coords = json.loads(coords_file.read_text())
            # Merge test coordinates with existing ones
            existing_coords.update(test_coords)
            coords_file.write_text(json.dumps(existing_coords, indent=2))
        except json.JSONDecodeError:
            # If file is corrupted, create new with test coordinates
            coords_file.write_text(json.dumps(test_coords, indent=2))
    else:
        # If file doesn't exist, create with test coordinates
        coords_file.write_text(json.dumps(test_coords, indent=2))

    # Create agent config file
    config_file = runtime_dir / "agent_memory" / "Agent-test_agent" / "config.json"
    config = {
        "agent_id": "Agent-test_agent",
        "logging": {
            "level": "INFO",
            "file": "test_logs/agent.log"
        }
    }
    config_file.write_text(json.dumps(config, indent=2))

    # Create empty message queue and mailbox files
    (runtime_dir / "queue" / "messages.json").write_text("[]")
    (runtime_dir / "mailbox" / "Agent-test_agent" / "messages.json").write_text("[]")

def run_cli_command(args):
    """Run a CLI command and return the result."""
    # Set up test environment
    setup_test_environment()
    
    # Get the absolute path to the CLI script
    cli_path = Path(__file__).parent.parent.parent / "dreamos" / "core" / "cli.py"
    
    # Build the command
    cmd = [sys.executable, str(cli_path)] + args
    
    # Run the command with proper environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)
    env["DREAMOS_CONFIG_DIR"] = str(Path("runtime/config"))
    env["DREAMOS_AGENT_MEMORY_DIR"] = str(Path("runtime/agent_memory"))
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        return result
    except Exception as e:
        print(f"Error running CLI command: {e}")
        print(f"Command: {' '.join(cmd)}")
        print(f"Working directory: {Path(__file__).parent.parent.parent}")
        raise

def test_cli_help():
    """Test CLI help command."""
    result = run_cli_command(["--help"])
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "usage:" in result.stdout
    assert "--help" in result.stdout

def test_cli_required_args():
    """Test CLI required arguments."""
    result = run_cli_command([])
    assert result.returncode == 1, f"Command failed: {result.stderr}"
    assert "Error: --to argument is required" in result.stderr

def test_cli_welcome_message():
    """Test welcome message functionality."""
    result = run_cli_command(["--to", "Agent-test_agent", "--welcome"])
    assert result.returncode == 0
    assert "Welcome to Dream.OS!" in result.stdout
    assert "Your initial tasks:" in result.stdout
    assert "Status: queued" in result.stdout

def test_cli_custom_message():
    """Test sending a custom message."""
    result = run_cli_command(["--to", "Agent-test_agent", "--message", "Test message"])
    assert result.returncode == 0
    assert "Message sent to Agent-test_agent" in result.stdout
    assert "Status: queued" in result.stdout

def test_cli_invalid_priority():
    """Test CLI invalid priority."""
    result = run_cli_command(["--to", "Agent-test_agent", "--priority", "6"])
    assert result.returncode == 1, f"Command failed: {result.stderr}"
    assert "Error: Priority must be between 0 and 5" in result.stderr

def test_cli_invalid_mode():
    """Test CLI invalid mode."""
    result = run_cli_command(["--to", "Agent-test_agent", "--mode", "INVALID"])
    assert result.returncode == 2, f"Command failed: {result.stderr}"
    assert "invalid choice" in result.stderr

def test_cli_message_with_mode():
    """Test sending a message with a specific mode."""
    result = run_cli_command(["--to", "Agent-test_agent", "--message", "Test message", "--mode", "PRIORITY"])
    assert result.returncode == 0
    assert "Message sent to Agent-test_agent" in result.stdout
    assert "[PRIORITY]" in result.stdout
    assert "Status: queued" in result.stdout

def test_cli_concurrent_messages():
    """Test sending multiple messages concurrently."""
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i in range(3):
            futures.append(executor.submit(
                run_cli_command,
                ["--to", "Agent-test_agent", "--message", f"Test message {i}"]
            ))
        
        results = [f.result() for f in futures]
        for result in results:
            assert result.returncode == 0
            assert "Message sent to Agent-test_agent" in result.stdout
            assert "Status: queued" in result.stdout 
