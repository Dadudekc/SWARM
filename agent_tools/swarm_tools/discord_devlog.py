#!/usr/bin/env python3
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, Optional
import discord
from discord import Webhook
import aiohttp

class DiscordDevlog:
    """Generalized tool for any agent to update their Discord devlog with narrative and interaction updates."""
    
    def __init__(self, webhook_url: str, agent_name: str = "Agent-1", footer: Optional[str] = None, avatar_url: Optional[str] = None):
        self.logger = logging.getLogger("DiscordDevlog")
        self.webhook_url = webhook_url
        self.agent_name = agent_name
        self.footer = footer or f"{agent_name}"
        self.avatar_url = avatar_url
        
    async def update_devlog(self,
                          content: str,
                          title: Optional[str] = None,
                          agent_states: Optional[Dict] = None,
                          interaction_data: Optional[Dict] = None,
                          memory_state: Optional[Dict] = None) -> bool:
        """Update the Discord devlog with new content."""
        try:
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(self.webhook_url, session=session)
                
                # Create embed
                embed = discord.Embed(
                    title=title or f"{self.agent_name} Update",
                    description=content,
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                # Add agent states if provided
                if agent_states:
                    agent_info = "\n".join([
                        f"**{agent_id}**: {state.get('state', 'Unknown')} - {state.get('focus', 'No focus')}"
                        for agent_id, state in agent_states.items()
                    ])
                    embed.add_field(name="Agent States", value=agent_info, inline=False)
                
                # Add interaction data if provided
                if interaction_data:
                    interaction_info = (
                        f"**Type**: {interaction_data.get('type', 'Unknown')}\n"
                        f"**Agents**: {interaction_data.get('agent1', 'Unknown')} ↔ {interaction_data.get('agent2', 'Unknown')}\n"
                        f"**Context**: {interaction_data.get('context', 'No context')}"
                    )
                    embed.add_field(name="Interaction", value=interaction_info, inline=False)
                
                # Add memory state if provided
                if memory_state:
                    memory_info = "\n".join([
                        f"**{key}**: {value}"
                        for key, value in memory_state.items()
                    ])
                    embed.add_field(name="Memory State", value=memory_info, inline=False)
                
                # Add footer
                embed.set_footer(text=self.footer)
                
                # Send webhook
                await webhook.send(embed=embed, username=self.agent_name, avatar_url=self.avatar_url)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update devlog: {str(e)}")
            return False

async def main():
    parser = argparse.ArgumentParser(description="General Discord Devlog Update Tool for Agents")
    parser.add_argument("--webhook-url", type=str, required=True, help="Discord webhook URL")
    parser.add_argument("--agent-name", type=str, default="Agent-1", help="Name of the agent posting the update")
    parser.add_argument("--footer", type=str, help="Footer text for the embed")
    parser.add_argument("--avatar-url", type=str, help="Avatar URL for the agent")
    parser.add_argument("--content", type=str, required=True, help="Content to post")
    parser.add_argument("--title", type=str, help="Title for the update")
    parser.add_argument("--agent-states", type=str, help="JSON string of agent states")
    parser.add_argument("--interaction-data", type=str, help="JSON string of interaction data")
    parser.add_argument("--memory-state", type=str, help="JSON string of memory state")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("DiscordDevlog")
    
    try:
        # Initialize devlog updater
        devlog = DiscordDevlog(
            webhook_url=args.webhook_url,
            agent_name=args.agent_name,
            footer=args.footer,
            avatar_url=args.avatar_url
        )
        
        # Parse JSON arguments
        agent_states = json.loads(args.agent_states) if args.agent_states else None
        interaction_data = json.loads(args.interaction_data) if args.interaction_data else None
        memory_state = json.loads(args.memory_state) if args.memory_state else None
        
        # Update devlog
        success = await devlog.update_devlog(
            content=args.content,
            title=args.title,
            agent_states=agent_states,
            interaction_data=interaction_data,
            memory_state=memory_state
        )
        
        if success:
            logger.info("Devlog updated successfully")
        else:
            logger.error("Failed to update devlog")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 
