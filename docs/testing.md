# Testing Guide

## Overview
This guide outlines the testing practices, procedures, and strategy for the SWARM project.

## Directory Structure

```
tests/
├── analysis/          # Test analysis tools and utilities
├── logs/             # Test logs and reports
├── utils/            # Test utilities and helpers
├── core/             # Core unit tests
├── integration/      # Integration tests
├── e2e/             # End-to-end tests
├── fixtures/        # Test fixtures
└── conftest.py      # Pytest configuration
```

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

2. Run tests:
   ```bash
   # Run all tests
   python scripts/run_tests.py

   # Run specific test
   python scripts/run_tests.py tests/some_module/test_example.py::test_case

   # Run overnight tests
   python tools/run_overnight_tests.py
   ```

## Test Types

### Unit Tests
- Location: `tests/core/` directory
- Purpose: Test individual components
- Example:
  ```python
  def test_agent_initialization():
      """Test agent initialization."""
      agent = Agent("test_agent")
      assert agent.name == "test_agent"
      assert agent.status == "initialized"
  ```

### Integration Tests
- Location: `tests/integration/` directory
- Purpose: Test component interaction
- Example:
  ```python
  class TestAgentCommunication:
      def test_message_exchange(self):
          """Test message exchange between agents."""
          message = "test message"
          self.agent1.send_message(self.agent2, message)
          assert self.agent2.received_messages[-1] == message
  ```

### End-to-End Tests
- Location: `tests/e2e/` directory
- Purpose: Test complete workflows
- Example:
  ```python
  class TestAgentWorkflow:
      def test_agent_lifecycle(self):
          """Test complete agent lifecycle."""
          agent = self.system.create_agent("test_agent")
          agent.start()
          agent.process_task("test_task")
          agent.stop()
          assert agent.status == "stopped"
  ```

## Test Organization

### Test Utilities
- Location: `tests/utils/` directory
- Purpose: Common test utilities and helpers
- Examples:
  - Test timing utilities
  - Mock data generators
  - Test environment setup

### Test Analysis
- Location: `tests/analysis/` directory
- Purpose: Test analysis and reporting tools
- Examples:
  - Test coverage analysis
  - Performance analysis
  - Test dependency analysis

### Test Logs
- Location: `tests/logs/` directory
- Purpose: Test execution logs and reports
- Contents:
  - Test execution logs
  - Coverage reports
  - Performance reports
  - Error reports

## Best Practices

### Test Structure
1. Follow AAA pattern:
   - Arrange: Set up test data
   - Act: Perform test action
   - Assert: Verify results

2. Test Isolation:
   - Independent tests
   - Clean state
   - No side effects

3. Test Coverage:
   - Critical paths
   - Edge cases
   - Error conditions

### Test Fixtures
```python
@pytest.fixture
def test_agent():
    """Create test agent."""
    agent = Agent("test_agent")
    yield agent
    agent.cleanup()
```

## Continuous Integration

### GitHub Actions
- Runs on every commit
- Runs on pull requests
- Runs on merges to main
- Uploads coverage to Codecov

### Coverage Requirements
- Minimum 80% coverage for new code
- No decrease in overall coverage
- Track coverage trends

## Debugging Tests

### Common Issues
1. Test Failures:
   - Check test data
   - Verify environment
   - Review changes

2. Performance Issues:
   - Profile tests
   - Optimize setup
   - Reduce dependencies

### Debugging Tools
```bash
# Show print statements
pytest -s

# Run with debugger
pytest --pdb

# Show test durations
pytest --durations=0
```

## Test Maintenance

### Regular Tasks
1. Update tests:
   - Keep tests current
   - Update for changes
   - Remove obsolete tests

2. Review coverage:
   - Monitor coverage
   - Add missing tests
   - Remove redundant tests

### Performance
1. Test Quality:
   - Clear test names
   - Proper documentation
   - Meaningful assertions

2. Test Speed:
   - Efficient setup
   - Minimal dependencies
   - Quick execution 