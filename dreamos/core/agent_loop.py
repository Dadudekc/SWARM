"""
Agent Loop Reader

Monitors agent inboxes and processes incoming prompts.
"""

import os
import json
import time
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
import discord
from discord.ext import commands
import yaml
from dreamos.core.agent_resume_main import AgentResume

logger = logging.getLogger('agent_loop')

class AgentLoop:
    """Handles the main agent processing loop."""
    
    def __init__(self, bot: commands.Bot, agent_id: str):
        self.bot = bot
        self.agent_id = agent_id
        self.inbox_path = f"runtime/agent_memory/{agent_id}/inbox.json"
        self.devlog_path = f"runtime/agent_memory/{agent_id}/devlog.md"
        self.last_processed: Optional[float] = None
        self.is_autonomous = False
        
        # Load channel configuration
        self.channel_config = self.load_channel_config()
        self.channel_id = self.channel_config.get(agent_id)
        
    def load_channel_config(self) -> Dict[str, str]:
        """Load channel configuration from YAML file."""
        try:
            config_path = "runtime/config/agent_channels.yaml"
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return {k: v for k, v in config.items() if isinstance(v, str)}
        except Exception as e:
            logger.error(f"Error loading channel config: {e}")
            return {}
        
    async def start(self):
        """Start the agent processing loop."""
        logger.info(f"Starting agent loop for {self.agent_id}")
        if self.channel_id:
            logger.info(f"Agent {self.agent_id} assigned to channel {self.channel_id}")
        else:
            logger.warning(f"No channel assigned for agent {self.agent_id}")
            
        while True:
            try:
                await self.process_inbox()
                if self.is_autonomous:
                    await self.run_autonomous_cycle()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def run_autonomous_cycle(self):
        """Execute one cycle of autonomous operations."""
        try:
            # 1. Scan for pending tasks
            tasks = await self.scan_pending_tasks()
            
            # 2. Identify optimization opportunities
            optimizations = await self.identify_optimizations()
            
            # 3. Initiate protocol sequences
            protocols = await self.initiate_protocols()
            
            # 4. Engage with other agents
            collaborations = await self.engage_agents()
            
            # 5. Execute autonomous operations
            results = await self.execute_operations()
            
            # 6. Report critical issues or completed objectives
            await self.report_status(tasks, optimizations, protocols, collaborations, results)
            
        except Exception as e:
            logger.error(f"Error in autonomous cycle: {e}")
            await self.log_to_devlog(f"Autonomous cycle error: {str(e)}")
                
    async def process_inbox(self):
        """Process any new messages in the inbox."""
        if not os.path.exists(self.inbox_path):
            return
            
        try:
            with open(self.inbox_path, 'r') as f:
                message = json.load(f)
                
            # Skip if we've already processed this message
            if self.last_processed and message.get('timestamp', 0) <= self.last_processed:
                return
                
            # Process based on message type
            if message['type'] == 'PROMPT':
                await self.handle_prompt(message)
            elif message['type'] == 'RESUME':
                await self.handle_resume(message)
            elif message['type'] == 'DEVLOG_UPDATE':
                await self._handle_devlog_update(message)
                
            self.last_processed = message.get('timestamp', time.time())
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in inbox for {self.agent_id}")
        except Exception as e:
            logger.error(f"Error processing inbox: {e}")

    async def handle_resume(self, message: Dict[str, Any]):
        """Handle a resume message."""
        try:
            content = message.get('content', '')
            if '[RESUME]' in content:
                self.is_autonomous = True
                await self.log_to_devlog("Autonomous protocol activated")
                
                # Send confirmation to Discord
                if self.channel_id:
                    channel = self.bot.get_channel(int(self.channel_id))
                    if channel:
                        embed = discord.Embed(
                            title="🤖 Autonomous Protocol Activated",
                            description=f"Agent {self.agent_id} is now operating autonomously",
                            color=discord.Color.green()
                        )
                        await channel.send(embed=embed)
                        
        except Exception as e:
            logger.error(f"Error handling resume: {e}")
            await self.log_to_devlog(f"Error in resume handling: {str(e)}")
            
    async def scan_pending_tasks(self) -> List[Dict[str, Any]]:
        """Scan for pending tasks in the agent's domain."""
        # TODO: Implement actual task scanning
        return []
        
    async def identify_optimizations(self) -> List[Dict[str, Any]]:
        """Identify opportunities for system optimization."""
        # TODO: Implement optimization detection
        return []
        
    async def initiate_protocols(self) -> List[Dict[str, Any]]:
        """Initiate any pending protocol sequences."""
        # TODO: Implement protocol initiation
        return []
        
    async def engage_agents(self) -> List[Dict[str, Any]]:
        """Engage with other agents for collaborative tasks."""
        # TODO: Implement agent collaboration
        return []
        
    async def execute_operations(self) -> List[Dict[str, Any]]:
        """Execute autonomous operations."""
        # TODO: Implement autonomous operations
        return []
        
    async def report_status(self, tasks: List[Dict], optimizations: List[Dict],
                          protocols: List[Dict], collaborations: List[Dict],
                          results: List[Dict]):
        """Report critical issues or completed objectives."""
        try:
            if self.channel_id:
                channel = self.bot.get_channel(int(self.channel_id))
                if channel:
                    embed = discord.Embed(
                        title=f"🤖 {self.agent_id} Status Report",
                        color=discord.Color.blue()
                    )
                    
                    if tasks:
                        embed.add_field(
                            name="Pending Tasks",
                            value="\n".join(f"• {task.get('description', 'Unknown')}" for task in tasks),
                            inline=False
                        )
                        
                    if optimizations:
                        embed.add_field(
                            name="Optimization Opportunities",
                            value="\n".join(f"• {opt.get('description', 'Unknown')}" for opt in optimizations),
                            inline=False
                        )
                        
                    if protocols:
                        embed.add_field(
                            name="Active Protocols",
                            value="\n".join(f"• {proto.get('name', 'Unknown')}" for proto in protocols),
                            inline=False
                        )
                        
                    if collaborations:
                        embed.add_field(
                            name="Agent Collaborations",
                            value="\n".join(f"• {coll.get('description', 'Unknown')}" for coll in collaborations),
                            inline=False
                        )
                        
                    if results:
                        embed.add_field(
                            name="Operation Results",
                            value="\n".join(f"• {result.get('description', 'Unknown')}" for result in results),
                            inline=False
                        )
                        
                    await channel.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"Error reporting status: {e}")
            await self.log_to_devlog(f"Error in status reporting: {str(e)}")
            
    async def handle_prompt(self, message: Dict[str, Any]):
        """Handle an incoming prompt message."""
        try:
            # Log the prompt to devlog
            await self.log_to_devlog(f"Received prompt: {message['content'][:100]}...")
            
            # Process the prompt (placeholder for actual processing)
            response = await self.process_prompt(message['content'])
            
            # Send response back to Discord
            channel = None
            if 'channel' in message:
                # Use the channel from the message if provided
                channel = self.bot.get_channel(int(message['channel']))
            elif self.channel_id:
                # Otherwise use the configured channel
                channel = self.bot.get_channel(int(self.channel_id))
                
            if channel:
                embed = discord.Embed(
                    title=f"🤖 {self.agent_id} Response",
                    description=response,
                    color=discord.Color.blue()
                )
                await channel.send(embed=embed)
            else:
                logger.error(f"No valid channel found for {self.agent_id}")
                    
            # Log completion
            await self.log_to_devlog(f"Completed prompt processing")
            
        except Exception as e:
            logger.error(f"Error handling prompt: {e}")
            await self.log_to_devlog(f"Error processing prompt: {str(e)}")
            
    async def process_prompt(self, prompt: str) -> str:
        """Process a prompt and generate a response."""
        # TODO: Implement actual prompt processing logic
        return f"Processed prompt: {prompt[:100]}..."
        
    async def log_to_devlog(self, message: str):
        """Add an entry to the agent's devlog."""
        try:
            os.makedirs(os.path.dirname(self.devlog_path), exist_ok=True)
            
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M]")
            entry = f"{timestamp} {message}\n"
            
            with open(self.devlog_path, "a") as f:
                f.write(entry)
                
        except Exception as e:
            logger.error(f"Error writing to devlog: {e}")

    async def _handle_devlog_update(self, message: Dict[str, Any]):
        """Handle a devlog update message."""
        try:
            # Get Discord channel
            channel_id = int(os.getenv('DISCORD_DEVLOG_CHANNEL', 0))
            if not channel_id:
                return
                
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return
                
            # Create embed
            embed = discord.Embed(
                title=f"📜 {self.agent_id} Devlog Update",
                description=message['content'],
                color=discord.Color.blue()
            )
            
            # Add metadata if present
            if message.get('metadata'):
                embed.add_field(
                    name="Metadata",
                    value=f"```json\n{json.dumps(message['metadata'], indent=2)}\n```",
                    inline=False
                )
                
            embed.set_footer(text=f"Category: {message.get('category', 'INFO')}")
            
            # Send to Discord
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error handling devlog update: {e}")

async def start_agent_loops(bot: commands.Bot):
    """Start agent loops for all configured agents."""
    agent_resume = AgentResume()
    tasks = []
    
    for agent_id in agent_resume.coords.keys():
        loop = AgentLoop(bot, agent_id)
        task = asyncio.create_task(loop.start())
        tasks.append(task)
        
    return tasks 