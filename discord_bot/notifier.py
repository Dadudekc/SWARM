"""
Unified Discord notification system for Dream.OS.

This module provides a centralized notification system for sending messages,
embeds, and files to Discord channels and webhooks.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import json
from pathlib import Path
from prometheus_client import Counter, Histogram, Gauge

from tests.utils.mock_discord import (
    Webhook,
    Embed,
    File,
    commands,
    Client
)

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics
NOTIFICATION_PROCESSING_TIME = Histogram(
    'discord_notification_processing_seconds',
    'Time spent processing Discord notifications',
    ['notification_type']
)

NOTIFICATION_ERRORS = Counter(
    'discord_notification_errors_total',
    'Total Discord notification errors',
    ['error_type']
)

NOTIFICATION_QUEUE_SIZE = Gauge(
    'discord_notification_queue_size',
    'Current size of notification queue'
)

class DiscordNotifier:
    """Unified Discord notification system.
    
    This class provides a centralized way to send notifications to Discord
    channels and webhooks, with consistent error handling, logging, and
    performance monitoring.
    """
    
    def __init__(self, bot: Client):
        """Initialize the notifier.
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.webhooks: Dict[str, Webhook] = {}
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.logger = logging.getLogger(__name__)
        self._load_webhooks()
        
        # Start notification processor
        asyncio.create_task(self._process_notifications())
    
    def _load_webhooks(self):
        """Load webhook configurations."""
        webhook_path = Path("config/webhooks.json")
        if webhook_path.exists():
            try:
                with open(webhook_path) as f:
                    webhook_configs = json.load(f)
                    for name, url in webhook_configs.items():
                        self.webhooks[name] = Webhook.from_url(url, session=self.bot.http._HTTPClient__session)
            except Exception as e:
                logger.error(f"Error loading webhooks: {e}")
    
    async def _process_notifications(self):
        """Process notifications from the queue."""
        while True:
            try:
                notification = await self.notification_queue.get()
                with NOTIFICATION_PROCESSING_TIME.labels(notification_type=notification['type']).time():
                    await self._send_notification(notification)
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
                NOTIFICATION_ERRORS.labels(error_type=type(e).__name__).inc()
            finally:
                self.notification_queue.task_done()
                NOTIFICATION_QUEUE_SIZE.set(self.notification_queue.qsize())
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send a notification to Discord.
        
        Args:
            notification: Notification data including type, content, and target
        """
        try:
            if notification['type'] == 'channel':
                channel = self.bot.get_channel(notification['channel_id'])
                if channel:
                    await self._send_to_channel(notification['channel_id'], notification['content'], notification.get('embed'), notification.get('files'))
            elif notification['type'] == 'webhook':
                webhook = self.webhooks.get(notification['webhook_name'])
                if webhook:
                    await self._send_to_webhook(notification['webhook_name'], notification['content'], notification.get('embed'), notification.get('files'))
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            NOTIFICATION_ERRORS.labels(error_type=type(e).__name__).inc()
            raise
    
    async def _send_to_channel(self, channel_id: int, content: str, embed: Optional[Embed] = None, files: Optional[List[File]] = None):
        """Send notification to a Discord channel.
        
        Args:
            channel_id: Target Discord channel ID
            content: Message content
            embed: Optional embed to include
            files: Optional list of files to attach
        """
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                self.logger.error(f"Channel {channel_id} not found")
                return
                
            await channel.send(content=content, embed=embed, files=files)
            
        except Exception as e:
            self.logger.error(f"Error sending to channel {channel_id}: {e}")
    
    async def _send_to_webhook(self, webhook_name: str, content: str, embed: Optional[Embed] = None, files: Optional[List[File]] = None):
        """Send notification to a Discord webhook.
        
        Args:
            webhook_name: Target Discord webhook name
            content: Message content
            embed: Optional embed to include
            files: Optional list of files to attach
        """
        try:
            webhook = self.webhooks.get(webhook_name)
            if not webhook:
                self.logger.error(f"Webhook {webhook_name} not found")
                return
                
            await webhook.send(content=content, embed=embed, files=files)
            
        except Exception as e:
            self.logger.error(f"Error sending to webhook {webhook_name}: {e}")
    
    def _create_embed(self, embed_data: Dict[str, Any]) -> Embed:
        """Create a Discord embed from data.
        
        Args:
            embed_data: Embed configuration data
            
        Returns:
            Discord embed object
        """
        embed = Embed(
            title=embed_data.get('title'),
            description=embed_data.get('description'),
            color=embed_data.get('color', 0x00ff00)
        )
        
        if 'fields' in embed_data:
            for field in embed_data['fields']:
                embed.add_field(
                    name=field['name'],
                    value=field['value'],
                    inline=field.get('inline', False)
                )
        
        if 'footer' in embed_data:
            embed.set_footer(text=embed_data['footer'])
        
        if 'timestamp' in embed_data:
            embed.timestamp = datetime.fromisoformat(embed_data['timestamp'])
        
        return embed
    
    async def send_notification(
        self,
        content: str,
        channel_id: Optional[int] = None,
        webhook_name: Optional[str] = None,
        embed: Optional[Embed] = None,
        files: Optional[List[File]] = None
    ):
        """Queue a notification for sending.
        
        Args:
            content: Message content
            channel_id: Target channel ID
            webhook_name: Target webhook name
            embed: Optional embed to include
            files: Optional list of files to attach
        """
        if not channel_id and not webhook_name:
            raise ValueError("Either channel_id or webhook_name must be provided")
        
        notification = {
            'type': 'channel' if channel_id else 'webhook',
            'content': content,
            'embed': embed,
            'files': files,
            'channel_id': channel_id,
            'webhook_name': webhook_name,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.notification_queue.put(notification)
        NOTIFICATION_QUEUE_SIZE.set(self.notification_queue.qsize())
    
    async def send_error(
        self,
        message: str,
        error: Optional[Exception] = None,
        channel_id: Optional[int] = None,
        webhook_name: Optional[str] = None
    ):
        """Send an error notification.
        
        Args:
            message: Error message
            error: Optional exception to include
            channel_id: Target channel ID
            webhook_name: Target webhook name
        """
        embed = Embed(
            title="❌ Error",
            description=message,
            color=0xff0000
        )
        
        if error:
            embed.add_field(name="Error Details", value=str(error), inline=False)
        
        await self.send_notification(
            message,
            channel_id=channel_id,
            webhook_name=webhook_name,
            embed=embed
        )
    
    async def send_success(
        self,
        message: str,
        details: Optional[str] = None,
        channel_id: Optional[int] = None,
        webhook_name: Optional[str] = None
    ):
        """Send a success notification.
        
        Args:
            message: Success message
            details: Optional additional details
            channel_id: Target channel ID
            webhook_name: Target webhook name
        """
        embed = Embed(
            title="✅ Success",
            description=message,
            color=0x00ff00
        )
        
        if details:
            embed.add_field(name="Details", value=details, inline=False)
        
        await self.send_notification(
            message,
            channel_id=channel_id,
            webhook_name=webhook_name,
            embed=embed
        ) 
