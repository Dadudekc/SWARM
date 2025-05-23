# Duplication Prevention Guide

## Overview
This guide outlines strategies and best practices for preventing and managing code duplication in the SWARM project. Code duplication is a critical issue that can lead to maintenance problems, inconsistencies, and increased technical debt.

## Types of Duplication

### 1. Code Duplication
- Identical or similar code blocks
- Copied functions or methods
- Repeated business logic
- Similar error handling patterns

### 2. Configuration Duplication
- Repeated environment variables
- Duplicate settings across files
- Similar configuration patterns
- Redundant constants

### 3. Documentation Duplication
- Repeated explanations
- Similar README sections
- Duplicate API documentation
- Redundant comments

## Prevention Strategies

### 1. Code Organization

#### Use Shared Libraries
```python
# Instead of duplicating code:
# agent1.py
def process_data(data):
    # 100 lines of processing logic
    pass

# agent2.py
def process_data(data):
    # Same 100 lines of processing logic
    pass

# Create a shared utility:
# core/utils/data_processing.py
def process_data(data):
    # Single source of truth
    pass
```

#### Implement Base Classes
```python
class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "initialized"
    
    def start(self):
        """Common start logic."""
        pass
    
    def stop(self):
        """Common stop logic."""
        pass

class CustomAgent(BaseAgent):
    """Extends base agent with custom logic."""
    
    def start(self):
        super().start()
        # Custom start logic
```

### 2. Configuration Management

#### Use Environment Variables
```python
# config.py
from pathlib import Path
from typing import Dict
import os

class Config:
    """Centralized configuration management."""
    
    @staticmethod
    def load() -> Dict:
        """Load configuration from environment."""
        return {
            "database_url": os.getenv("DATABASE_URL"),
            "redis_url": os.getenv("REDIS_URL"),
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        }
```

#### Implement Configuration Inheritance
```python
# config/base.py
class BaseConfig:
    """Base configuration class."""
    
    DEBUG = False
    TESTING = False
    
# config/development.py
class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    
    DEBUG = True
    
# config/production.py
class ProductionConfig(BaseConfig):
    """Production configuration."""
    
    DEBUG = False
```

### 3. Documentation Management

#### Use Docstring Templates
```python
def function_template():
    """Function description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: Description of when this exception is raised
    """
    pass
```

#### Implement Documentation Inheritance
```python
class BaseClass:
    """Base class documentation."""
    
    def method(self):
        """Base method documentation."""
        pass

class ChildClass(BaseClass):
    """Child class documentation.
    
    Inherits from :class:`BaseClass`.
    """
    
    def method(self):
        """Child method documentation.
        
        Extends :meth:`BaseClass.method`.
        """
        super().method()
```

## Detection Tools

### 1. Static Analysis
- Use `pylint` for code duplication detection
- Implement `flake8` with duplication plugins
- Run `mypy` for type checking
- Use `bandit` for security checks

### 2. Dynamic Analysis
- Implement runtime checks
- Use logging for pattern detection
- Monitor performance metrics
- Track code coverage

## Best Practices

### 1. Code Review Process
1. Check for duplication
2. Verify inheritance usage
3. Review shared utilities
4. Validate documentation

### 2. Development Workflow
1. Create shared utilities first
2. Use base classes
3. Implement interfaces
4. Document patterns

### 3. Maintenance
1. Regular code reviews
2. Automated checks
3. Documentation updates
4. Pattern validation

## Common Pitfalls

### 1. Over-Abstraction
- Don't create abstractions too early
- Keep interfaces simple
- Avoid premature optimization
- Maintain readability

### 2. Under-Abstraction
- Don't copy code
- Use shared utilities
- Implement base classes
- Follow DRY principle

### 3. Documentation
- Keep docs up to date
- Use templates
- Avoid redundancy
- Maintain consistency

## Tools and Resources

### 1. Development Tools
- IDE plugins
- Linting tools
- Testing frameworks
- Documentation generators

### 2. Monitoring Tools
- Code coverage
- Performance metrics
- Error tracking
- Usage statistics

### 3. Documentation
- API documentation
- Code examples
- Best practices
- Troubleshooting guides

## Implementation Examples

### 1. Shared Utilities
```python
# core/utils/validation.py
def validate_input(data: dict) -> bool:
    """Validate input data."""
    required_fields = ["name", "type", "value"]
    return all(field in data for field in required_fields)

# Use in agents:
from core.utils.validation import validate_input

class Agent:
    def process_data(self, data: dict) -> None:
        if not validate_input(data):
            raise ValueError("Invalid input data")
```

### 2. Base Classes
```python
# core/agents/base.py
class BaseAgent:
    """Base agent class."""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "initialized"
    
    def start(self) -> None:
        """Start the agent."""
        self.status = "running"
    
    def stop(self) -> None:
        """Stop the agent."""
        self.status = "stopped"

# Use in custom agents:
class CustomAgent(BaseAgent):
    """Custom agent implementation."""
    
    def start(self) -> None:
        super().start()
        # Custom start logic
```

### 3. Configuration Management
```python
# core/config.py
from pathlib import Path
from typing import Dict
import os

class Config:
    """Configuration management."""
    
    @staticmethod
    def load() -> Dict:
        """Load configuration."""
        return {
            "database_url": os.getenv("DATABASE_URL"),
            "redis_url": os.getenv("REDIS_URL"),
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        }

# Use in agents:
from core.config import Config

class Agent:
    def __init__(self):
        self.config = Config.load()
```

## Conclusion

### Key Takeaways
1. Use shared utilities
2. Implement base classes
3. Centralize configuration
4. Maintain documentation
5. Regular code reviews
6. Automated checks
7. Follow best practices
8. Monitor for duplication

### Next Steps
1. Review existing code
2. Identify duplication
3. Create shared utilities
4. Update documentation
5. Implement checks
6. Monitor progress 