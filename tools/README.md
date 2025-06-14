# Agent System Diagnostics

A suite of tools for monitoring and maintaining agent system health, configuration integrity, and code quality.

## 🛠️ Tools

| Tool | Purpose | Command |
|------|---------|---------|
| `system_diagnostics.py` | Unified dashboard for all checks | `python system_diagnostics.py` |
| `loop_drift_detector.py` | Detect stalled agents | `python loop_drift_detector.py` |
| `config_validator.py` | Validate configuration files | `python config_validator.py` |
| `find_duplicate_classes.py` | Find duplicate class definitions | `python find_duplicate_classes.py` |

## 📋 Requirements

- Python 3.8+
- Required packages:
  ```bash
  pip install -r requirements.txt
  ```

## 🚀 Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run all checks:
   ```bash
   python system_diagnostics.py
   ```

3. Run specific check:
   ```bash
   python system_diagnostics.py --check drift
   ```

## 📊 Usage Examples

### System Diagnostics Dashboard

Run all checks with default settings:
```bash
python system_diagnostics.py
```

Example output:
```
=== System Diagnostics Report ===
Timestamp: 2024-03-14T12:34:56.789Z
Overall Health Score: 85.5%

Detailed Results:

--- Loop Drift Check ---
✅ No drift detected

--- Config Validation ---
❌ Invalid configs found:
  - agent_config.json:
    * Missing field: memory.max_size
    * Invalid type for agent_id: expected str, got int

--- Duplicate Classes ---
❌ Duplicate classes found:
  - ResponseHandler:
    * agents/handler.py <-> utils/handler.py
      Similarity: 92.5%
```

Run with JSON output:
```bash
python system_diagnostics.py --format json
```

Example JSON output:
```json
{
  "timestamp": "2024-03-14T12:34:56.789Z",
  "health_score": 85.5,
  "checks": {
    "drift": {
      "drift_detected": false,
      "agents": [
        {
          "agent_id": "task_agent",
          "drift": false
        }
      ]
    },
    "config": {
      "valid": ["response_loop_config.json"],
      "invalid": [
        {
          "file": "agent_config.json",
          "errors": [
            "Missing field: memory.max_size",
            "Invalid type for agent_id: expected str, got int"
          ]
        }
      ]
    },
    "duplicates": {
      "ResponseHandler": [
        {
          "file1": "agents/handler.py",
          "file2": "utils/handler.py",
          "similarity": 0.925
        }
      ]
    }
  }
}
```

### Individual Tools

#### Loop Drift Detector

Check for stalled agents:
```bash
python loop_drift_detector.py --root agents/
```

Resume a drifted agent:
```bash
python loop_drift_detector.py --resume task_agent
```

#### Config Validator

Validate all configs:
```bash
python config_validator.py --path config/
```

Strict validation:
```bash
python config_validator.py --strict
```

#### Duplicate Class Finder

Find duplicates with custom similarity threshold:
```bash
python find_duplicate_classes.py --min-similarity 0.9
```

## ⚙️ Configuration

### System Diagnostics

| Option | Description | Default |
|--------|-------------|---------|
| `--check` | Check to run (`all`, `drift`, `config`, `duplicates`) | `all` |
| `--root` | Root directory to analyze | `.` |
| `--format` | Output format (`text`, `json`) | `text` |
| `--output` | Output file path | None |
| `--strict` | Use strict validation for configs | False |
| `--min-similarity` | Minimum similarity for duplicates | 0.8 |

### Loop Drift Detector

| Option | Description | Default |
|--------|-------------|---------|
| `--root` | Root directory containing agents | `.` |
| `--resume` | Agent ID to resume | None |
| `--timeout` | Drift timeout in minutes | 30 |

### Config Validator

| Option | Description | Default |
|--------|-------------|---------|
| `--path` | Path to config directory | `config/` |
| `--strict` | Enforce strict validation | False |
| `--output` | Output file path | None |

### Duplicate Class Finder

| Option | Description | Default |
|--------|-------------|---------|
| `--root` | Root directory to search | `.` |
| `--min-similarity` | Minimum similarity score (0-1) | 0.8 |
| `--output` | Output file path | None |

## 🔍 Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success, no issues found |
| 1 | Issues found or error occurred |
| 2 | Invalid arguments |

## 🧪 Running Tests

Run all tests:
```bash
python -m unittest discover tests/tools/diagnostics
```

Run specific test:
```bash
python -m unittest tests/tools/diagnostics/test_loop_drift_detector.py
```

## 📝 Notes

- The system health score is calculated as a weighted average of individual check scores
- Config validation can be run in strict mode to catch unknown config files
- Duplicate class detection uses a similarity score based on method names and inheritance
- Loop drift detection checks agent activity across multiple files (status, inbox, devlog)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details 