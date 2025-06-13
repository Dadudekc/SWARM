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
   - Version information
   - Health check endpoints

2. **Communication**:
   - CellPhone integration
   - Message handling
   - State management
   - Error reporting
   - Metrics collection
   - Health status updates

3. **Task Processing**:
   - Task acceptance
   - Progress tracking
   - Result reporting
   - Error handling
   - Resource monitoring
   - Performance metrics

### Cursor Agent Requirements

#### Outbox Management
1. **Response Recording**:
   ```python
   save_json({
       "status": "complete",
       "response": full_text,
       "started_at": ts_start,
       "completed_at": ts_end,
       "metrics": {
           "processing_time": ts_end - ts_start,
           "memory_usage": get_memory_usage(),
           "cpu_usage": get_cpu_usage()
       }
   }, f"runtime/bridge_outbox/agent-{agent_id}.json")
   ```

2. **Staleness Handling**:
   - Check file modification time
   - Mark as stale after 5 minutes
   - Trigger resume logic
   - Update status
   - Log staleness events
   - Report metrics

## Agent Development

### Agent Structure
```python
class Agent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.cell_phone = CellPhone()
        self.state = AgentState()
        self.capabilities = []
        self.metrics = AgentMetrics()
        self.health = HealthMonitor()

    async def start(self):
        """Initialize agent and register with system."""
        await self.register()
        await self.initialize_capabilities()
        await self.start_message_loop()
        await self.start_health_monitoring()

    async def process_message(self, message: Message):
        """Process incoming messages."""
        try:
            with self.metrics.measure_processing_time():
                response = await self.handle_message(message)
                await self.record_response(response)
        except Exception as e:
            await self.handle_error(e)
            await self.health.report_error(e)

    async def record_response(self, response: str):
        """Record agent response in outbox."""
        await save_json({
            "status": "complete",
            "response": response,
            "started_at": self.state.started_at,
            "completed_at": time.time(),
            "metrics": self.metrics.get_current_metrics()
        }, f"runtime/bridge_outbox/agent-{self.agent_id}.json")
```

### Message Handling
1. **Message Types**:
   - Command messages
   - Task messages
   - Status messages
   - Error messages
   - Health check messages
   - Metrics messages

2. **Message Processing**:
   - Message validation
   - Capability matching
   - Task execution
   - Response generation
   - Metrics collection
   - Health updates

3. **Error Handling**:
   - Error detection
   - Error reporting
   - Recovery procedures
   - State restoration
   - Error metrics
   - Health impact

### State Management
1. **State Components**:
   - Current task
   - Processing status
   - Resource usage
   - Error state
   - Health status
   - Performance metrics

2. **State Operations**:
   - State updates
   - State persistence
   - State recovery
   - State validation
   - State metrics
   - Health checks

## Agent Lifecycle

### Initialization
1. **Registration**:
   - System registration
   - Capability declaration
   - Resource allocation
   - State initialization
   - Metrics setup
   - Health monitoring

2. **Setup**:
   - Message loop setup
   - Task queue setup
   - Error handler setup
   - Monitoring setup
   - Metrics collection
   - Health checks

### Runtime
1. **Message Loop**:
   - Message reception
   - Message processing
   - Response generation
   - State updates
   - Metrics collection
   - Health monitoring

2. **Task Processing**:
   - Task acceptance
   - Task execution
   - Progress tracking
   - Result reporting
   - Performance metrics
   - Resource monitoring

3. **Monitoring**:
   - Health checks
   - Resource monitoring
   - Error monitoring
   - Performance tracking
   - Metrics collection
   - Health reporting

### Shutdown
1. **Cleanup**:
   - Task completion
   - Resource release
   - State persistence
   - Message cleanup
   - Metrics finalization
   - Health reporting

2. **Reporting**:
   - Final status
   - Error summary
   - Resource usage
   - Performance metrics
   - Health status
   - Cleanup status

## Best Practices

### Development
1. **Code Organization**:
   - Clear structure
   - Modular design
   - Proper documentation
   - Type safety
   - Metrics integration
   - Health monitoring

2. **Error Handling**:
   - Comprehensive error handling
   - Error recovery
   - Error reporting
   - State management
   - Error metrics
   - Health impact

3. **Testing**:
   - Unit tests
   - Integration tests
   - Performance tests
   - Error tests
   - Health tests
   - Metrics tests

### Performance
1. **Resource Management**:
   - Efficient resource usage
   - Resource cleanup
   - Resource monitoring
   - Resource limits
   - Resource metrics
   - Health impact

2. **Message Processing**:
   - Efficient message handling
   - Message queuing
   - Message prioritization
   - Message filtering
   - Message metrics
   - Health monitoring

3. **State Management**:
   - Efficient state updates
   - State persistence
   - State recovery
   - State validation
   - State metrics
   - Health checks

### Security
1. **Authentication**:
   - Agent authentication
   - Message authentication
   - State authentication
   - Health authentication
   - Metrics authentication
   - Resource authentication

2. **Authorization**:
   - Capability checks
   - Resource limits
   - State access
   - Health access
   - Metrics access
   - Message access

3. **Data Protection**:
   - Message encryption
   - State encryption
   - Health data protection
   - Metrics protection
   - Resource protection
   - Error protection

## Agent Patterns

### 1. Worker Pattern
```python
class WorkerAgent(Agent):
    async def process_task(self, task: Task):
        """Process a single task."""
        with self.metrics.measure_task_time():
            result = await self.execute_task(task)
            await self.report_result(result)

    async def execute_task(self, task: Task):
        """Execute the actual task."""
        # Task implementation
        pass
```

### 2. Supervisor Pattern
```python
class SupervisorAgent(Agent):
    async def supervise_workers(self):
        """Supervise worker agents."""
        while True:
            await self.check_worker_health()
            await self.rebalance_workload()
            await self.collect_metrics()
```

### 3. Coordinator Pattern
```python
class CoordinatorAgent(Agent):
    async def coordinate_tasks(self):
        """Coordinate multiple tasks."""
        tasks = await self.get_pending_tasks()
        results = await self.distribute_tasks(tasks)
        await self.aggregate_results(results)
```

## Monitoring and Metrics

### 1. Health Monitoring
```python
class HealthMonitor:
    def __init__(self):
        self.health_status = "healthy"
        self.last_check = time.time()
        self.error_count = 0

    async def check_health(self):
        """Check agent health."""
        try:
            await self.verify_capabilities()
            await self.check_resources()
            await self.verify_state()
            self.health_status = "healthy"
        except Exception as e:
            self.health_status = "unhealthy"
            self.error_count += 1
```

### 2. Metrics Collection
```python
class AgentMetrics:
    def __init__(self):
        self.metrics = {
            "processing_time": [],
            "memory_usage": [],
            "cpu_usage": [],
            "error_count": 0,
            "task_count": 0
        }

    @contextmanager
    def measure_processing_time(self):
        """Measure processing time."""
        start_time = time.time()
        try:
            yield
        finally:
            self.metrics["processing_time"].append(time.time() - start_time)
```

### 3. Performance Monitoring
```python
class PerformanceMonitor:
    def __init__(self):
        self.performance_metrics = {
            "response_time": [],
            "throughput": [],
            "resource_usage": []
        }

    async def monitor_performance(self):
        """Monitor agent performance."""
        while True:
            await self.collect_metrics()
            await self.analyze_performance()
            await self.report_metrics()
```

## Security Best Practices

### 1. Authentication
```python
class SecureAgent(Agent):
    async def authenticate(self):
        """Authenticate agent."""
        token = await self.get_auth_token()
        await self.verify_token(token)
        await self.setup_secure_channel()

    async def verify_message(self, message: Message):
        """Verify message authenticity."""
        if not await self.verify_signature(message):
            raise SecurityError("Invalid message signature")
```

### 2. Authorization
```python
class AuthorizedAgent(Agent):
    async def check_permissions(self, action: str):
        """Check action permissions."""
        if not await self.has_permission(action):
            raise PermissionError(f"No permission for {action}")

    async def enforce_limits(self):
        """Enforce resource limits."""
        if await self.exceeds_limits():
            raise ResourceLimitError("Resource limits exceeded")
```

### 3. Data Protection
```python
class SecureDataHandler:
    def __init__(self):
        self.encryption_key = self.load_encryption_key()

    async def encrypt_data(self, data: dict):
        """Encrypt sensitive data."""
        return await self.encrypt(data, self.encryption_key)

    async def decrypt_data(self, encrypted_data: bytes):
        """Decrypt sensitive data."""
        return await self.decrypt(encrypted_data, self.encryption_key)
``` 