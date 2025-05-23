# Development Setup Guide

## Overview
This guide provides detailed instructions for setting up your development environment for the SWARM project.

## Prerequisites

### Required Software
1. Python 3.8 or higher
2. Git
3. A code editor (VS Code recommended)
4. Discord account (for bot testing)

### Optional Software
1. Docker (for containerized development)
2. PostgreSQL (for local database)
3. Redis (for caching)

## Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Dadudekc/SWARM.git
cd SWARM
```

### 2. Python Environment
1. Create virtual environment
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

### 3. IDE Setup

#### VS Code
1. Install extensions:
   - Python
   - Pylance
   - Python Test Explorer
   - GitLens
   - Docker

2. Configure settings:
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.formatting.provider": "black",
     "editor.formatOnSave": true
   }
   ```

#### PyCharm
1. Configure virtual environment
2. Set up run configurations
3. Configure testing

## Development Tools

### Code Quality Tools
1. Install development tools
   ```bash
   pip install black pylint mypy pytest pytest-cov
   ```

2. Configure pre-commit hooks
   ```bash
   pre-commit install
   ```

### Testing Tools
1. Install testing tools
   ```bash
   pip install pytest pytest-cov pytest-mock
   ```

2. Configure pytest
   ```ini
   [pytest]
   testpaths = tests
   python_files = test_*.py
   addopts = -v --cov=.
   ```

## Database Setup

### Local Database
1. Install PostgreSQL
2. Create database
   ```sql
   CREATE DATABASE swarm_dev;
   ```

3. Configure connection
   ```bash
   # .env
   DATABASE_URL=postgresql://user:password@localhost:5432/swarm_dev
   ```

### Redis Setup
1. Install Redis
2. Configure connection
   ```bash
   # .env
   REDIS_URL=redis://localhost:6379/0
   ```

## Running the Project

### Development Server
1. Start core system
   ```bash
   python core/main.py
   ```

2. Start Discord bot
   ```bash
   python discord_bot/bot.py
   ```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test
pytest tests/test_file.py
```

## Common Issues

### Environment Issues
1. Python version mismatch
   - Verify Python version
   - Update if necessary

2. Dependency conflicts
   - Use virtual environment
   - Check requirements.txt

### Database Issues
1. Connection errors
   - Check credentials
   - Verify service running

2. Migration issues
   - Run migrations
   - Check logs

## Next Steps

### Learning Resources
1. Read documentation
2. Review examples
3. Join community

### Development Tasks
1. Set up environment
2. Run example code
3. Make small changes
4. Run tests

## Support

### Getting Help
1. Check documentation
2. Search issues
3. Join Discord
4. Contact maintainers

### Reporting Issues
1. Check existing issues
2. Create new issue
3. Provide details
4. Follow template 