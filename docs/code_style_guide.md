# Code Style Guide

## Overview
This guide outlines the coding standards and best practices for the SWARM project.

## Python Style Guide

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

## Testing Style

### Test Organization
1. Test Files
   - Name: `test_*.py`
   - Location: `tests/` directory
   - One test file per module

2. Test Classes
   ```python
   class TestMyClass:
       """Test suite for MyClass."""

       def setup_method(self):
           """Set up test fixtures."""
           pass

       def test_specific_feature(self):
           """Test specific feature."""
           pass
   ```

### Test Naming
1. Test Functions
   - Name: `test_*`
   - Be descriptive
   - Include expected outcome

2. Test Cases
   - One assertion per test
   - Clear test names
   - Document edge cases

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

## Best Practices

### Code Quality
1. Keep functions small
2. Use meaningful names
3. Add proper documentation
4. Handle errors appropriately
5. Write comprehensive tests

### Performance
1. Use appropriate data structures
2. Optimize critical paths
3. Profile when necessary
4. Cache when appropriate

### Security
1. Validate input
2. Handle sensitive data
3. Use secure defaults
4. Follow security guidelines

## Tools

### Linting
1. Use pylint
2. Configure in setup.cfg
3. Run before commits

### Formatting
1. Use black
2. Configure in pyproject.toml
3. Run before commits

### Type Checking
1. Use mypy
2. Configure in mypy.ini
3. Run in CI/CD

## Review Process

### Code Review
1. Check style compliance
2. Verify documentation
3. Review error handling
4. Check test coverage

### Pull Requests
1. Follow template
2. Include tests
3. Update documentation
4. Address comments 