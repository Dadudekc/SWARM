# Testing Guide

## Overview
This guide outlines the testing practices and procedures for the SWARM project.

## Testing Types

### Unit Tests
1. Purpose
   - Test individual components
   - Verify functionality
   - Ensure reliability

2. Location
   - `tests/unit/` directory
   - One test file per module
   - Follow naming convention

3. Example
   ```python
   def test_agent_initialization():
       """Test agent initialization."""
       agent = Agent("test_agent")
       assert agent.name == "test_agent"
       assert agent.status == "initialized"
   ```

### Integration Tests
1. Purpose
   - Test component interaction
   - Verify system behavior
   - Ensure compatibility

2. Location
   - `tests/integration/` directory
   - Group by feature
   - Include setup/teardown

3. Example
   ```python
   class TestAgentCommunication:
       """Test agent communication."""

       def setup_method(self):
           """Set up test fixtures."""
           self.agent1 = Agent("agent1")
           self.agent2 = Agent("agent2")

       def test_message_exchange(self):
           """Test message exchange between agents."""
           message = "test message"
           self.agent1.send_message(self.agent2, message)
           assert self.agent2.received_messages[-1] == message
   ```

### End-to-End Tests
1. Purpose
   - Test complete workflows
   - Verify system integration
   - Ensure user experience

2. Location
   - `tests/e2e/` directory
   - Group by workflow
   - Include environment setup

3. Example
   ```python
   class TestAgentWorkflow:
       """Test complete agent workflow."""

       def setup_method(self):
           """Set up test environment."""
           self.system = System()
           self.system.initialize()

       def test_agent_lifecycle(self):
           """Test complete agent lifecycle."""
           agent = self.system.create_agent("test_agent")
           agent.start()
           agent.process_task("test_task")
           agent.stop()
           assert agent.status == "stopped"
   ```

## Test Organization

### Directory Structure
```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── e2e/              # End-to-end tests
├── fixtures/         # Test fixtures
└── conftest.py       # Pytest configuration
```

### Test Files
1. Naming Convention
   - `test_*.py` for test files
   - `*_test.py` for test modules
   - Clear, descriptive names

2. File Organization
   - One test file per module
   - Group related tests
   - Include setup/teardown

## Test Writing

### Best Practices
1. Test Structure
   - Arrange: Set up test data
   - Act: Perform test action
   - Assert: Verify results

2. Test Isolation
   - Independent tests
   - Clean state
   - No side effects

3. Test Coverage
   - Critical paths
   - Edge cases
   - Error conditions

### Test Fixtures
1. Purpose
   - Reusable test setup
   - Common test data
   - Environment configuration

2. Implementation
   ```python
   import pytest

   @pytest.fixture
   def test_agent():
       """Create test agent."""
       agent = Agent("test_agent")
       yield agent
       agent.cleanup()
   ```

## Running Tests

### Command Line
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_file.py

# Run with coverage
pytest --cov=.

# Run specific test
pytest tests/test_file.py::test_function
```

### Test Configuration
1. Pytest Configuration
   ```ini
   [pytest]
   testpaths = tests
   python_files = test_*.py
   addopts = -v --cov=.
   ```

2. Coverage Configuration
   ```ini
   [coverage:run]
   source = .
   omit = tests/*,venv/*
   ```

## Test Maintenance

### Regular Tasks
1. Update tests
   - Keep tests current
   - Update for changes
   - Remove obsolete tests

2. Review coverage
   - Monitor coverage
   - Add missing tests
   - Remove redundant tests

### Best Practices
1. Test Quality
   - Clear test names
   - Proper documentation
   - Meaningful assertions

2. Test Performance
   - Efficient setup
   - Minimal dependencies
   - Quick execution

## Continuous Integration

### CI Setup
1. Test Execution
   - Run on every commit
   - Run on pull requests
   - Run on merges

2. Coverage Reports
   - Generate reports
   - Track coverage
   - Set thresholds

### Best Practices
1. CI Configuration
   - Clear test output
   - Fast test execution
   - Reliable results

2. Failure Handling
   - Clear error messages
   - Quick feedback
   - Easy debugging

## Debugging Tests

### Common Issues
1. Test Failures
   - Check test data
   - Verify environment
   - Review changes

2. Performance Issues
   - Profile tests
   - Optimize setup
   - Reduce dependencies

### Debugging Tools
1. Pytest Options
   ```bash
   # Show print statements
   pytest -s

   # Show extra info
   pytest -v

   # Stop on first failure
   pytest -x
   ```

2. Debugging Techniques
   - Use debugger
   - Add logging
   - Check state

## Test Documentation

### Test Documentation
1. Test Descriptions
   - Clear purpose
   - Expected behavior
   - Edge cases

2. Test Maintenance
   - Update documentation
   - Track changes
   - Document decisions

### Best Practices
1. Documentation
   - Keep docs current
   - Include examples
   - Document setup

2. Maintenance
   - Regular updates
   - Clear structure
   - Easy navigation 