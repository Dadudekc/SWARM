# Dream.OS

[![Tests](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/your-username/your-gist-id/raw/test-status.json)](https://github.com/your-username/Dream.OS/actions)

## Overview

Dream.OS is an AI-powered operating system that provides a seamless interface between users and AI agents. It features:

- Agent control and coordination
- Message processing and routing
- Social media integration
- UI automation and interaction

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/Dream.OS.git
cd Dream.OS

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt  # For development
```

## Usage

```python
from dreamos.core.agent_control import AgentControl
from dreamos.core.message_processor import MessageProcessor

# Initialize components
agent_control = AgentControl()
message_processor = MessageProcessor()

# Process a message
message = "Hello, world!"
response = message_processor.process_message(message)
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dreamos

# Generate HTML coverage report
pytest --cov=dreamos --cov-report=html
```

### Code Style

We use:
- Black for code formatting
- isort for import sorting
- flake8 for linting

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details

# Dream.OS Agent Control System

A sophisticated agent control system with Discord bot integration for remote management and monitoring of autonomous agents, including trading bot integration.

## Project Structure

```
Dream.OS/
├── dreamos/                    # Core system modules
│   ├── core/                  # Core functionality
│   │   ├── agent_control/     # Agent control system
│   │   ├── messaging/         # Message handling
│   │   ├── ui/               # User interface
│   │   └── utils/            # Core utilities
│   ├── agents/               # Agent implementations
│   └── dashboard/            # System dashboard
├── discord_bot/               # Discord bot integration
│   ├── bot.py                # Main bot implementation
│   ├── commands.py           # Bot command handlers
│   └── config.json          # Bot configuration
├── runtime/                   # Runtime files
│   ├── agent_comms/          # Agent communications
│   │   ├── governance/       # System governance
│   │   └── onboarding/       # Agent onboarding
│   └── config/               # Configuration files
├── Trading_/                  # Trading bot system
│   └── basicbot/             # Main trading bot implementation
│       ├── analysis/         # Strategy analysis tools
│       ├── ml_models/        # Machine learning components
│       ├── strategies/       # Trading strategies
│       └── tests/            # Test suite
├── docs/                      # Documentation
│   ├── onboarding/           # Agent onboarding guides
│   ├── development/          # Development guides
│   └── api/                  # API documentation
├── tests/                     # Test suite
│   ├── core/                 # Core system tests
│   ├── agents/               # Agent tests
│   └── integration/          # Integration tests
├── agent_resume_main.py      # Main agent control interface
├── agent_cellphone.py        # Cell phone communication system
├── message_processor.py      # Message handling system
├── run_menu.py              # CLI menu interface
└── setup.py                 # Package setup
```

## Core Components

### 1. Agent Control System
- Remote agent management
- State verification and repair
- Message broadcasting
- System status monitoring

### 2. Messaging System
- Priority-based message queue
- Multiple message types
- Rate limiting
- Message history tracking

### 3. Trading System
- Machine learning-based trading strategies
- Real-time market analysis
- Risk management
- Backtesting capabilities
- Multi-broker support (Alpaca)
- Discord alerts and notifications

### 4. Content Loop Framework
- Autonomous content generation
- Task-based content seeding
- Masterpiece development track
- Multi-domain output streams:
  - Conversation Highlights
  - DevLogs
  - Self-Improvement Reports
  - Entertainment Content

## Documentation

### 1. Onboarding
- [Agent Core Guide](docs/onboarding/01_agent_core.md)
- [Autonomous Operations](docs/onboarding/02_autonomous_operations.md)
- [System Integration](docs/onboarding/03_system_integration.md)
- [Advanced Topics](docs/onboarding/04_advanced_topics.md)
- [Content Loop Framework](docs/onboarding/05_content_loop.md)

### 2. Development
- [Code Style Guide](docs/code_style_guide.md)
- [Testing Guide](docs/testing_guide.md)
- [Project Setup](docs/project_setup_guide.md)
- [Contribution Guide](docs/contribution_guide.md)

### 3. API Reference
- [Core API](docs/api/core.md)
- [Agent API](docs/api/agents.md)
- [Messaging API](docs/api/messaging.md)
- [Trading API](docs/api/trading.md)

## Features

- **Agent Control System**
  - Remote agent management
  - State verification and repair
  - Message broadcasting
  - System status monitoring

- **Discord Bot Integration**
  - Real-time agent control
  - Status monitoring
  - Command-based interface
  - Secure token management

- **Message System**
  - Priority-based message queue
  - Multiple message types
  - Rate limiting
  - Message history tracking

- **Trading System**
  - Machine learning-based trading strategies
  - Real-time market analysis
  - Risk management
  - Backtesting capabilities
  - Multi-broker support (Alpaca)
  - Discord alerts and notifications

## Setup

### Prerequisites

- Python 3.8+
- Discord Bot Token
- Alpaca API credentials (for trading)
- Required Python packages:
  ```bash
  pip install discord.py pyautogui
  pip install -r Trading_/basicbot/requirements.txt
  ```

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Dream.OS
   ```

2. Set up environment variables:
   ```bash
   cp discord_bot/env.example discord_bot/.env
   cp Trading_/basicbot/.env.example Trading_/basicbot/.env
   # Edit both .env files with your tokens and credentials
   ```

3. Install the package:
   ```bash
   pip install -e .
   ```

### Discord Bot Setup

1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot and enable required intents:
   - Message Content Intent
   - Server Members Intent
   - Presence Intent
3. Copy the bot token to your `.env` file
4. Generate an invite link with required permissions:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Read Message History

### Trading Bot Setup

1. Set up Alpaca API credentials in `Trading_/basicbot/.env`
2. Configure trading parameters in `Trading_/basicbot/tsla_trader/config.yaml`
3. Run initial backtest:
   ```bash
   cd Trading_/basicbot
   python backtester.py
   ```

## Usage

### Starting the Discord Bot

```bash
python -m discord_bot.bot
```

### Available Commands

- `!list` - List all available agents
- `!resume <agent_id>` - Resume an agent's operations
- `!verify <agent_id>` - Verify an agent's state
- `!message <agent_id> <message>` - Send a custom message
- `!status` - Get system status and recent messages
- `!broadcast <message>` - Send message to all agents

### Running the Trading Bot

```bash
cd Trading_/basicbot
python start_paper_trading.py  # For paper trading
python main_trader.py         # For live trading
```

### Running the CLI Interface

```bash
python run_menu.py
```

## Development

### Running Tests

```bash
# Cell phone system tests
python test_cell_phone.py

# Trading bot tests
cd Trading_/basicbot
pytest tests/
```

### Adding New Commands

1. Add command to `discord_bot/commands.py`
2. Update cooldowns in `discord_bot/config.json`
3. Test the command locally

### Adding New Trading Strategies

1. Create new strategy in `Trading_/basicbot/strategies/`
2. Add tests in `Trading_/basicbot/tests/`
3. Update configuration in `Trading_/basicbot/tsla_trader/config.yaml`

## Security

- Bot tokens stored in environment variables
- Command cooldowns prevent spam
- Channel restrictions available
- Role-based permissions
- API credentials encrypted
- Risk management controls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here]

## Support

For support, please [contact details or issue tracker information] 