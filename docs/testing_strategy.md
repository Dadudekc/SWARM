# Testing Strategy

This document outlines how to run the SWARM test suite locally and explains the project's continuous integration setup.

## Local Test Execution

1. Install development and test dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```
2. Run all tests using the provided helper script:
   ```bash
   python run_tests.py
   ```
   This script cleans the pytest cache, applies a short timeout and runs the most commonly used test path by default.
3. To target a specific test file or individual test you can pass the path and optional test name:
   ```bash
   python run_tests.py tests/some_module/test_example.py::test_case
   ```

## Continuous Integration

All pull requests and pushes to the `main` branch automatically execute the test suite via GitHub Actions. The workflow defined in `.github/workflows/test.yml` installs dependencies and runs unit and integration tests with coverage reporting. Results are uploaded to Codecov to track overall coverage trends.

