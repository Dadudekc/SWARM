# SWARM Project Setup Guide

## Overview
This guide provides comprehensive instructions for setting up and running the SWARM project development environment.

## Prerequisites

### Required Software
- Python 3.8 or higher
- Git
- Discord account (for bot testing)
- Operating System:
  - Windows 10/11
  - Linux (Ubuntu 20.04+)
  - macOS 10.15+

### Hardware Requirements
- CPU: 2+ cores
- RAM: 4GB minimum (8GB recommended)
- Storage: 1GB free space
- Network: Stable internet connection

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/victor-general/Dream.OS.git
cd Dream.OS
```

### 2. Python Environment Setup
1. Create virtual environment
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/Mac
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt  # For development
   ```

### 3. Configuration Setup
1. Create configuration files
   ```bash
   cp config.example.json config.json
   cp .env.example .env
   ```

2. Update configuration
   - Set Discord bot token
   - Configure agent settings
   - Set up logging

### 4. Database Setup
1. Initialize database
   ```bash
   python tools/init_db.py
   ```

2. Verify database connection
   ```bash
   python tools/verify_db.py
   ```

## Virtual Environment Management

### Best Practices
1. **Single Environment**:
   - Use only one virtual environment (`.venv`)
   - Avoid creating multiple environments
   - Keep environment in version control (`.gitignore`)

2. **Dependency Management**:
   - Update `requirements.txt` when adding dependencies
   - Use `pip freeze > requirements.txt` to update
   - Keep test dependencies in `requirements-test.txt`

3. **Environment Updates**:
   ```bash
   # Update all packages
   pip install --upgrade -r requirements.txt

   # Update specific package
   pip install --upgrade package_name

   # Check outdated packages
   pip list --outdated
   ```

4. **Troubleshooting**:
   - If environment is corrupted:
     ```bash
     # Deactivate current environment
     deactivate

     # Remove old environment
     rm -rf .venv

     # Create new environment
     python -m venv .venv
     source .venv/bin/activate  # or .venv\Scripts\activate on Windows

     # Reinstall dependencies
     pip install -r requirements.txt
     ```

## Project Structure

### Directory Layout
```
SWARM/
├── dreamos/             # Core system components including self-discovery
├── tools/              # All utility scripts and automation tools
├── discord_bot/        # Discord bot implementation
├── docs/              # Documentation and examples
│   └── examples/      # Code samples and usage examples
├── config/            # Configuration files and settings
├── runtime/           # Runtime files
├── tests/             # Test files
├── .env               # Environment variables
├── config.json        # Configuration file
└── requirements.txt   # Python dependencies
```

### Key Components
1. `dreamos/`
   - Core system functionality
   - Agent management
   - Self-discovery modules
   - Resource handling

2. `tools/`
   - Development utilities
   - Automation scripts
   - Helper functions
   - Agent tools

3. `discord_bot/`
   - Bot implementation
   - Command handlers
   - Event listeners

## Development Setup

### IDE Configuration

#### VS Code Setup
1. Install Extensions:
   - Python
   - Pylance
   - Python Test Explorer
   - GitLens

2. Configure Settings:
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.testing.pytestEnabled": true,
     "python.testing.unittestEnabled": false,
     "python.testing.nosetestsEnabled": false
   }
   ```

#### PyCharm Setup
1. Configure Project:
   - Set Python interpreter to venv
   - Configure run configurations
   - Set up testing framework

2. Recommended Plugins:
   - Python
   - Git Integration
   - Database Tools
   - Markdown

### Development Tools

#### Code Quality
1. Linting:
   ```bash
   # Run pylint
   pylint dreamos/

   # Run flake8
   flake8 dreamos/
   ```

2. Type Checking:
   ```bash
   # Run mypy
   mypy dreamos/
   ```

3. Formatting:
   ```bash
   # Run black
   black dreamos/

   # Run isort
   isort dreamos/
   ```

#### Testing
1. Run Tests:
   ```bash
   # Run all tests
   python -m pytest

   # Run specific test file
   python -m pytest tests/test_file.py

   # Run with coverage
   python -m pytest --cov=.
   ```

2. Test Configuration:
   ```bash
   # Set up test environment
   python tools/setup_test_env.py
   ```

## Running the Project

### Development Server
1. Start the core system:
   ```bash
   python tools/run_menu.py
   ```

2. Start the Discord bot:
   ```bash
   python discord_bot/bot.py
   ```

### Monitoring
1. Check logs:
   ```bash
   # View system logs
   tail -f logs/system.log

   # View bot logs
   tail -f logs/bot.log
   ```

2. Monitor resources:
   ```bash
   # Check system status
   python tools/check_status.py
   ```

## Troubleshooting

### Common Issues

#### Installation Issues
1. Python version mismatch:
   - Verify Python version: `python --version`
   - Update if necessary

2. Dependency conflicts:
   - Use virtual environment
   - Check requirements.txt
   - Try: `pip install --upgrade -r requirements.txt`

#### Configuration Issues
1. Missing configuration:
   - Copy example files
   - Update settings
   - Verify file permissions

2. Invalid settings:
   - Check format
   - Verify values
   - Check documentation

#### Runtime Issues
1. Database connection:
   - Check credentials
   - Verify connection
   - Check logs

2. Discord bot:
   - Check token
   - Verify permissions
   - Check bot status

### Getting Help
1. Check documentation
2. Search issues
3. Join Discord
4. Contact maintainers

## Maintenance

### Regular Tasks
1. Update dependencies:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. Run tests:
   ```bash
   python -m pytest
   ```

3. Check logs:
   ```bash
   python tools/check_logs.py
   ```

4. Backup data:
   ```bash
   python tools/backup.py
   ```

### System Updates
1. Pull latest changes:
   ```bash
   git pull origin main
   ```

2. Update dependencies:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python tools/migrate.py
   ```

4. Test changes:
   ```bash
   python -m pytest
   ``` 