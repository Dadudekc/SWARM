# SWARM Project Setup Guide

## Overview
This guide provides step-by-step instructions for setting up the SWARM project development environment.

## System Requirements

### Hardware Requirements
- CPU: 2+ cores
- RAM: 4GB minimum (8GB recommended)
- Storage: 1GB free space
- Network: Stable internet connection

### Software Requirements
- Operating System:
  - Windows 10/11
  - Linux (Ubuntu 20.04+)
  - macOS 10.15+
- Python 3.8 or higher
- Git
- Discord account (for bot testing)

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/Dadudekc/SWARM.git
cd SWARM
```

### 2. Python Environment Setup
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
   python scripts/init_db.py
   ```

2. Verify database connection
   ```bash
   python scripts/verify_db.py
   ```

## Project Structure

### Directory Layout
```
SWARM/
├── agent_tools/          # Agent-related tools
├── core/                 # Core system components
├── discord_bot/          # Discord bot implementation
├── docs/                 # Documentation
├── runtime/             # Runtime files
├── scripts/             # Utility scripts
├── tests/               # Test files
├── .env                 # Environment variables
├── config.json          # Configuration file
└── requirements.txt     # Python dependencies
```

### Key Components
1. `agent_tools/`
   - Agent communication tools
   - Message handling
   - State management

2. `core/`
   - System core functionality
   - Agent management
   - Resource handling

3. `discord_bot/`
   - Bot implementation
   - Command handlers
   - Event listeners

## Development Setup

### IDE Configuration
1. VS Code Setup
   - Install Python extension
   - Configure linting
   - Set up debugging

2. PyCharm Setup
   - Configure virtual environment
   - Set up run configurations
   - Configure testing

### Testing Environment
1. Install test dependencies
   ```bash
   pip install -r requirements-test.txt
   ```

2. Configure test environment
   ```bash
   python scripts/setup_test_env.py
   ```

## Running the Project

### Start Development Server
1. Start the core system
   ```bash
   python core/main.py
   ```

2. Start the Discord bot
   ```bash
   python discord_bot/bot.py
   ```

### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_file.py

# Run with coverage
python -m pytest --cov=.
```

## Common Issues

### Installation Issues
1. Python version mismatch
   - Verify Python version
   - Update if necessary

2. Dependency conflicts
   - Use virtual environment
   - Check requirements.txt

### Configuration Issues
1. Missing configuration
   - Copy example files
   - Update settings

2. Invalid settings
   - Check format
   - Verify values

### Runtime Issues
1. Database connection
   - Check credentials
   - Verify connection

2. Discord bot
   - Check token
   - Verify permissions

## Next Steps

### Learning Resources
1. Read documentation
2. Review examples
3. Join community

### Development Tasks
1. Set up development environment
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

## Maintenance

### Regular Tasks
1. Update dependencies
2. Run tests
3. Check logs
4. Backup data

### System Updates
1. Pull latest changes
2. Update dependencies
3. Run migrations
4. Test changes 