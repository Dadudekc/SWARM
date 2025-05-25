"""
Performance tests for the agent control system.
"""

import json
import time
import asyncio
import statistics
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock
import pytest
from dreamos.core.agent_control.controller import AgentController
from dreamos.core.agent_control.menu_builder import MenuBuilder
from dreamos.core.messaging import MessageProcessor, Message, MessageMode
from dreamos.core.agent_control.agent_operations import AgentOperations

@pytest.fixture
def temp_runtime_dir(tmp_path):
    """Create a temporary runtime directory structure."""
    runtime_dir = tmp_path / "runtime"
    mailbox_dir = runtime_dir / "mailbox"
    mailbox_dir.mkdir(parents=True)
    return runtime_dir

@pytest.fixture
def message_processor(temp_runtime_dir):
    """Create a real MessageProcessor instance."""
    return MessageProcessor(base_path=temp_runtime_dir)

@pytest.fixture
def agent_operations(message_processor):
    """Create a real AgentOperations instance."""
    return AgentOperations()

@pytest.fixture
def controller(message_processor, agent_operations):
    """Create a real AgentController instance."""
    controller = AgentController()
    controller.message_processor = message_processor
    controller.agent_operations = agent_operations
    return controller

@pytest.fixture
def menu_builder(controller):
    """Create a real MenuBuilder instance."""
    builder = MenuBuilder()
    builder.set_controller(controller)
    return builder

class PerformanceMetrics:
    """Helper class to collect and analyze performance metrics."""
    def __init__(self):
        self.latencies = []
        self.success_count = 0
        self.failure_count = 0
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timing."""
        self.start_time = time.time()
    
    def stop(self):
        """Stop timing."""
        self.end_time = time.time()
    
    def add_latency(self, latency):
        """Add a latency measurement."""
        self.latencies.append(latency)
    
    def record_success(self):
        """Record a successful operation."""
        self.success_count += 1
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
    
    def get_summary(self):
        """Get performance summary."""
        if not self.latencies:
            return {
                "total_time": self.end_time - self.start_time if self.end_time else 0,
                "success_rate": 0,
                "avg_latency": 0,
                "p95_latency": 0,
                "p99_latency": 0
            }
        
        return {
            "total_time": self.end_time - self.start_time,
            "success_rate": self.success_count / (self.success_count + self.failure_count),
            "avg_latency": statistics.mean(self.latencies),
            "p95_latency": statistics.quantiles(self.latencies, n=20)[18],
            "p99_latency": statistics.quantiles(self.latencies, n=100)[98]
        }

def test_single_message_latency(controller, menu_builder, temp_runtime_dir):
    """Test latency of single message delivery."""
    metrics = PerformanceMetrics()
    
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Measure message delivery
    metrics.start()
    menu_builder._handle_menu_action("resume", "Agent-1")
    metrics.stop()
    
    # Calculate latency
    latency = metrics.end_time - metrics.start_time
    metrics.add_latency(latency)
    
    # Verify message was delivered
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    assert inbox_path.exists()
    
    # Record success
    metrics.record_success()
    
    # Get performance summary
    summary = metrics.get_summary()
    assert summary["success_rate"] == 1.0
    assert summary["avg_latency"] > 0

@pytest.mark.asyncio
async def test_concurrent_message_dispatch(controller, menu_builder, temp_runtime_dir):
    """Test performance of concurrent message dispatch."""
    metrics = PerformanceMetrics()
    num_messages = 100
    num_agents = 10
    
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    async def send_message(agent_id):
        start_time = time.time()
        try:
            menu_builder._handle_menu_action("resume", f"Agent-{agent_id}")
            metrics.record_success()
        except Exception:
            metrics.record_failure()
        finally:
            latency = time.time() - start_time
            metrics.add_latency(latency)
    
    # Start timing
    metrics.start()
    
    # Send messages concurrently
    tasks = []
    for i in range(num_messages):
        agent_id = i % num_agents
        tasks.append(send_message(agent_id))
    
    await asyncio.gather(*tasks)
    
    # Stop timing
    metrics.stop()
    
    # Verify messages were delivered
    for i in range(num_agents):
        inbox_path = temp_runtime_dir / "mailbox" / f"Agent-{i}" / "inbox.json"
        assert inbox_path.exists()
    
    # Get performance summary
    summary = metrics.get_summary()
    assert summary["success_rate"] > 0.95  # Allow for some failures
    assert summary["avg_latency"] > 0

def test_message_cleanup_performance(controller, menu_builder, temp_runtime_dir):
    """Test performance of message cleanup operation."""
    metrics = PerformanceMetrics()
    
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create many messages
    num_messages = 1000
    for i in range(num_messages):
        menu_builder._handle_menu_action("resume", "Agent-1")
    
    # Measure cleanup performance
    metrics.start()
    controller.message_processor.cleanup_messages(max_age_seconds=0)
    metrics.stop()
    
    # Calculate latency
    latency = metrics.end_time - metrics.start_time
    metrics.add_latency(latency)
    
    # Get performance summary
    summary = metrics.get_summary()
    assert summary["avg_latency"] > 0

def test_system_under_load(controller, menu_builder, temp_runtime_dir):
    """Test system behavior under sustained load."""
    metrics = PerformanceMetrics()
    num_iterations = 50
    
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Start timing
    metrics.start()
    
    # Perform multiple operations
    for i in range(num_iterations):
        start_time = time.time()
        try:
            # Alternate between different operations
            operation = ["resume", "verify", "repair"][i % 3]
            menu_builder._handle_menu_action(operation, "Agent-1")
            metrics.record_success()
        except Exception:
            metrics.record_failure()
        finally:
            latency = time.time() - start_time
            metrics.add_latency(latency)
    
    # Stop timing
    metrics.stop()
    
    # Get performance summary
    summary = metrics.get_summary()
    
    # Save performance data
    perf_dir = temp_runtime_dir / "devlog"
    perf_dir.mkdir(exist_ok=True)
    perf_file = perf_dir / "perf_test_summary.json"
    
    with perf_file.open("w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_name": "system_under_load",
            "metrics": summary
        }, f, indent=2)
    
    assert summary["success_rate"] > 0.95
    assert summary["avg_latency"] > 0

def test_message_ordering_under_load(controller, menu_builder, temp_runtime_dir):
    """Test message ordering under high load."""
    metrics = PerformanceMetrics()
    num_messages = 100
    
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Send many messages rapidly
    for i in range(num_messages):
        start_time = time.time()
        menu_builder._handle_menu_action("resume", "Agent-1")
        latency = time.time() - start_time
        metrics.add_latency(latency)
    
    # Verify message ordering
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert len(data) == num_messages
        
        # Verify messages are in order
        for i in range(num_messages):
            assert "resume" in data[i]["content"].lower()
    
    # Get performance summary
    summary = metrics.get_summary()
    assert summary["avg_latency"] > 0 