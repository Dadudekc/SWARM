# Project Scanner

A modular and extensible project analysis tool that provides comprehensive insights into your codebase.

## Features

- **Dependency Analysis**: Track imports, identify circular dependencies, and map project structure
- **Code Quality Metrics**: Calculate cyclomatic complexity, detect code duplication, and measure test coverage
- **Architecture Insights**: Group related files, identify core vs. peripheral components
- **Test Analysis**: Separate test files and analyze test coverage
- **ChatGPT Context**: Generate detailed context for AI-assisted development

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from scanner.scanner import Scanner

# Initialize scanner
scanner = Scanner(project_root="path/to/project")

# Scan project
analysis = scanner.scan_project(
    ignore_patterns=["venv", "__pycache__", "node_modules"],
    categorize_agents=True,
    generate_init=True
)
```

## Project Structure

```
scanner/
├── analyzers/
│   ├── dependency_analyzer.py
│   └── quality_analyzer.py
├── models/
│   └── analysis.py
├── utils/
│   └── file_utils.py
├── scanner.py
└── tests/
    ├── conftest.py
    ├── test_analyzers.py
    ├── test_models.py
    ├── test_scanner.py
    └── test_utils.py
```

## Output Files

- `project_analysis.json`: Complete project analysis
- `test_analysis.json`: Test file analysis
- `chatgpt_project_context.json`: Context for AI-assisted development

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Analyzers

1. Create a new analyzer class in `analyzers/`
2. Implement required methods
3. Add tests in `tests/test_analyzers.py`
4. Update `scanner.py` to use the new analyzer

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License 