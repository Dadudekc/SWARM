# Dream.OS User Guide

This guide provides a quick introduction for new users.

## Starting the System
1. Clone the repository and install dependencies as described in [project_setup_guide.md](project_setup_guide.md).
2. Prepare the mailbox directories:
   ```bash
   mkdir -p agent_tools/mailbox/agent0
   mkdir -p agent_tools/mailbox/agent1
   mkdir -p agent_tools/mailbox/agent2
   ```
3. Copy the environment example from `discord_bot/.env.example` and edit it with your credentials.
4. Run the orchestrator and Discord bot:
   ```bash
   python dreamos/main.py
   python -m discord_bot.bot
   ```

## Common Commands
Use the Discord bot to manage agents:
- `!list` – list running agents
- `!resume <id>` – resume an agent
- `!verify <id>` – verify agent state
- `!broadcast <msg>` – send a message to all agents

## Further Reading
- [System Architecture Overview](architecture_overview.md)
- [StealthBrowser API](api/stealth_browser.md)
- [Dreamscribe API](api/dreamscribe.md)
