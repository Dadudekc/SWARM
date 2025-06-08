"""
Tests for the Text-to-Speech functionality.
"""

import pytest
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile

from discord_bot.tts import TTSManager

@pytest.fixture
def output_dir(tmp_path):
    """Create a temporary output directory."""
    return tmp_path / "voice_queue"

@pytest.fixture
def tts_manager(output_dir):
    """Create a TTS manager instance."""
    return TTSManager(output_dir)

@pytest.mark.asyncio
async def test_generate_speech_gtts(tts_manager, output_dir):
    """Test speech generation using gTTS."""
    text = "Hello, this is a test"
    output_path = await tts_manager.generate_speech(text, engine="gtts")
    
    assert output_path.exists()
    assert output_path.suffix == '.mp3'
    assert output_path.parent == output_dir

@pytest.mark.asyncio
async def test_generate_speech_edge(tts_manager, output_dir):
    """Test speech generation using Edge TTS."""
    text = "Hello, this is a test"
    voice = "en-US-GuyNeural"
    output_path = await tts_manager.generate_speech(text, engine="edge", voice=voice)
    
    assert output_path.exists()
    assert output_path.suffix == '.mp3'
    assert output_path.parent == output_dir

@pytest.mark.asyncio
async def test_generate_speech_custom_output(tts_manager):
    """Test speech generation with custom output file."""
    text = "Hello, this is a test"
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp:
        output_path = await tts_manager.generate_speech(text, output_file=temp.name)
        assert output_path == Path(temp.name)
        assert output_path.exists()

@pytest.mark.asyncio
async def test_invalid_engine(tts_manager):
    """Test speech generation with invalid engine."""
    with pytest.raises(ValueError, match="Unsupported TTS engine"):
        await tts_manager.generate_speech("test", engine="invalid")

@pytest.mark.asyncio
async def test_list_voices_edge(tts_manager):
    """Test listing Edge TTS voices."""
    voices = await tts_manager.list_voices(engine="edge")
    assert isinstance(voices, list)
    assert len(voices) > 0
    assert all(isinstance(voice, dict) for voice in voices)
    assert all("Name" in voice for voice in voices)

@pytest.mark.asyncio
async def test_list_voices_invalid_engine(tts_manager):
    """Test listing voices with invalid engine."""
    with pytest.raises(ValueError, match="Voice listing not supported"):
        await tts_manager.list_voices(engine="invalid")

@pytest.mark.asyncio
async def test_gtts_error_handling(tts_manager):
    """Test error handling in gTTS generation."""
    with patch('gtts.gTTS.save', side_effect=Exception("Test error")):
        with pytest.raises(Exception, match="Error with gTTS"):
            await tts_manager.generate_speech("test", engine="gtts")

@pytest.mark.asyncio
async def test_edge_tts_error_handling(tts_manager):
    """Test error handling in Edge TTS generation."""
    with patch('edge_tts.Communicate.save', side_effect=Exception("Test error")):
        with pytest.raises(Exception, match="Error with Edge TTS"):
            await tts_manager.generate_speech("test", engine="edge") 
