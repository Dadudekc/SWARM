# Dream.OS Integration Specifications

## Overview
This document outlines the integration specifications for Dream.OS, including API endpoints, data formats, and integration patterns.

## API Integration

### REST API
1. Base URL
   ```
   https://api.dreamos.com/v1
   ```

2. Authentication
   ```http
   POST /auth/token
   Content-Type: application/json
   
   {
     "username": "string",
     "password": "string"
   }
   ```

3. Endpoints
   - Agents
     ```http
     GET /agents
     GET /agents/{id}
     POST /agents
     PUT /agents/{id}
     DELETE /agents/{id}
     ```
   
   - Tasks
     ```http
     GET /tasks
     GET /tasks/{id}
     POST /tasks
     PUT /tasks/{id}
     DELETE /tasks/{id}
     ```
   
   - System
     ```http
     GET /system/status
     GET /system/metrics
     POST /system/command
     ```

### WebSocket API
1. Connection
   ```
   wss://api.dreamos.com/v1/ws
   ```

2. Authentication
   ```json
   {
     "type": "auth",
     "token": "string"
   }
   ```

3. Message Types
   - System Events
     ```json
     {
       "type": "system_event",
       "event": "string",
       "data": {}
     }
     ```
   
   - Agent Events
     ```json
     {
       "type": "agent_event",
       "agent_id": "string",
       "event": "string",
       "data": {}
     }
     ```
   
   - Task Events
     ```json
     {
       "type": "task_event",
       "task_id": "string",
       "event": "string",
       "data": {}
     }
     ```

## Data Formats

### JSON Schema
1. Agent
   ```json
   {
     "id": "string",
     "name": "string",
     "type": "string",
     "status": "string",
     "settings": {},
     "metrics": {}
   }
   ```

2. Task
   ```json
   {
     "id": "string",
     "name": "string",
     "type": "string",
     "status": "string",
     "parameters": {},
     "result": {}
   }
   ```

3. System
   ```json
   {
     "status": "string",
     "version": "string",
     "metrics": {},
     "settings": {}
   }
   ```

### Message Format
1. Request
   ```json
   {
     "id": "string",
     "type": "string",
     "action": "string",
     "parameters": {},
     "timestamp": "string"
   }
   ```

2. Response
   ```json
   {
     "id": "string",
     "type": "string",
     "status": "string",
     "result": {},
     "error": {},
     "timestamp": "string"
   }
   ```

## Integration Patterns

### Agent Integration
1. Registration
   ```python
   def register_agent(agent_config):
       """Register a new agent."""
       # Validate config
       if not validate_config(agent_config):
           raise ValueError("Invalid config")
           
       # Register agent
       response = api.post("/agents", json=agent_config)
       
       # Process response
       return process_response(response)
   ```

2. Communication
   ```python
   def send_message(agent_id, message):
       """Send message to agent."""
       # Validate message
       if not validate_message(message):
           raise ValueError("Invalid message")
           
       # Send message
       response = api.post(f"/agents/{agent_id}/messages", json=message)
       
       # Process response
       return process_response(response)
   ```

### Task Integration
1. Task Creation
   ```python
   def create_task(task_config):
       """Create a new task."""
       # Validate config
       if not validate_config(task_config):
           raise ValueError("Invalid config")
           
       # Create task
       response = api.post("/tasks", json=task_config)
       
       # Process response
       return process_response(response)
   ```

2. Task Monitoring
   ```python
   def monitor_task(task_id):
       """Monitor task status."""
       # Get task status
       response = api.get(f"/tasks/{task_id}")
       
       # Process response
       return process_response(response)
   ```

### System Integration
1. Status Check
   ```python
   def check_system_status():
       """Check system status."""
       # Get status
       response = api.get("/system/status")
       
       # Process response
       return process_response(response)
   ```

2. Metrics Collection
   ```python
   def collect_metrics():
       """Collect system metrics."""
       # Get metrics
       response = api.get("/system/metrics")
       
       # Process response
       return process_response(response)
   ```

## Error Handling

### Error Codes
1. HTTP Status Codes
   - 200: Success
   - 400: Bad Request
   - 401: Unauthorized
   - 403: Forbidden
   - 404: Not Found
   - 500: Internal Server Error

2. Error Response
   ```json
   {
     "error": {
       "code": "string",
       "message": "string",
       "details": {}
     }
   }
   ```

### Error Handling
1. API Errors
   ```python
   def handle_api_error(error):
       """Handle API error."""
       if error.status_code == 401:
           # Handle unauthorized
           handle_unauthorized()
       elif error.status_code == 403:
           # Handle forbidden
           handle_forbidden()
       else:
           # Handle other errors
           handle_other_error(error)
   ```

2. Connection Errors
   ```python
   def handle_connection_error(error):
       """Handle connection error."""
       # Log error
       logger.error(f"Connection error: {error}")
       
       # Retry connection
       retry_connection()
   ```

## Security

### Authentication
1. API Key
   ```python
   def authenticate_api_key(api_key):
       """Authenticate using API key."""
       # Validate key
       if not validate_api_key(api_key):
           raise ValueError("Invalid API key")
           
       # Set authentication
       api.set_auth_header(f"Bearer {api_key}")
   ```

2. OAuth
   ```python
   def authenticate_oauth(credentials):
       """Authenticate using OAuth."""
       # Get token
       token = get_oauth_token(credentials)
       
       # Set authentication
       api.set_auth_header(f"Bearer {token}")
   ```

### Authorization
1. Role-Based Access
   ```python
   def check_permission(user, resource, action):
       """Check user permission."""
       # Get user roles
       roles = get_user_roles(user)
       
       # Check permission
       return has_permission(roles, resource, action)
   ```

2. Resource Access
   ```python
   def check_resource_access(user, resource):
       """Check resource access."""
       # Get resource permissions
       permissions = get_resource_permissions(resource)
       
       # Check access
       return has_access(user, permissions)
   ```

## Monitoring

### Metrics
1. System Metrics
   ```python
   def collect_system_metrics():
       """Collect system metrics."""
       # Get CPU usage
       cpu_usage = get_cpu_usage()
       
       # Get memory usage
       memory_usage = get_memory_usage()
       
       # Get disk usage
       disk_usage = get_disk_usage()
       
       return {
           "cpu": cpu_usage,
           "memory": memory_usage,
           "disk": disk_usage
       }
   ```

2. Application Metrics
   ```python
   def collect_app_metrics():
       """Collect application metrics."""
       # Get request count
       request_count = get_request_count()
       
       # Get error count
       error_count = get_error_count()
       
       # Get response time
       response_time = get_response_time()
       
       return {
           "requests": request_count,
           "errors": error_count,
           "response_time": response_time
       }
   ```

### Logging
1. System Logs
   ```python
   def log_system_event(event):
       """Log system event."""
       # Format log
       log_entry = format_log_entry(event)
       
       # Write log
       write_log(log_entry)
   ```

2. Application Logs
   ```python
   def log_app_event(event):
       """Log application event."""
       # Format log
       log_entry = format_log_entry(event)
       
       # Write log
       write_log(log_entry)
   ```

## Best Practices

### API Usage
1. Rate Limiting
   - Respect rate limits
   - Implement backoff
   - Handle limits gracefully
   - Monitor usage

2. Error Handling
   - Handle all errors
   - Implement retries
   - Log errors
   - Report issues

3. Security
   - Use HTTPS
   - Validate input
   - Sanitize output
   - Protect credentials

### Integration
1. Testing
   - Unit test integration
   - Integration test
   - Load test
   - Security test

2. Monitoring
   - Monitor performance
   - Track errors
   - Log events
   - Alert issues

3. Maintenance
   - Update dependencies
   - Review security
   - Optimize performance
   - Document changes

## Codex Bridge Integration

### Overview
The Codex Bridge integration enables autonomous code understanding, review, and generation for Dream.OS swarm. It provides a resilient AI quality control layer with automated code review and improvement capabilities.

### Capabilities
1. Web Native Features
   - Undetected Login
     - Persistent session management
     - Encrypted cookie storage
     - Session continuity
   - Browser Control
     - Headless/hybrid operation
     - Stealth mode
     - Anti-detection measures

2. Swarm Intelligence
   - Code Review
     - Live code analysis
     - Recommendation parsing
     - Automated feedback
   - Code Generation
     - Docstring generation
     - Test generation
     - Module generation
   - Vulnerability Scanning
     - Buffer overflow detection
     - Security best practices
     - Vulnerability assessment
   - Cross-Agent QA
     - Code quality assessment
     - Style consistency
     - Best practices enforcement
   - Feedback Loop
     - PR regeneration
     - Code improvement
     - Learning from feedback

### Compatibility
1. Subsystems
   - BrowserControl: Base class extended
   - BridgeHealthMonitor: Status reporting + retries
   - RequestQueue: Async injection compatible
   - with_retry: Preserved for browser ops
   - YAML Config: Standard runtime patterns
   - Logging: Standard formatter

2. Security Features
   - Rate Limiting: Retry backoff
   - Session Storage: Encrypted cookies
   - Browser Shutdown: Clean error handling
   - Anti-Detection: Header/timing randomization

### Features
1. Preserved Features
   - Session handling across runs
   - Async-compatible browser usage
   - Agent-task loop integration
   - Modular agent access

2. New Features
   - Stealth Mode Browser: Evades bot detection
   - Codex Bridge Prompt Cycle: Inbound→Prompt→Reply→Parse
   - Cookie Persistence: Auto reuses session state
   - Platform Router: Route to Codex, Bard, etc.
   - Interactive Login: Manual-first login fallback
   - Enhanced Retry Logic: Tiered failover & backoff

### Verification
1. Test Suite
   - Browser Control: test_existing_browser_control
   - Request Queue: test_existing_request_queue
   - Codex Prompt Cycle: test_codex_prompt_cycle
   - Cookie Restore: test_cookie_restore
   - Login Fallback: test_login_fallback

2. Config Validation
   - Structure Check: codex_config.structure == base_bridge_config.structure
   - Security Check: codex_config.security.encryption == True
   - Rate Limit Check: codex_config.rate_limit.window <= 60

3. Monitoring
   - CPU Usage: monitor_cpu_usage
   - Session Reuse: monitor_session_reuse
   - Request Tracking: track_agent_codex_requests

### Next Steps
1. High Priority
   - Integration Tests: Create full integration tests across login/prompt/response loop
   - Login Hardening: Implement OTP/email fallback flow

2. Medium Priority
   - CodexHandler Agent: Assign dedicated agent for QA & patch generation
   - Platform Router: Extend to include Anthropic, Gemini, etc.
   - Memory Layer: Track Codex insights across tasks

### Status Summary
- Integration: Active
- Codex Injection: Tested
- Cookie System: Working
- OTP 2FA: Needs Implementation
- Devlog Bridge: Needs Implementation 