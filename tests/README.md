# 🧪 Dream.OS Test Suite

## 📁 Structure

```
tests/
├── core/                  # Core module tests
│   ├── messaging/        # Messaging system tests
│   │   ├── utils/       # Message utilities
│   │   ├── bridge/      # Bridge implementations
│   │   └── handlers/    # Message handlers
│   ├── utils/           # Core utilities
│   └── security/        # Security & auth
├── integration/          # Integration tests
├── unit/                # Unit tests
├── fixtures/            # Shared test fixtures
└── conftest.py         # Global pytest config
```

## 🚀 Running Tests

### Basic Usage

```bash
# Run all tests
python scripts/run_tests.py

# Run specific categories
python scripts/run_tests.py --category unit
python scripts/run_tests.py --category integration
python scripts/run_tests.py --category core

# Run specific core modules
python scripts/run_tests.py --category core --module messaging
python scripts/run_tests.py --category core --module utils
python scripts/run_tests.py --category core --module security
```

### Advanced Options

```bash
# Run with coverage report
python scripts/run_tests.py --coverage

# Run tests in parallel
python scripts/run_tests.py --parallel

# Run in CI mode (strict checks)
python scripts/run_tests.py --ci

# Filter by tags
python scripts/run_tests.py --tag critical
python scripts/run_tests.py --notag slow
```

## 📝 Writing Tests

### File Naming

- All test files must start with `test_`
- Place files in the appropriate category directory
- Use descriptive names: `test_message_validation.py`

### Test Structure

```python
import pytest
from dreamos.core.messaging import Message

@pytest.mark.critical
def test_message_validation():
    """Test message validation logic."""
    message = Message(content="test")
    assert message.is_valid()

@pytest.mark.slow
def test_large_message_processing():
    """Test processing of large messages."""
    # Test implementation
```

### Using Fixtures

```python
from tests.fixtures.messages import sample_message

def test_with_fixture(sample_message):
    """Test using a shared fixture."""
    assert sample_message.is_valid()
```

## 🏷️ Test Tags

Common tags for test categorization:

- `@pytest.mark.critical` - Critical path tests
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.security` - Security-related tests

## 🔧 CI Integration

The test runner supports CI mode with:

- Strict coverage thresholds
- Warning-as-error
- JSON result output
- Parallel execution

```bash
# CI mode with coverage
python scripts/run_tests.py --ci --coverage
```

## 📊 Coverage Requirements

- Core modules: 90% minimum
- Integration tests: 80% minimum
- Unit tests: 95% minimum

## 🛠️ Development Tools

### Quick Test

Use the development shortcut:

```powershell
# Windows
.\tools\dev\quicktest.ps1

# Unix
./tools/dev/quicktest.sh
```

### Test Organization

To reorganize test files:

```bash
python scripts/reorg_tests.py
```

This will:
- Move files to correct locations
- Create necessary `__init__.py` files
- Preserve git history
- Log all changes

## 🔍 Debugging Tests

1. Use `-v` for verbose output:
   ```bash
   python scripts/run_tests.py -v
   ```

2. Check test results in `test_results/`

3. Use pytest's built-in debugger:
   ```python
   pytest.set_trace()  # Add to test for debugging
   ```

## 📚 Best Practices

1. **Test Organization**
   - Keep tests close to implementation
   - Use appropriate category
   - Follow naming conventions

2. **Test Quality**
   - One assertion per test
   - Clear test names
   - Use fixtures for setup
   - Tag appropriately

3. **Performance**
   - Use `@pytest.mark.slow` for long tests
   - Run critical tests first
   - Use parallel execution when possible

4. **Maintenance**
   - Keep fixtures up to date
   - Remove obsolete tests
   - Update documentation 