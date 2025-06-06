"""
Tests for the voice bot functionality.
"""

import pytest
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import discord
from discord_bot.voicebot import VoiceBot, VoiceQueueHandler

@pytest.fixture
def voice_queue_dir(tmp_path):
    """Create a temporary voice queue directory."""
    queue_dir = tmp_path / "voice_queue"
    queue_dir.mkdir()
    return queue_dir

@pytest.fixture
def mock_voice_client():
    """Create a mock voice client."""
    client = AsyncMock(spec=discord.VoiceClient)
    client.is_connected.return_value = True
    return client

@pytest.fixture
def voice_bot(voice_queue_dir):
    """Create a voice bot instance with a temporary queue directory."""
    with patch('discord_bot.voicebot.Path') as mock_path:
        mock_path.return_value = voice_queue_dir
        bot = VoiceBot()
        return bot

@pytest.mark.asyncio
async def test_voice_queue_handler(voice_queue_dir, mock_voice_client):
    """Test the voice queue handler."""
    handler = VoiceQueueHandler(mock_voice_client)
    
    # Create a test audio file
    test_file = voice_queue_dir / "test.mp3"
    test_file.write_bytes(b"dummy audio data")
    
    # Simulate file creation event
    handler.on_created(Mock(src_path=str(test_file), is_directory=False))
    
    # Wait for the queue to process
    await asyncio.sleep(0.1)
    
    # Verify the file was queued
    assert not handler.queue.empty()
    queued_file = await handler.queue.get()
    assert queued_file == str(test_file)

@pytest.mark.asyncio
async def test_join_voice_channel(voice_bot):
    """Test joining a voice channel."""
    # Create mock channel with connect method
    mock_channel = AsyncMock(spec=discord.VoiceChannel)
    mock_channel.name = "Test Channel"
    mock_channel.id = 123456789
    mock_channel.connect = AsyncMock()
    
    # Create mock voice client
    mock_voice_client = AsyncMock(spec=discord.VoiceClient)
    mock_voice_client.is_connected.return_value = True
    mock_channel.connect.return_value = mock_voice_client
    
    # Patch get_channel to return our mock channel
    with patch.object(voice_bot, 'get_channel', return_value=mock_channel) as mock_get_channel:
        success = await voice_bot.join_voice_channel(123456789)
        
        # Verify the behavior
        assert success
        mock_get_channel.assert_called_once_with(123456789)
        mock_channel.connect.assert_called_once()
        assert voice_bot.voice_client == mock_voice_client

@pytest.mark.asyncio
async def test_disconnect(voice_bot, mock_voice_client):
    """Test disconnecting from voice channel."""
    voice_bot.voice_client = mock_voice_client
    
    await voice_bot.disconnect()
    mock_voice_client.disconnect.assert_called_once()
    assert voice_bot.voice_client is None

@pytest.mark.asyncio
async def test_process_voice_queue(voice_bot, voice_queue_dir, mock_voice_client):
    """Test processing the voice queue."""
    voice_bot.voice_client = mock_voice_client
    voice_bot.voice_queue_handler = VoiceQueueHandler(mock_voice_client)
    
    # Create a test audio file
    test_file = voice_queue_dir / "test.mp3"
    test_file.write_bytes(b"dummy audio data")
    
    # Add file to queue
    await voice_bot.voice_queue_handler.queue.put(str(test_file))
    
    # Start processing
    task = asyncio.create_task(voice_bot.process_voice_queue())
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    # Clean up
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
        
    # Verify the file was played
    assert mock_voice_client.play.called 