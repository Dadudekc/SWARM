"""
Voice Bot Module for Swarm Voice Protocol

Handles voice channel connections and audio streaming for the swarm.
"""

import os
import asyncio
import logging
import discord
from discord.ext import commands
from pathlib import Path
import json
from typing import Optional, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .tts import TTSManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('voicebot')

class VoiceQueueHandler(FileSystemEventHandler):
    """Handles file system events for the voice queue directory."""
    
    def __init__(self, voice_client: Optional[discord.VoiceClient] = None):
        self.voice_client = voice_client
        self.queue: asyncio.Queue = asyncio.Queue()
        self.is_playing = False
        
    def on_created(self, event):
        """Called when a new file is created in the voice queue directory."""
        if event.is_directory:
            return
            
        if event.src_path.endswith(('.mp3', '.wav')):
            logger.info(f"New audio file detected: {event.src_path}")
            asyncio.create_task(self.queue.put(event.src_path))

class VoiceBot(commands.Bot):
    """Voice-enabled Discord bot for swarm audio output."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.message_content = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.voice_client: Optional[discord.VoiceClient] = None
        self.voice_queue_handler: Optional[VoiceQueueHandler] = None
        self.voice_queue_dir = Path("runtime/voice_queue")
        self.voice_queue_dir.mkdir(parents=True, exist_ok=True)
        self.tts_manager = TTSManager(self.voice_queue_dir)
        
    async def setup_hook(self):
        """Set up the voice queue handler and observer."""
        self.voice_queue_handler = VoiceQueueHandler()
        observer = Observer()
        observer.schedule(
            self.voice_queue_handler,
            str(self.voice_queue_dir),
            recursive=False
        )
        observer.start()
        
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f'Voice bot logged in as {self.user.name} ({self.user.id})')
        
        # Set up voice queue handler with voice client
        if self.voice_queue_handler:
            self.voice_queue_handler.voice_client = self.voice_client
            
        # Start audio processing loop
        asyncio.create_task(self.process_voice_queue())
        
    async def process_voice_queue(self):
        """Process the voice queue and play audio files."""
        while True:
            try:
                if not self.voice_client or not self.voice_client.is_connected():
                    await asyncio.sleep(1)
                    continue
                    
                if self.voice_queue_handler.is_playing:
                    await asyncio.sleep(0.1)
                    continue
                    
                file_path = await self.voice_queue_handler.queue.get()
                if not os.path.exists(file_path):
                    continue
                    
                self.voice_queue_handler.is_playing = True
                try:
                    self.voice_client.play(
                        discord.FFmpegPCMAudio(file_path),
                        after=lambda e: self._after_playback(e, file_path)
                    )
                except Exception as e:
                    logger.error(f"Error playing audio file {file_path}: {e}")
                    self.voice_queue_handler.is_playing = False
                    
            except Exception as e:
                logger.error(f"Error in voice queue processing: {e}")
                await asyncio.sleep(1)
                
    def _after_playback(self, error: Optional[Exception], file_path: str):
        """Called after an audio file finishes playing."""
        if error:
            logger.error(f"Error during playback of {file_path}: {error}")
            
        self.voice_queue_handler.is_playing = False
        
        # Clean up the audio file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing audio file {file_path}: {e}")
            
    async def join_voice_channel(self, channel_id: int) -> bool:
        """Join a voice channel by ID."""
        try:
            channel = self.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.VoiceChannel):
                logger.error(f"Invalid voice channel ID: {channel_id}")
                return False
                
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.disconnect()
                
            self.voice_client = await channel.connect()
            if self.voice_queue_handler:
                self.voice_queue_handler.voice_client = self.voice_client
            logger.info(f"Connected to voice channel: {channel.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining voice channel: {e}")
            return False
            
    async def disconnect(self):
        """Disconnect from the voice channel."""
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.voice_client = None
            if self.voice_queue_handler:
                self.voice_queue_handler.voice_client = None

def run_voicebot(token: str, voice_channel_id: int):
    """Run the voice bot with the specified token and voice channel."""
    bot = VoiceBot()
    
    @bot.command(name='join')
    async def join(ctx):
        """Join the voice channel."""
        if await bot.join_voice_channel(voice_channel_id):
            await ctx.send("🎙️ Connected to voice channel!")
        else:
            await ctx.send("❌ Failed to connect to voice channel")
            
    @bot.command(name='leave')
    async def leave(ctx):
        """Leave the voice channel."""
        await bot.disconnect()
        await ctx.send("👋 Disconnected from voice channel")
        
    @bot.command(name='say')
    async def say(ctx, *, text: str):
        """Convert text to speech and play it."""
        if not bot.voice_client or not bot.voice_client.is_connected():
            await ctx.send("❌ Not connected to voice channel. Use !join first.")
            return
            
        try:
            # Generate speech
            output_path = await bot.tts_manager.generate_speech(text)
            await ctx.send(f"🎵 Speaking: {text}")
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            await ctx.send("❌ Error generating speech")
            
    @bot.command(name='voices')
    async def voices(ctx):
        """List available voices."""
        try:
            voices = await bot.tts_manager.list_voices()
            voice_list = "\n".join(
                f"- {voice['Name']}: {voice['Gender']} ({voice['Locale']})"
                for voice in voices[:10]  # Show first 10 voices
            )
            await ctx.send(f"Available voices:\n{voice_list}")
        except Exception as e:
            logger.error(f"Error listing voices: {e}")
            await ctx.send("❌ Error listing voices")
            
    @bot.command(name='voice')
    async def voice(ctx, voice_name: str):
        """Set the voice to use for TTS."""
        try:
            voices = await bot.tts_manager.list_voices()
            if voice_name in [v['Name'] for v in voices]:
                # Store voice preference
                bot.tts_manager.current_voice = voice_name
                await ctx.send(f"✅ Voice set to: {voice_name}")
            else:
                await ctx.send("❌ Invalid voice name. Use !voices to list available voices.")
        except Exception as e:
            logger.error(f"Error setting voice: {e}")
            await ctx.send("❌ Error setting voice")
            
    @bot.command(name='status')
    async def status(ctx):
        """Show voice bot status."""
        status = {
            "Connected": bool(bot.voice_client and bot.voice_client.is_connected()),
            "Playing": bool(bot.voice_queue_handler and bot.voice_queue_handler.is_playing),
            "Queue Size": bot.voice_queue_handler.queue.qsize() if bot.voice_queue_handler else 0,
            "Current Voice": getattr(bot.tts_manager, 'current_voice', 'en-US-GuyNeural')
        }
        
        status_text = "\n".join(f"{k}: {v}" for k, v in status.items())
        await ctx.send(f"Voice Bot Status:\n```\n{status_text}\n```")
        
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Error running voice bot: {e}")
        raise

if __name__ == '__main__':
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    TOKEN = os.getenv('DISCORD_TOKEN')
    VOICE_CHANNEL_ID = int(os.getenv('VOICE_CHANNEL_ID', '0'))
    
    if not TOKEN:
        raise ValueError("No Discord token found. Please set DISCORD_TOKEN in .env file")
    if not VOICE_CHANNEL_ID:
        raise ValueError("No voice channel ID found. Please set VOICE_CHANNEL_ID in .env file")
        
    run_voicebot(TOKEN, VOICE_CHANNEL_ID) 