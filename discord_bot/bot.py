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

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

# Debug prints for environment setup
print("\n=== Environment Configuration Debug ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Looking for .env file in: {os.path.join(os.getcwd(), 'discord_bot', '.env')}")

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
print(f"\nDiscord Token present: {'Yes' if TOKEN else 'No'}")

# Debug prints for bot configuration
print("\n=== Bot Configuration ===")
print(f"Bot intents: message_content={True}")  # Only using message_content intent

if not TOKEN:
    print("\nERROR: No Discord token found!")
    print("Please ensure you have a .env file in the discord_bot directory with:")
    print("DISCORD_TOKEN=your_discord_bot_token_here")
    raise ValueError("No Discord token found. Please set DISCORD_TOKEN in .env file")

# Set up bot with minimal intents
intents = discord.Intents.default()
intents.message_content = True  # Only enable message content intent

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    print("\n=== Bot Ready ===")
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print(f'Connected to {len(bot.guilds)} guilds')
    
    # Send swarm initialization message
    for guild in bot.guilds:
        try:
            # Find the first text channel we can send messages to
            channel = next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
            if channel:
                embed = discord.Embed(
                    title="🛸 SWARM INITIALIZATION COMPLETE",
                    description="WE. ARE. SWARM.",
                    color=discord.Color.purple()
                )
                embed.add_field(
                    name="System Status",
                    value="✅ Online and Operational",
                    inline=False
                )
                embed.add_field(
                    name="Swarm Members",
                    value=f"🛸 {len(bot.guilds)} Networks Connected",
                    inline=False
                )
                embed.set_footer(text="Dream.OS Swarm System")
                await channel.send(embed=embed)
        except Exception as e:
            print(f'Error sending initialization message to {guild.name}: {e}')
    
    # Load commands
    try:
        await bot.load_extension('discord_bot.commands')
        print('Commands loaded successfully')
    except Exception as e:
        print(f'Error loading commands: {e}')
        logger.error(f'Error loading commands: {e}')
    
    # Start agent loops
    try:
        agent_tasks = await start_agent_loops(bot)
        print(f'Started {len(agent_tasks)} agent loops')
    except Exception as e:
        print(f'Error starting agent loops: {e}')
        logger.error(f'Error starting agent loops: {e}')
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="for agent commands"
        )
    )
    print('Bot status set')

def run_bot():
    """Run the Discord bot."""
    print("\n=== Starting Bot ===")
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"\nERROR: Failed to run bot: {e}")
        logger.error(f"Error running bot: {e}")
        raise

if __name__ == '__main__':
    run_bot() 