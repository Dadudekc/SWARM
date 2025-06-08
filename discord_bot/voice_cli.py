"""
CLI Tool for Testing Voice Output

Provides command-line interface for testing voice generation and playback.
"""

import os
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Optional
import json

from .tts import TTSManager
from .voicebot import VoiceBot

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('voice_cli')

async def list_voices(engine: str = "edge"):
    """List available voices."""
    tts = TTSManager()
    voices = await tts.list_voices(engine)
    print("\nAvailable voices:")
    for voice in voices:
        print(f"- {voice['Name']}: {voice['Gender']} ({voice['Locale']})")

async def generate_speech(
    text: str,
    engine: str = "gtts",
    voice: str = "en-US-GuyNeural",
    output_file: Optional[str] = None
):
    """Generate speech from text."""
    tts = TTSManager()
    output_path = await tts.generate_speech(text, engine, voice, output_file)
    print(f"\nGenerated speech saved to: {output_path}")

async def test_playback(
    text: str,
    token: str,
    channel_id: int,
    engine: str = "gtts",
    voice: str = "en-US-GuyNeural"
):
    """Test voice playback in Discord."""
    # Generate speech
    tts = TTSManager()
    output_path = await tts.generate_speech(text, engine, voice)
    print(f"\nGenerated speech: {output_path}")
    
    # Start voice bot
    bot = VoiceBot()
    
    @bot.event
    async def on_ready():
        print("\nBot is ready! Connecting to voice channel...")
        if await bot.join_voice_channel(channel_id):
            print("Connected to voice channel!")
            # Wait for file to be played
            await asyncio.sleep(5)
            await bot.disconnect()
            await bot.close()
        else:
            print("Failed to connect to voice channel")
            await bot.close()
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise

def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(description="Voice Testing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List voices command
    list_parser = subparsers.add_parser("list", help="List available voices")
    list_parser.add_argument(
        "--engine",
        default="edge",
        choices=["edge"],
        help="TTS engine to use"
    )
    
    # Generate speech command
    generate_parser = subparsers.add_parser("generate", help="Generate speech from text")
    generate_parser.add_argument("text", help="Text to convert to speech")
    generate_parser.add_argument(
        "--engine",
        default="gtts",
        choices=["gtts", "edge"],
        help="TTS engine to use"
    )
    generate_parser.add_argument(
        "--voice",
        default="en-US-GuyNeural",
        help="Voice to use (for edge-tts)"
    )
    generate_parser.add_argument(
        "--output",
        help="Output file path"
    )
    
    # Test playback command
    test_parser = subparsers.add_parser("test", help="Test voice playback in Discord")
    test_parser.add_argument("text", help="Text to convert to speech")
    test_parser.add_argument(
        "--engine",
        default="gtts",
        choices=["gtts", "edge"],
        help="TTS engine to use"
    )
    test_parser.add_argument(
        "--voice",
        default="en-US-GuyNeural",
        help="Voice to use (for edge-tts)"
    )
    
    args = parser.parse_args()
    
    if args.command == "list":
        asyncio.run(list_voices(args.engine))
    elif args.command == "generate":
        asyncio.run(generate_speech(args.text, args.engine, args.voice, args.output))
    elif args.command == "test":
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        token = os.getenv('DISCORD_TOKEN')
        channel_id = int(os.getenv('VOICE_CHANNEL_ID', '0'))
        
        if not token:
            raise ValueError("No Discord token found. Please set DISCORD_TOKEN in .env file")
        if not channel_id:
            raise ValueError("No voice channel ID found. Please set VOICE_CHANNEL_ID in .env file")
            
        asyncio.run(test_playback(args.text, token, channel_id, args.engine, args.voice))
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 
