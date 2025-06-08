"""
Log Analyzer Test Script
-----------------------
Validates the Log Analyzer CLI in production-like conditions.
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import random
import json
import shutil

# Test configuration
TEST_AGENT = "test_agent"
LOG_DIR = Path("logs/agent_loop")
LOG_LEVELS = ["debug", "info", "warning", "error"]
TEST_MESSAGES = [
    "System initialized",
    "Task started: data_processing",
    "Processing batch of 100 items",
    "Error: Connection timeout",
    "Retrying operation",
    "Task completed successfully",
    "Warning: High memory usage",
    "Error: Invalid response format",
    "Debug: Detailed state dump",
    "Info: Regular status update"
]

def setup_test_environment():
    """Set up test environment with sample logs."""
    print("Setting up test environment...")
    
    # Create log directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate test logs
    start_time = datetime.now() - timedelta(days=2)
    for level in LOG_LEVELS:
        log_file = LOG_DIR / f"{TEST_AGENT}_loop_{level}.log"
        
        # Generate 100 log entries
        with open(log_file, "w") as f:
            for i in range(100):
                # Add some random gaps
                if random.random() < 0.1:  # 10% chance of gap
                    start_time += timedelta(minutes=random.randint(5, 30))
                
                timestamp = start_time + timedelta(minutes=i)
                message = random.choice(TEST_MESSAGES)
                f.write(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
                
                # Add some errors
                if "error" in message.lower():
                    f.write(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Stack trace: Error in module X\n")
    
    print("Test environment setup complete.")

def run_analyzer_tests():
    """Run various analyzer tests."""
    print("\nRunning analyzer tests...")
    
    # Test 1: Basic log viewing
    print("\nTest 1: Basic log viewing")
    subprocess.run(["python", "tools/analyze_logs.py", "--agent", TEST_AGENT, "--level", "error"])
    
    # Test 2: Summary generation
    print("\nTest 2: Summary generation")
    subprocess.run(["python", "tools/analyze_logs.py", "--agent", TEST_AGENT, "--summary"])
    
    # Test 3: Markdown export
    print("\nTest 3: Markdown export")
    subprocess.run(["python", "tools/analyze_logs.py", "--agent", TEST_AGENT, "--summary", "--export", "md"])
    
    # Test 4: JSON export
    print("\nTest 4: JSON export")
    subprocess.run(["python", "tools/analyze_logs.py", "--agent", TEST_AGENT, "--summary", "--export", "json"])
    
    # Test 5: Log rotation
    print("\nTest 5: Log rotation")
    subprocess.run(["python", "tools/analyze_logs.py", "--agent", TEST_AGENT, "--rotate"])
    
    # Test 6: Log clearing
    print("\nTest 6: Log clearing")
    subprocess.run(["python", "tools/analyze_logs.py", "--agent", TEST_AGENT, "--clear", "--days", "1"])

def validate_results():
    """Validate the results of the tests."""
    print("\nValidating results...")
    
    # Check if log files exist
    for level in LOG_LEVELS:
        log_file = LOG_DIR / f"{TEST_AGENT}_loop_{level}.log"
        if not log_file.exists():
            print(f"❌ Error: Log file not found: {log_file}")
            continue
            
        # Check file content
        with open(log_file) as f:
            content = f.read()
            if not content:
                print(f"❌ Error: Empty log file: {log_file}")
            else:
                print(f"✅ Log file valid: {log_file}")
    
    # Check for rotated files
    rotated_files = list(LOG_DIR.glob(f"{TEST_AGENT}_loop_*.log.*"))
    if rotated_files:
        print(f"✅ Found {len(rotated_files)} rotated log files")
    else:
        print("❌ No rotated log files found")

def cleanup():
    """Clean up test environment."""
    print("\nCleaning up test environment...")
    if LOG_DIR.exists():
        shutil.rmtree(LOG_DIR)
    print("Cleanup complete.")

def main():
    """Run the test suite."""
    try:
        setup_test_environment()
        run_analyzer_tests()
        validate_results()
    finally:
        cleanup()

if __name__ == "__main__":
    main() 
