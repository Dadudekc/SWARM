# Bridge Integration Agent Rollout Guide

## Overview

This guide provides a standardized approach for agents to integrate with the ChatGPT bridge system. It includes usage patterns, response handling, and best practices.

## Quick Start

```python
from dreamos.core.messaging.bridge_integration import BridgeIntegration
from dreamos.core.messaging.utils.core_utils import format_message, parse_message

class AgentBridgeHandler:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.bridge = BridgeIntegration()
        
    async def start(self):
        await self.bridge.start()
        
    async def stop(self):
        await self.bridge.stop()
        
    async def process_with_chatgpt(self, prompt: str, msg_type: str = "default"):
        """Process a prompt through ChatGPT with proper error handling."""
        try:
            response = await self.bridge.send_to_agent(
                agent_id=self.agent_id,
                message=prompt,
                msg_type=msg_type
            )
            return self._parse_response(response)
        except Exception as e:
            self._log_error(e)
            return None
            
    def _parse_response(self, response: dict) -> dict:
        """Parse and validate ChatGPT response."""
        if not response or "content" not in response:
            return {"error": "Invalid response format"}
        return response
        
    def _log_error(self, error: Exception):
        """Log bridge errors to agent devlog."""
        # Implementation depends on agent's logging system
        pass
```

## Message Types

Use these standardized message types for different use cases:

| Type | Description | Example |
|------|-------------|---------|
| `task_analysis` | Analyze and break down tasks | "Analyze this feature request" |
| `code_review` | Review and suggest improvements | "Review this implementation" |
| `debug_trace` | Debug and trace issues | "Debug this error" |
| `research_summary` | Summarize research findings | "Summarize these findings" |
| `plan_request` | Create execution plans | "Plan this feature" |

## Response Format

All responses follow this structure:

```python
{
    "content": str,  # Main response content
    "type": str,     # Message type
    "metadata": {    # Additional context
        "timestamp": str,
        "agent_id": str,
        "task_id": str
    }
}
```

## Error Handling

Implement these patterns for robust error handling:

```python
async def safe_bridge_call(self, prompt: str, max_retries: int = 3):
    """Make a safe bridge call with retries."""
    for attempt in range(max_retries):
        try:
            response = await self.process_with_chatgpt(prompt)
            if response and "error" not in response:
                return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Health Monitoring

Regularly check bridge health:

```python
async def check_bridge_health(self):
    """Check bridge health status."""
    status = self.bridge.get_health_status()
    if status["metrics"]["failed_requests"] > 0:
        self._log_warning("Bridge has failed requests")
    return status
```

## Best Practices

1. **Always Use Message Types**
   ```python
   response = await bridge.send_to_agent(
       agent_id=self.agent_id,
       message=prompt,
       msg_type="task_analysis"  # Always specify type
   )
   ```

2. **Handle Responses Properly**
   ```python
   if response := await self.process_with_chatgpt(prompt):
       content = response.get("content", "")
       metadata = response.get("metadata", {})
       # Process content and metadata
   ```

3. **Monitor Performance**
   ```python
   status = self.bridge.get_health_status()
   if status["metrics"]["average_response_time"] > 10.0:
       self._log_warning("Slow bridge responses")
   ```

4. **Clean Up Resources**
   ```python
   try:
       await self.bridge.start()
       # Use bridge
   finally:
       await self.bridge.stop()
   ```

## Integration Checklist

- [ ] Initialize `BridgeIntegration` in agent startup
- [ ] Implement proper error handling
- [ ] Add health monitoring
- [ ] Use standardized message types
- [ ] Follow response format
- [ ] Add logging and metrics
- [ ] Test with various message types
- [ ] Verify cleanup on shutdown

## Troubleshooting

Common issues and solutions:

1. **Bridge Not Responding**
   - Check health status
   - Verify agent ID
   - Check message format

2. **Invalid Responses**
   - Verify response structure
   - Check message type
   - Validate content

3. **Performance Issues**
   - Monitor response times
   - Check queue status
   - Verify network connection 