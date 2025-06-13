# Dream.OS Setup and User Guide

## Overview
This guide provides comprehensive instructions for setting up, running, and using the Dream.OS system.

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

## Starting the System

### 1. Prepare Mailbox Directories
```bash
mkdir -p agent_tools/mailbox/agent0
mkdir -p agent_tools/mailbox/agent1
mkdir -p agent_tools/mailbox/agent2
```

### 2. Configure Discord Bot
1. Copy the environment example:
   ```bash
   cp discord_bot/.env.example discord_bot/.env
   ```
2. Edit the `.env` file with your Discord credentials

### 3. Start Services
1. Run the orchestrator:
   ```bash
   python dreamos/main.py
   ```
2. Start the Discord bot:
   ```bash
   python -m discord_bot.bot
   ```

## Using the System

### Discord Bot Commands
- `!list` – List running agents
- `!resume <id>` – Resume an agent
- `!verify <id>` – Verify agent state
- `!broadcast <msg>` – Send a message to all agents

### Agent Management
1. **Starting Agents**
   - Agents start automatically with the orchestrator
   - Use Discord commands to manage agents
   - Monitor agent status in Discord

2. **Agent Communication**
   - Use Discord for agent commands
   - Monitor agent logs in Discord
   - Check agent status regularly

3. **Troubleshooting**
   - Use `!verify` to check agent state
   - Check logs for errors
   - Restart agents if needed

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
   ```

## Project Structure

### Directory Layout
```
Dream.OS/
├── agent_tools/              # Core agent utilities and tools
│   ├── core/                # Core agent functionality
│   │   ├── autonomy/        # Autonomous operation handlers
│   │   ├── bridge/          # External system bridges
│   │   ├── config/          # Configuration management
│   │   ├── inject/          # Code injection utilities
│   │   ├── mailbox/         # Message handling system
│   │   ├── monitor/         # System monitoring tools
│   │   ├── resume/          # Agent recovery system
│   │   ├── security/        # Security utilities
│   │   └── utils/           # Core utilities
│   ├── devlog/              # Development logging
│   └── swarm/               # Swarm intelligence tools
│       ├── analyzers/       # Code analysis tools
│       ├── browser/         # Browser automation
│       ├── models/          # Data models
│       ├── scanner/         # Project scanning
│       └── utils/           # Swarm utilities
├── config/                  # Configuration files
│   ├── agent_comms/         # Agent communication configs
│   ├── agent_roles/         # Agent role definitions
│   └── onboarding_templates/# Agent onboarding templates
├── docs/                    # Documentation
│   ├── architecture/        # System architecture docs
│   ├── core/               # Core system documentation
│   ├── development/        # Development guides
│   ├── examples/           # Example implementations
│   ├── metrics/            # System metrics
│   ├── onboarding/         # Onboarding guides
│   └── security/           # Security documentation
├── dreamos/                # Main application code
├── scripts/                # Utility scripts
├── tests/                  # Test suite
└── tools/                  # Development tools
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

## Further Reading
- [System Architecture Overview](architecture_overview.md)
- [StealthBrowser API](api/stealth_browser.md)
- [Dreamscribe API](api/dreamscribe.md)
- [Testing Guide](testing.md)
- [Contributing Guide](contributing.md)

## Agent Tools Configuration

### Core Components
1. **Autonomy System**
   - Located in `agent_tools/core/autonomy/`
   - Handles task completion and autonomous operation
   - Key files:
     - `loop.py`: Main autonomy loop implementation
     - `task_completion.py`: Task completion logic

2. **Bridge System**
   - Located in `agent_tools/core/bridge/`
   - Manages integration with external services
   - Key files:
     - `cursor_chatgpt_bridge.py`: ChatGPT integration

3. **Configuration Management**
   - Located in `agent_tools/core/config/`
   - Handles system configuration and validation
   - Key files:
     - `config_loader.py`: Configuration loading
     - `config_validator.py`: Configuration validation
     - `schema.py`: Configuration schemas

4. **Injection System**
   - Located in `agent_tools/core/inject/`
   - Handles code and prompt injection
   - Key files:
     - `captain_prompt.py`: Captain prompt injection
     - `capture_copy_button.py`: Copy button functionality

5. **Mailbox System**
   - Located in `agent_tools/core/mailbox/`
   - Manages agent communication
   - Components:
     - `handlers/`: Message and task handlers
     - `storage/`: Message storage
     - `utils/`: Utility functions including standardization

6. **Monitoring System**
   - Located in `agent_tools/core/monitor/`
   - Provides debugging and monitoring tools
   - Key files:
     - `debug_tools.py`: Debugging utilities
     - `drift_detector.py`: System drift detection
     - `loop_drift_detector.py`: Loop-specific drift detection
     - `project_scanner.py`: Project analysis

7. **Resume System**
   - Located in `agent_tools/core/resume/`
   - Handles agent state recovery
   - Key files:
     - `agent_restart.py`: Agent restart functionality
     - `agent_resumer.py`: Agent state resumption

8. **Security System**
   - Located in `agent_tools/core/security/`
   - Handles security features
   - Key files:
     - `security_overlay_generator.py`: Security overlay generation

9. **Utility System**
   - Located in `agent_tools/core/utils/`
   - Provides core utility functions
   - Key files:
     - `file_metrics.py`: File metrics collection
     - `file_utils.py`: File operations utilities

### Swarm Components
1. **Analyzers**
   - Located in `agent_tools/swarm/analyzers/`
   - Provides code and system analysis
   - Key analyzers:
     - `agent_analyzer.py`: Agent behavior analysis
     - `architectural_analyzer.py`: Architecture analysis
     - `ast_analyzer.py`: Abstract Syntax Tree analysis
     - `code_analyzer.py`: Code quality analysis
     - `dependency_analyzer.py`: Dependency analysis
     - `duplicate_analyzer.py`: Code duplication detection
     - `performance_monitor.py`: Performance monitoring
     - `quality_analyzer.py`: Code quality assessment
     - `structure_analyzer.py`: Code structure analysis
     - `theme_analyzer.py`: Theme analysis
     - `visualize_agent_layout.py`: Agent layout visualization

2. **Browser Integration**
   - Located in `agent_tools/swarm/browser/`
   - Handles web browser automation
   - Key files:
     - `stealth_browser.py`: Stealth browser implementation
     - `cookie_manager.py`: Cookie management
     - `login_handler.py`: Login automation
     - `integration.py`: Browser integration
     - `debug_helper.py`: Browser debugging tools
     - `config.py`: Browser configuration

#### Browser Configuration
1. **Basic Configuration**
   ```python
   # config.json
   {
     "browser": {
       "headless": false,
       "window_size": [1920, 1080],
       "page_load_wait": 30,
       "element_wait": 10,
       "cookies_file": "cookies.json",
       "credentials": {
         "email": "your-email@example.com",
         "password": "your-password"
       }
     }
   }
   ```

2. **Security Settings**
   ```python
   # config.json
   {
     "browser": {
       "security": {
         "cookie_validation": true,
         "session_timeout": 3600,
         "access_logging": true,
         "encryption": {
           "enabled": true,
           "algorithm": "AES-256"
         }
       }
     }
   }
   ```

3. **Performance Settings**
   ```python
   # config.json
   {
     "browser": {
       "performance": {
         "memory_limit": 1024,
         "cpu_limit": 50,
         "network_timeout": 30,
         "retry_attempts": 3
       }
     }
   }
   ```

#### Browser Usage Examples

1. **Basic Browser Operations**:
   ```python
   from agent_tools.swarm.browser import StealthBrowser, DEFAULT_CONFIG

   # Initialize browser
   browser = StealthBrowser(DEFAULT_CONFIG)

   # Start session
   browser.start()

   # Send message
   browser.login_handler.input_codex_message("Your message here")

   # Wait for response
   browser.login_handler.wait_for_codex_response()
   ```

2. **Automated Testing**:
   ```python
   def run_security_scan():
       browser = StealthBrowser(config)
       browser.login_handler.input_codex_message("Scan this code for security issues:")
       # Process security scan results
   ```

3. **Documentation Generation**:
   ```python
   def generate_docs():
       browser = StealthBrowser(config)
       browser.login_handler.input_codex_message("Generate documentation for this API:")
       # Process and format documentation
   ```

4. **Deployment Verification**:
   ```python
   def verify_deployment():
       browser = StealthBrowser(config)
       browser.login_handler.verify_login()
       # Add deployment verification logic
   ```

#### Browser Troubleshooting

1. **Session Issues**:
   ```bash
   # Check session status
   python -m agent_tools.swarm.browser.login_handler check_session

   # Reset session
   python -m agent_tools.swarm.browser.login_handler reset_session

   # Verify cookies
   python -m agent_tools.swarm.browser.cookie_manager verify
   ```

2. **Performance Issues**:
   ```bash
   # Check resource usage
   python -m agent_tools.swarm.browser.debug_helper check_resources

   # Optimize performance
   python -m agent_tools.swarm.browser.debug_helper optimize

   # Clear cache
   python -m agent_tools.swarm.browser.debug_helper clear_cache
   ```

3. **Element Detection Issues**:
   ```bash
   # Debug element detection
   python -m agent_tools.swarm.browser.debug_helper inspect_elements

   # Test selectors
   python -m agent_tools.swarm.browser.debug_helper test_selectors

   # Verify page structure
   python -m agent_tools.swarm.browser.debug_helper verify_structure
   ```

4. **Security Issues**:
   ```bash
   # Check security settings
   python -m agent_tools.swarm.browser.debug_helper check_security

   # Validate credentials
   python -m agent_tools.swarm.browser.login_handler validate_credentials

   # Audit access logs
   python -m agent_tools.swarm.browser.debug_helper audit_logs
   ```

3. **Scanner System**
   - Located in `agent_tools/swarm/scanner/`
   - Provides code scanning capabilities
   - Key files:
     - `core/scanner.py`: Core scanning functionality

4. **Models**
   - Located in `agent_tools/swarm/models/`
   - Contains analysis models
   - Key files:
     - `analysis.py`: Analysis model definitions

5. **Utility Tools**
   - Located in `agent_tools/swarm/utils/`
   - Provides various utility functions
   - Key files:
     - `backup_restore.py`: Backup and restore functionality
     - `cleanup_project.py`: Project cleanup utilities
     - `zip_resolver.py`: ZIP code resolution

### Development Log System
- Located in `agent_tools/devlog/`
- Handles development logging
- Key files:
  - `devlog_pitcher.py`: Development log generation

### System Diagnostics
- Located in `agent_tools/`
- Provides system-wide diagnostics
- Key file:
  - `system_diagnostics.py`: System diagnostic tools

#### Diagnostic Tools

1. **System Diagnostics Dashboard**
   ```bash
   # Run all checks
   python system_diagnostics.py

   # Run specific check
   python system_diagnostics.py --check drift

   # Output in JSON format
   python system_diagnostics.py --format json
   ```

2. **Loop Drift Detection**
   ```bash
   # Check for stalled agents
   python loop_drift_detector.py --root agents/

   # Resume drifted agent
   python loop_drift_detector.py --resume task_agent
   ```

3. **Configuration Validation**
   ```bash
   # Validate all configs
   python config_validator.py --path config/

   # Strict validation
   python config_validator.py --strict
   ```

4. **Duplicate Detection**
   ```bash
   # Find duplicate classes
   python find_duplicate_classes.py --min-similarity 0.9
   ```

#### Configuration Options

1. **System Diagnostics**
   ```python
   # config.json
   {
     "diagnostics": {
       "checks": ["all", "drift", "config", "duplicates"],
       "root": ".",
       "format": "text",
       "output": null,
       "strict": false,
       "min_similarity": 0.8
     }
   }
   ```

2. **Loop Drift Detector**
   ```python
   # config.json
   {
     "drift_detector": {
       "root": ".",
       "timeout": 30,
       "resume_agent": null
     }
   }
   ```

3. **Config Validator**
   ```python
   # config.json
   {
     "config_validator": {
       "path": "config/",
       "strict": false,
       "output": null
     }
   }
   ```

#### Diagnostic Output Examples

1. **Text Output**:
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

2. **JSON Output**:
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

#### Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success, no issues found |
| 1 | Issues found or error occurred |
| 2 | Invalid arguments |

#### Testing Diagnostics

1. **Run All Tests**:
   ```bash
   python -m unittest discover tests/tools/diagnostics
   ```

2. **Run Specific Test**:
   ```bash
   python -m unittest tests/tools/diagnostics/test_loop_drift_detector.py
   ```

#### Notes
- System health score is calculated as a weighted average of individual check scores
- Config validation can be run in strict mode to catch unknown config files
- Duplicate class detection uses a similarity score based on method names and inheritance
- Loop drift detection checks agent activity across multiple files (status, inbox, devlog)

### Setup Steps
1. Install agent tools dependencies:
   ```bash
   cd agent_tools
   pip install -r requirements.txt
   ```

2. Configure agent tools:
   ```bash
   # Create necessary directories
   mkdir -p agent_tools/mailbox/agent0
   mkdir -p agent_tools/mailbox/agent1
   mkdir -p agent_tools/mailbox/agent2

   # Set up monitoring
   python -m agent_tools.core.monitor.debug_tools setup
   ```

3. Initialize analyzers:
   ```bash
   # Set up code analyzers
   python -m agent_tools.swarm.analyzers.agent_analyzer setup
   python -m agent_tools.swarm.analyzers.architectural_analyzer setup
   ```

4. Configure browser integration:
   ```bash
   # Set up stealth browser
   python -m agent_tools.swarm.browser.stealth_browser setup
   ```

### Usage Examples

1. **Running Code Analysis**:
   ```bash
   # Analyze code quality
   python -m agent_tools.swarm.analyzers.quality_analyzer analyze

   # Check dependencies
   python -m agent_tools.swarm.analyzers.dependency_analyzer analyze

   # Detect code duplication
   python -m agent_tools.swarm.analyzers.duplicate_analyzer analyze

   # Visualize agent layout
   python -m agent_tools.swarm.analyzers.visualize_agent_layout generate
   ```

2. **Monitoring System**:
   ```bash
   # Start drift detection
   python -m agent_tools.core.monitor.drift_detector start

   # Run project scan
   python -m agent_tools.core.monitor.project_scanner scan

   # Run system diagnostics
   python -m agent_tools.system_diagnostics run
   ```

3. **Browser Automation**:
   ```bash
   # Start stealth browser
   python -m agent_tools.swarm.browser.stealth_browser start

   # Handle login
   python -m agent_tools.swarm.browser.login_handler login

   # Debug browser issues
   python -m agent_tools.swarm.browser.debug_helper diagnose
   ```

4. **Development Logging**:
   ```bash
   # Generate development log
   python -m agent_tools.devlog.devlog_pitcher generate
   ```

### Troubleshooting

1. **Browser Issues**:
   - If stealth browser fails to start:
     ```bash
     # Check browser configuration
     python -m agent_tools.swarm.browser.config verify
     
     # Run browser diagnostics
     python -m agent_tools.swarm.browser.debug_helper diagnose
     ```

2. **Analysis Issues**:
   - If analyzers fail:
     ```bash
     # Check analyzer configuration
     python -m agent_tools.swarm.analyzers.base_analyzer verify
     
     # Run analyzer diagnostics
     python -m agent_tools.swarm.analyzers.analyze_logs check
     ```

3. **System Issues**:
   - If system diagnostics show problems:
     ```bash
     # Run full system check
     python -m agent_tools.system_diagnostics run --full
     
     # Check specific component
     python -m agent_tools.system_diagnostics check --component <component_name>
     ```

4. **Common Solutions**:
   - Clear cache and temporary files:
     ```bash
     python -m agent_tools.swarm.utils.cleanup_project cleanup
     ```
   - Restore from backup:
     ```bash
     python -m agent_tools.swarm.utils.backup_restore restore
     ```
   - Reset configuration:
     ```bash
     python -m agent_tools.core.config.config_loader reset
     ``` 