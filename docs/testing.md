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
├── data/            # Test data files
├── mocks/           # Mock implementations
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
   python scripts/run_overnight.py

   # Run with coverage
   python scripts/run_tests.py --cov

   # Run performance tests
   python scripts/run_tests.py --performance
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

### Performance Tests
- Location: `tests/performance/` directory
- Purpose: Test system performance and scalability
- Example:
  ```python
  class TestAgentPerformance:
      def test_concurrent_agents(self):
          """Test system performance with multiple agents."""
          agents = [self.system.create_agent(f"agent_{i}") for i in range(100)]
          start_time = time.time()
          for agent in agents:
              agent.process_task("heavy_task")
          duration = time.time() - start_time
          assert duration < 5.0  # Should complete within 5 seconds
  ```

## Test Organization

### Test Utilities
- Location: `tests/utils/` directory
- Purpose: Common test utilities and helpers
- Examples:
  - Test timing utilities
  - Mock data generators
  - Test environment setup
  - Performance measurement tools
  - Memory profiling utilities

### Test Analysis
- Location: `tests/analysis/` directory
- Purpose: Test analysis and reporting tools
- Examples:
  - Test coverage analysis
  - Performance analysis
  - Test dependency analysis
  - Memory leak detection
  - CPU profiling

### Test Logs
- Location: `tests/logs/` directory
- Purpose: Test execution logs and reports
- Contents:
  - Test execution logs
  - Coverage reports
  - Performance reports
  - Error reports
  - Memory usage reports
  - CPU usage reports

### Test Data
- Location: `tests/data/` directory
- Purpose: Test data files and fixtures
- Contents:
  - Sample input files
  - Expected output files
  - Test configuration files
  - Mock database dumps
  - Test environment files

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
   - Proper cleanup

3. Test Coverage:
   - Critical paths
   - Edge cases
   - Error conditions
   - Performance boundaries

### Test Fixtures
```python
@pytest.fixture
def test_agent():
    """Create test agent."""
    agent = Agent("test_agent")
    yield agent
    agent.cleanup()

@pytest.fixture(scope="session")
def test_database():
    """Create test database."""
    db = TestDatabase()
    db.setup()
    yield db
    db.teardown()
```

### Mocking Strategies
1. Use appropriate mock types:
   ```python
   # Simple mock
   mock_agent = Mock(spec=Agent)
   
   # Async mock
   mock_async = AsyncMock()
   
   # Property mock
   mock_property = PropertyMock(return_value="value")
   ```

2. Mock external dependencies:
   ```python
   @patch("requests.get")
   def test_api_call(mock_get):
       mock_get.return_value.json.return_value = {"status": "success"}
       result = api_client.get_data()
       assert result["status"] == "success"
   ```

3. Mock time-dependent operations:
   ```python
   @patch("time.time")
   def test_timed_operation(mock_time):
       mock_time.return_value = 1000
       result = timed_operation()
       assert result.timestamp == 1000
   ```

## Continuous Integration

### GitHub Actions
- Runs on every commit
- Runs on pull requests
- Runs on merges to main
- Uploads coverage to Codecov
- Runs performance benchmarks
- Generates test reports

### Coverage Requirements
- Minimum 80% coverage for new code
- No decrease in overall coverage
- Track coverage trends
- Monitor performance metrics
- Track memory usage

## Debugging Tests

### Common Issues
1. Test Failures:
   - Check test data
   - Verify environment
   - Review changes
   - Check dependencies
   - Verify cleanup

2. Performance Issues:
   - Profile tests
   - Optimize setup
   - Reduce dependencies
   - Monitor memory usage
   - Check resource limits

### Debugging Tools
```bash
# Show print statements
pytest -s

# Run with debugger
pytest --pdb

# Show test durations
pytest --durations=0

# Profile memory usage
pytest --memray

# Profile CPU usage
pytest --profile
```

## Test Maintenance

### Regular Tasks
1. Update tests:
   - Keep tests current
   - Update for changes
   - Remove obsolete tests
   - Add new test cases
   - Update test data

2. Review coverage:
   - Monitor coverage
   - Add missing tests
   - Remove redundant tests
   - Update performance baselines
   - Review memory usage

### Performance
1. Test Quality:
   - Clear test names
   - Proper documentation
   - Meaningful assertions
   - Efficient setup
   - Proper cleanup

2. Test Speed:
   - Efficient setup
   - Minimal dependencies
   - Quick execution
   - Parallel execution
   - Resource optimization

## Test Data Management

### Data Generation
1. Use factories:
   ```python
   class AgentFactory:
       @staticmethod
       def create_agent(name=None, status=None):
           return Agent(
               name=name or f"agent_{uuid.uuid4()}",
               status=status or "initialized"
           )
   ```

2. Use data builders:
   ```python
   class TestDataBuilder:
       def __init__(self):
           self.data = {}
       
       def with_name(self, name):
           self.data["name"] = name
           return self
       
       def build(self):
           return TestData(**self.data)
   ```

### Data Cleanup
1. Automatic cleanup:
   ```python
   @pytest.fixture(autouse=True)
   def cleanup_test_data():
       yield
       cleanup_test_files()
       cleanup_test_database()
   ```

2. Manual cleanup:
   ```python
   def test_with_cleanup():
       setup_test_data()
       try:
           run_test()
       finally:
           cleanup_test_data()
   ```

## Performance Testing

### Load Testing
1. Concurrent users:
   ```python
   def test_concurrent_users():
       users = [create_test_user() for _ in range(100)]
       results = run_concurrent_operations(users)
       assert all(r.success for r in results)
   ```

2. Resource usage:
   ```python
   def test_memory_usage():
       with MemoryProfiler() as profiler:
           run_memory_intensive_operation()
       assert profiler.peak_memory < 100 * 1024 * 1024  # 100MB
   ```

### Stress Testing
1. System limits:
   ```python
   def test_system_limits():
       with SystemMonitor() as monitor:
           run_stress_test()
       assert monitor.cpu_usage < 90
       assert monitor.memory_usage < 80
   ```

2. Recovery testing:
   ```python
   def test_system_recovery():
       system = create_test_system()
       system.simulate_failure()
       system.recover()
       assert system.is_healthy()
   ``` 