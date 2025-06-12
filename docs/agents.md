# Agent Development Guide

## Overview
This guide outlines the requirements, best practices, and implementation details for developing and managing agents in the Dream.OS system.

## Agent Requirements

### Core Requirements
1. **Agent Registration**:
   - Unique agent ID
   - Capability declaration
   - Resource requirements
   - Dependencies

2. **Communication**:
   - CellPhone integration
   - Message handling
   - State management
   - Error reporting

3. **Task Processing**:
   - Task acceptance
   - Progress tracking
   - Result reporting
   - Error handling

### Cursor Agent Requirements

#### Outbox Management
1. **Response Recording**:
   ```python
   save_json({
       "status": "complete",
       "response": full_text,
       "started_at": ts_start,
       "completed_at": ts_end
   }, f"runtime/bridge_outbox/agent-{agent_id}.json")
   ```

2. **Staleness Handling**:
   - Check file modification time
   - Mark as stale after 5 minutes
   - Trigger resume logic
   - Update status

## Agent Development

### Agent Structure
```python
class Agent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.cell_phone = CellPhone()
        self.state = AgentState()
        self.capabilities = []

    async def start(self):
        """Initialize agent and register with system."""
        await self.register()
        await self.initialize_capabilities()
        await self.start_message_loop()

    async def process_message(self, message: Message):
        """Process incoming messages."""
        try:
            response = await self.handle_message(message)
            await self.record_response(response)
        except Exception as e:
            await self.handle_error(e)

    async def record_response(self, response: str):
        """Record agent response in outbox."""
        await save_json({
            "status": "complete",
            "response": response,
            "started_at": self.state.started_at,
            "completed_at": time.time()
        }, f"runtime/bridge_outbox/agent-{self.agent_id}.json")
```

### Message Handling
1. **Message Types**:
   - Command messages
   - Task messages
   - Status messages
   - Error messages

2. **Message Processing**:
   - Message validation
   - Capability matching
   - Task execution
   - Response generation

3. **Error Handling**:
   - Error detection
   - Error reporting
   - Recovery procedures
   - State restoration

### State Management
1. **State Components**:
   - Current task
   - Processing status
   - Resource usage
   - Error state

2. **State Operations**:
   - State updates
   - State persistence
   - State recovery
   - State validation

## Agent Lifecycle

### Initialization
1. **Registration**:
   - System registration
   - Capability declaration
   - Resource allocation
   - State initialization

2. **Setup**:
   - Message loop setup
   - Task queue setup
   - Error handler setup
   - Monitoring setup

### Runtime
1. **Message Loop**:
   - Message reception
   - Message processing
   - Response generation
   - State updates

2. **Task Processing**:
   - Task acceptance
   - Task execution
   - Progress tracking
   - Result reporting

3. **Monitoring**:
   - Health checks
   - Resource monitoring
   - Error monitoring
   - Performance tracking

### Shutdown
1. **Cleanup**:
   - Task completion
   - Resource release
   - State persistence
   - Message cleanup

2. **Reporting**:
   - Final status
   - Error summary
   - Resource usage
   - Performance metrics

## Best Practices

### Development
1. **Code Organization**:
   - Clear structure
   - Modular design
   - Proper documentation
   - Type safety

2. **Error Handling**:
   - Comprehensive error handling
   - Error recovery
   - Error reporting
   - State management

3. **Testing**:
   - Unit tests
   - Integration tests
   - Performance tests
   - Error tests

### Performance
1. **Resource Management**:
   - Efficient resource usage
   - Resource cleanup
   - Resource monitoring
   - Resource limits

2. **Message Processing**:
   - Efficient message handling
   - Message queuing
   - Message prioritization
   - Message filtering

3. **State Management**:
   - Efficient state updates
   - State persistence
   - State recovery
   - State validation

### Security
1. **Authentication**:
   - Agent authentication
   - Message authentication
   - Task authentication
   - Resource authentication

2. **Authorization**:
   - Capability checks
   - Resource access
   - Operation validation
   - State protection

3. **Data Protection**:
   - Message encryption
   - State encryption
   - Resource protection
   - Access control

## Monitoring and Maintenance

### Health Monitoring
1. **Health Checks**:
   - Agent status
   - Resource usage
   - Error state
   - Performance metrics

2. **Resource Monitoring**:
   - CPU usage
   - Memory usage
   - Network usage
   - Storage usage

3. **Error Monitoring**:
   - Error detection
   - Error reporting
   - Error analysis
   - Error resolution

### Maintenance
1. **Regular Tasks**:
   - State cleanup
   - Resource cleanup
   - Log rotation
   - Performance optimization

2. **Updates**:
   - Capability updates
   - Resource updates
   - State updates
   - Configuration updates

3. **Recovery**:
   - State recovery
   - Resource recovery
   - Error recovery
   - Performance recovery 