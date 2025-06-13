# SWARM Project Setup Guide

## Overview
This guide provides comprehensive instructions for setting up and running the SWARM project development environment.

## Prerequisites

### Required Software
- Python 3.8 or higher
- Git
- Discord account (for bot testing)
- Docker (optional, for containerized development)
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
   pip install -r requirements-dev.txt   # For additional development tools
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
   - Configure monitoring
   - Set up metrics collection

### 4. Database Setup
1. Initialize database
   ```bash
   python tools/init_db.py
   ```

2. Verify database connection
   ```bash
   python tools/verify_db.py
   ```

### 5. Docker Setup (Optional)
1. Build Docker image
   ```bash
   docker build -t swarm-dev .
   ```

2. Run development container
   ```bash
   docker run -it --rm \
     -v $(pwd):/app \
     -p 8000:8000 \
     swarm-dev
   ```

3. Use Docker Compose for services
   ```bash
   docker-compose up -d
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
   - Use `requirements-dev.txt` for development tools

3. **Environment Updates**:
   ```bash
   # Update all packages
   pip install --upgrade -r requirements.txt

   # Update specific package
   pip install --upgrade package_name

   # Check outdated packages
   pip list --outdated

   # Clean up old packages
   pip cache purge
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
├── docker/            # Docker configuration files
├── monitoring/        # Monitoring and metrics configuration
├── .env               # Environment variables
├── config.json        # Configuration file
├── docker-compose.yml # Docker Compose configuration
└── requirements.txt   # Python dependencies
```

### Key Components
1. `dreamos/`
   - Core system functionality
   - Agent management
   - Self-discovery modules
   - Resource handling
   - Monitoring integration

2. `tools/`
   - Development utilities
   - Automation scripts
   - Helper functions
   - Agent tools
   - Monitoring tools

3. `discord_bot/`
   - Bot implementation
   - Command handlers
   - Event listeners
   - Monitoring hooks

4. `monitoring/`
   - Metrics configuration
   - Alert rules
   - Dashboard templates
   - Log aggregation

## Development Setup

### IDE Configuration

#### VS Code Setup
1. Install Extensions:
   - Python
   - Pylance
   - Python Test Explorer
   - GitLens
   - Docker
   - Remote Development
   - Markdown All in One

2. Configure Settings:
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.testing.pytestEnabled": true,
     "python.testing.unittestEnabled": false,
     "python.testing.nosetestsEnabled": false,
     "python.formatting.provider": "black",
     "editor.formatOnSave": true,
     "python.analysis.typeCheckingMode": "basic"
   }
   ```

#### PyCharm Setup
1. Configure Project:
   - Set Python interpreter to venv
   - Configure run configurations
   - Set up testing framework
   - Configure Docker integration

2. Recommended Plugins:
   - Python
   - Git Integration
   - Database Tools
   - Markdown
   - Docker
   - IdeaVim

### Development Tools

#### Code Quality
1. Linting:
   ```bash
   # Run pylint
   pylint dreamos/

   # Run flake8
   flake8 dreamos/

   # Run black
   black dreamos/
   ```

2. Type Checking:
   ```bash
   # Run mypy
   mypy dreamos/

   # Run pyright
   pyright dreamos/
   ```

3. Security Scanning:
   ```bash
   # Run bandit
   bandit -r dreamos/

   # Run safety
   safety check
   ```

## Monitoring Setup

### 1. Metrics Configuration
1. Set up Prometheus:
   ```yaml
   # prometheus.yml
   scrape_configs:
     - job_name: 'swarm'
       scrape_interval: 15s
       static_configs:
         - targets: ['localhost:8000']
   ```

2. Configure Grafana:
   - Import dashboards
   - Set up data sources
   - Configure alerts

### 2. Logging Setup
1. Configure log rotation:
   ```python
   # logging_config.py
   LOGGING_CONFIG = {
       'version': 1,
       'disable_existing_loggers': False,
       'formatters': {
           'standard': {
               'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
           },
       },
       'handlers': {
           'file': {
               'class': 'logging.handlers.RotatingFileHandler',
               'filename': 'logs/swarm.log',
               'maxBytes': 10485760,  # 10MB
               'backupCount': 5,
               'formatter': 'standard'
           },
       },
       'loggers': {
           '': {
               'handlers': ['file'],
               'level': 'INFO',
               'propagate': True
           }
       }
   }
   ```

2. Set up log aggregation:
   - Configure ELK stack
   - Set up log shipping
   - Create log dashboards

## Development Workflow

### 1. Git Workflow
1. Branch naming:
   ```
   feature/feature-name
   bugfix/bug-description
   hotfix/issue-description
   ```

2. Commit messages:
   ```
   feat: add new feature
   fix: fix bug in feature
   docs: update documentation
   test: add test cases
   ```

### 2. Code Review Process
1. Create pull request
2. Run automated checks
3. Request review
4. Address feedback
5. Merge changes

### 3. Release Process
1. Version bump
2. Update changelog
3. Create release branch
4. Run full test suite
5. Deploy to staging
6. Deploy to production

## Troubleshooting

### Common Issues
1. **Import Errors**:
   - Check PYTHONPATH
   - Verify virtual environment
   - Check package installation

2. **Database Issues**:
   - Verify connection string
   - Check database permissions
   - Run database migrations

3. **Docker Issues**:
   - Check Docker daemon
   - Verify port mappings
   - Check volume mounts

4. **Monitoring Issues**:
   - Check metrics endpoint
   - Verify alert rules
   - Check log shipping

### Support Resources
- GitHub Issues
- Documentation
- Discord Channel
- Stack Overflow
- Project Wiki

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