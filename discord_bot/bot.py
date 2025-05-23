"""
Discord Bot for Agent Control

Handles Discord bot initialization and command loading.
"""

import os
import discord
from discord.ext import commands
import logging
import asyncio
from dotenv import load_dotenv

from dreamos.core.agent_loop import start_agent_loops

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("No Discord token found. Please set DISCORD_TOKEN in .env file")

# Set up bot with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    
    # Load commands
    await bot.load_extension('discord_bot.commands')
    logger.info('Commands loaded')
    
    # Start agent loops
    agent_tasks = await start_agent_loops(bot)
    logger.info(f'Started {len(agent_tasks)} agent loops')
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="for agent commands"
        )
    )

def run_bot():
    """Run the Discord bot."""
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise

if __name__ == '__main__':
    run_bot() 