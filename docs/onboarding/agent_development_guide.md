# Agent Development Guide

## Overview

This guide provides comprehensive information for developing and integrating new agents into the Dream.OS ecosystem.

## Development Environment Setup

### Prerequisites
- Python 3.11 or higher
- Git
- Virtual environment (recommended)

### Installation
```bash
# Clone the repository
git clone https://github.com/your-org/dreamos.git
cd dreamos

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Agent Structure

### Basic Agent Template
```python
from dreamos.core.agent_base import AgentBase

class MyAgent(AgentBase):
    def __init__(self):
        super().__init__("MyAgent")
        self.initialize()
    
    def initialize(self):
        """Initialize agent-specific resources."""
        pass
    
    def process_message(self, message):
        """Process incoming messages."""
        pass
    
    def cleanup(self):
        """Clean up resources before shutdown."""
        pass
```

### Required Components
1. **Initialization**
   - Agent ID and name
   - Resource setup
   - State initialization

2. **Message Handling**
   - Message processing
   - Response generation
   - Error handling

3. **State Management**
   - Status tracking
   - Resource monitoring
   - Performance metrics

## Agent Lifecycle

### 1. Creation
- Define agent class
- Implement required methods
- Set up configuration

### 2. Initialization
- Load dependencies
- Initialize resources
- Register with system

### 3. Operation
- Process messages
- Maintain state
- Handle errors

### 4. Shutdown
- Clean up resources
- Save state
- Log final status

## Testing

### Unit Tests
```python
import pytest
from dreamos.core.agent_base import AgentBase

def test_agent_initialization():
    agent = MyAgent()
    assert agent.status == "initialized"
    assert agent.agent_id is not None

def test_message_processing():
    agent = MyAgent()
    response = agent.process_message("test message")
    assert response is not None
```

### Integration Tests
```python
def test_agent_communication():
    agent1 = MyAgent()
    agent2 = MyAgent()
    
    # Test message exchange
    success = agent1.send_message(agent2.agent_id, "test")
    assert success
```

## Best Practices

### 1. Code Organization
- Follow project structure
- Use clear naming conventions
- Document code thoroughly

### 2. Error Handling
- Implement proper error handling
- Log errors appropriately
- Provide meaningful error messages

### 3. Resource Management
- Clean up resources properly
- Monitor resource usage
- Handle resource limits

### 4. Performance
- Optimize message processing
- Minimize resource usage
- Monitor performance metrics

## Integration with Core Systems

### Message System
```python
from dreamos.core.cell_phone import send_message, MessageMode

class MyAgent(AgentBase):
    def send_alert(self, message):
        send_message("System", message, 
                    priority=5, 
                    mode=MessageMode.URGENT)
```

### DevLog Integration
```python
from dreamos.core.agent_devlog import AgentDevLog

class MyAgent(AgentBase):
    def __init__(self):
        super().__init__("MyAgent")
        self.devlog = AgentDevLog(self.agent_id)
    
    def log_event(self, event):
        self.devlog.log_event(event)
```

## Debugging

### Common Issues
1. **Initialization Failures**
   - Check dependencies
   - Verify configuration
   - Review error logs

2. **Message Processing**
   - Validate message format
   - Check processing logic
   - Monitor performance

3. **Resource Issues**
   - Monitor resource usage
   - Check cleanup procedures
   - Review error handling

### Debugging Tools
1. **Logging**
   - Use appropriate log levels
   - Include context information
   - Monitor error patterns

2. **Monitoring**
   - Track performance metrics
   - Monitor resource usage
   - Check system status

## Security Considerations

### 1. Input Validation
- Validate all inputs
- Sanitize message content
- Check permissions

### 2. Resource Protection
- Limit resource access
- Monitor usage patterns
- Implement timeouts

### 3. Error Handling
- Prevent information leakage
- Log security events
- Handle failures gracefully

## Examples

### Basic Agent
```python
from dreamos.core.agent_base import AgentBase
from dreamos.core.cell_phone import send_message

class BasicAgent(AgentBase):
    def __init__(self):
        super().__init__("BasicAgent")
        self.initialize()
    
    def initialize(self):
        self.status = "ready"
        self.counter = 0
    
    def process_message(self, message):
        self.counter += 1
        return f"Processed message {self.counter}: {message}"
    
    def cleanup(self):
        self.status = "shutdown"
```

### Advanced Agent
```python
from dreamos.core.agent_base import AgentBase
from dreamos.core.cell_phone import send_message, MessageMode
from dreamos.core.agent_devlog import AgentDevLog

class AdvancedAgent(AgentBase):
    def __init__(self):
        super().__init__("AdvancedAgent")
        self.devlog = AgentDevLog(self.agent_id)
        self.initialize()
    
    def initialize(self):
        self.status = "initializing"
        self.resources = {}
        self.initialize_resources()
        self.status = "ready"
        self.devlog.log_event("Agent initialized")
    
    def process_message(self, message):
        try:
            # Process message
            result = self.process_message_internal(message)
            
            # Log success
            self.devlog.log_event(f"Message processed: {message}")
            
            return result
        except Exception as e:
            # Log error
            self.devlog.log_event(f"Error processing message: {str(e)}")
            
            # Send alert
            send_message("System", f"Error in {self.agent_id}: {str(e)}",
                        priority=5, mode=MessageMode.URGENT)
            
            raise
    
    def cleanup(self):
        self.status = "shutting_down"
        self.cleanup_resources()
        self.devlog.log_event("Agent shutdown complete")
        self.status = "shutdown"
```

## Additional Resources

- [Agent Communication Guide](./agent_communication_guide.md)
- [System Architecture Guide](./system_architecture_guide.md)
- [CLI Usage Guide](./cli_usage_guide.md) 