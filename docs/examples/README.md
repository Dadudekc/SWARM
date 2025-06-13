# Dream.OS Examples

## Overview
This directory contains example code and documentation for various Dream.OS features and components. Each example demonstrates best practices and common use cases.

## Agent Examples

### Basic Agent
```python
from core.agents import BaseAgent

class ExampleAgent(BaseAgent):
    """Example agent demonstrating basic functionality."""
    
    def __init__(self):
        """Initialize the agent."""
        super().__init__()
        self.name = "example_agent"
        
    def process_message(self, message):
        """Process incoming messages."""
        # Handle message
        response = self._handle_message(message)
        
        # Send response
        self.send_response(response)
        
    def _handle_message(self, message):
        """Handle specific message types."""
        if message.type == "command":
            return self._handle_command(message)
        elif message.type == "query":
            return self._handle_query(message)
        else:
            return self._handle_unknown(message)
```

### Worker Agent
```python
from core.agents import WorkerAgent

class ExampleWorker(WorkerAgent):
    """Example worker agent for task processing."""
    
    def __init__(self):
        """Initialize the worker."""
        super().__init__()
        self.name = "example_worker"
        
    def process_task(self, task):
        """Process assigned tasks."""
        # Validate task
        if not self._validate_task(task):
            return self._create_error_response("Invalid task")
            
        # Process task
        result = self._execute_task(task)
        
        # Return result
        return self._create_success_response(result)
```

### Supervisor Agent
```python
from core.agents import SupervisorAgent

class ExampleSupervisor(SupervisorAgent):
    """Example supervisor agent for task management."""
    
    def __init__(self):
        """Initialize the supervisor."""
        super().__init__()
        self.name = "example_supervisor"
        self.workers = []
        
    def assign_task(self, task):
        """Assign task to appropriate worker."""
        # Find suitable worker
        worker = self._find_worker(task)
        
        if not worker:
            return self._create_error_response("No suitable worker")
            
        # Assign task
        result = worker.process_task(task)
        
        # Monitor result
        self._monitor_task(task, result)
        
        return result
```

## UI Examples

### Basic Window
```python
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout

class ExampleWindow(QMainWindow):
    """Example window demonstrating basic UI."""
    
    def __init__(self):
        """Initialize the window."""
        super().__init__()
        self.setWindowTitle("Example Window")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Create layout
        layout = QVBoxLayout()
        central.setLayout(layout)
        
        # Add widgets
        self._add_widgets(layout)
        
    def _add_widgets(self, layout):
        """Add widgets to layout."""
        # Add your widgets here
        pass
```

### Custom Widget
```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class ExampleWidget(QWidget):
    """Example custom widget."""
    
    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Add widgets
        self._add_widgets(layout)
        
    def _add_widgets(self, layout):
        """Add widgets to layout."""
        # Add label
        label = QLabel("Example Widget")
        layout.addWidget(label)
        
        # Add button
        button = QPushButton("Click Me")
        button.clicked.connect(self._handle_click)
        layout.addWidget(button)
        
    def _handle_click(self):
        """Handle button click."""
        # Handle click event
        pass
```

## System Examples

### Service Example
```python
from core.services import BaseService

class ExampleService(BaseService):
    """Example system service."""
    
    def __init__(self):
        """Initialize the service."""
        super().__init__()
        self.name = "example_service"
        
    def start(self):
        """Start the service."""
        # Initialize service
        self._initialize()
        
        # Start processing
        self._start_processing()
        
    def stop(self):
        """Stop the service."""
        # Stop processing
        self._stop_processing()
        
        # Cleanup
        self._cleanup()
```

### Task Example
```python
from core.tasks import BaseTask

class ExampleTask(BaseTask):
    """Example system task."""
    
    def __init__(self):
        """Initialize the task."""
        super().__init__()
        self.name = "example_task"
        
    def execute(self):
        """Execute the task."""
        # Validate task
        if not self._validate():
            return False
            
        # Execute task
        result = self._run()
        
        # Process result
        return self._process_result(result)
```

## Testing Examples

### Unit Test
```python
import pytest
from core.agents import ExampleAgent

def test_example_agent():
    """Test example agent functionality."""
    # Create agent
    agent = ExampleAgent()
    
    # Test initialization
    assert agent.name == "example_agent"
    
    # Test message handling
    message = create_test_message()
    response = agent.process_message(message)
    assert response is not None
```

### Integration Test
```python
import pytest
from core.system import System

def test_system_integration():
    """Test system integration."""
    # Create system
    system = System()
    
    # Start system
    system.start()
    
    # Test functionality
    result = system.execute_test()
    assert result is not None
    
    # Stop system
    system.stop()
```

## Configuration Examples

### Agent Config
```yaml
name: example_agent
type: worker
settings:
  max_tasks: 10
  timeout: 30
  retry_count: 3
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### System Config
```yaml
system:
  name: example_system
  version: 1.0.0
  settings:
    max_agents: 100
    max_memory: 1024
    max_cpu: 4
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "system.log"
```

## Best Practices

### Code Organization
1. Follow the project structure
2. Use clear naming conventions
3. Add proper documentation
4. Include type hints

### Error Handling
1. Use proper exception handling
2. Add error logging
3. Implement recovery procedures
4. Validate inputs

### Testing
1. Write unit tests
2. Add integration tests
3. Include performance tests
4. Document test cases

### Documentation
1. Add docstrings
2. Include examples
3. Document parameters
4. Explain return values 