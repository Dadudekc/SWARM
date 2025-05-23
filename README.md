# Dream.OS Agent Control System

A sophisticated agent control system with Discord bot integration for remote management and monitoring of autonomous agents, including trading bot integration.

## Project Structure

```
Dream.OS/
├── discord_bot/                 # Discord bot integration
│   ├── bot.py                  # Main bot implementation
│   ├── commands.py             # Bot command handlers
│   ├── config.json            # Bot configuration
│   └── env.example            # Environment variables template
├── dreamos/                    # Core system modules
│   └── core/                  # Core functionality
├── runtime/                    # Runtime files
│   └── config/                # Configuration files
├── Trading_/                   # Trading bot system
│   └── basicbot/              # Main trading bot implementation
│       ├── analysis/          # Strategy analysis tools
│       │   └── strategy_performance.py
│       ├── ml_models/         # Machine learning components
│       │   ├── model_trainer.py
│       │   ├── regime_detector.py
│       │   └── trading_ai.py
│       ├── strategies/        # Trading strategies
│       │   └── adaptive_momentum.py
│       ├── tests/             # Test suite
│       │   ├── test_adaptive_momentum.py
│       │   └── test_trading_api.py
│       ├── tsla_trader/       # Tesla-specific trading module
│       │   ├── config.yaml
│       │   ├── core.py
│       │   └── journal.csv
│       ├── agent_api.py       # Agent interface
│       ├── backtester.py      # Strategy backtesting
│       ├── config.py          # Configuration
│       ├── db_handler.py      # Database operations
│       ├── discord_alerts.py  # Discord notifications
│       ├── dreamos_integration.py  # Dream.OS integration
│       ├── logger.py          # Logging system
│       ├── main_trader.py     # Main trading logic
│       ├── risk_manager.py    # Risk management
│       ├── trade_executor.py  # Trade execution
│       └── trading_api_alpaca.py  # Alpaca API integration
├── agent_resume_main.py       # Main agent control interface
├── agent_cellphone.py         # Cell phone communication system
├── message_processor.py       # Message handling system
├── run_menu.py               # CLI menu interface
├── setup.py                  # Package setup
├── test_cell_phone.py        # Cell phone system tests
└── .gitignore               # Git ignore rules
```

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