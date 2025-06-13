# Dream.OS Contribution Guide

## Overview
This guide outlines the process for contributing to the Dream.OS project, including coding standards, best practices, and workflow procedures.

## Getting Started

### Prerequisites
1. Git installed on your system
2. Python 3.8 or higher
3. Discord account (for bot testing)
4. Basic understanding of:
   - Python programming
   - Discord bot development
   - Agent-based systems

### Repository Setup
1. Fork the repository
   ```bash
   git clone https://github.com/victor-general/Dream.OS.git
   cd Dream.OS
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

## Code Style Guide

### General Rules
1. Follow PEP 8 guidelines
2. Use meaningful variable names
3. Keep functions focused and small
4. Use type hints
5. Write docstrings

### Naming Conventions
1. Variables and Functions
   - Use snake_case
   - Be descriptive
   - Avoid abbreviations

2. Classes
   - Use PascalCase
   - Be descriptive
   - Avoid abbreviations

3. Constants
   - Use UPPER_SNAKE_CASE
   - Be descriptive
   - Group related constants

### Code Organization
1. Imports
   ```python
   # Standard library imports
   import os
   import sys

   # Third-party imports
   import discord
   import pytest

   # Local imports
   from core import utils
   from agents import base
   ```

2. Class Structure
   ```python
   class MyClass:
       """Class docstring."""

       # Class variables
       CONSTANT = "value"

       def __init__(self):
           """Initialize the class."""
           self.instance_var = None

       def public_method(self):
           """Public method docstring."""
           pass

       def _private_method(self):
           """Private method docstring."""
           pass
   ```

### Documentation
1. Docstrings
   ```python
   def function_name(param1: str, param2: int) -> bool:
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

2. Comments
   - Use comments to explain why, not what
   - Keep comments up to date
   - Use clear language

### Type Hints
1. Basic Types
   ```python
   def process_data(data: list[str]) -> dict[str, int]:
       """Process the input data."""
       pass
   ```

2. Optional Types
   ```python
   from typing import Optional

   def get_value(key: str) -> Optional[str]:
       """Get value for key if it exists."""
       pass
   ```

3. Union Types
   ```python
   from typing import Union

   def process_input(value: Union[str, int]) -> bool:
       """Process input of either string or integer."""
       pass
   ```

## Development Workflow

### Branch Management
1. Create a new branch for your feature
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Follow branch naming conventions:
   - `feature/` - New features
   - `fix/` - Bug fixes
   - `docs/` - Documentation
   - `test/` - Test additions
   - `refactor/` - Code refactoring

### Testing
1. Write unit tests for new features
2. Run existing tests
   ```bash
   python -m pytest tests/
   ```
3. Ensure all tests pass
4. Add integration tests where appropriate

## Agent Development

### Creating New Agents
1. Follow the agent template structure
2. Implement required interfaces
3. Add proper error handling
4. Include logging
5. Write tests

### Agent Communication
1. Use the message bus system
2. Follow message format standards
3. Implement proper error handling
4. Add message validation

## Error Handling

### Exception Handling
1. Specific Exceptions
   ```python
   try:
       process_data()
   except ValueError as e:
       handle_value_error(e)
   except TypeError as e:
       handle_type_error(e)
   ```

2. Custom Exceptions
   ```python
   class SwarmError(Exception):
       """Base exception for SWARM project."""
       pass

   class AgentError(SwarmError):
       """Exception raised for agent-related errors."""
       pass
   ```

## Logging

### Log Levels
1. Use appropriate levels
   - DEBUG: Detailed information
   - INFO: General information
   - WARNING: Warning messages
   - ERROR: Error messages
   - CRITICAL: Critical errors

2. Log Format
   ```python
   import logging

   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

## Pull Request Process

### Before Submitting
1. Update documentation
2. Add tests
3. Run linters
4. Check formatting
5. Verify all tests pass

### Pull Request Template
```markdown
## Description
[Describe your changes]

## Related Issues
[Link to related issues]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Test addition
- [ ] Code refactoring

## Testing
[Describe testing performed]

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No merge conflicts
```

## Review Process

### Code Review
1. Address reviewer comments
2. Make requested changes
3. Update documentation
4. Ensure tests pass
5. Squash commits if needed

### Merging
1. Get required approvals
2. Resolve conflicts
3. Update documentation
4. Merge to main branch

## Best Practices

### Code Quality
1. Write clean, readable code
2. Follow SOLID principles
3. Use design patterns appropriately
4. Keep functions focused
5. Add proper error handling

### Testing
1. Write comprehensive tests
2. Test edge cases
3. Include integration tests
4. Maintain test coverage

### Documentation
1. Keep docs up to date
2. Add examples
3. Include troubleshooting
4. Document changes

## Getting Help

### Resources
1. Project documentation
2. Issue tracker
3. Discord community
4. Code examples

### Communication
1. Use issue tracker
2. Join Discord server
3. Follow contribution guidelines
4. Be respectful and professional

## License
[Include license information]

## Acknowledgments
[Add acknowledgments section] 