"""
Text-to-Speech Module for Swarm Voice Protocol

Supports multiple TTS engines and voice generation.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile
import asyncio
import uuid
import shutil
from gtts import gTTS
import edge_tts
import aiohttp

logger = logging.getLogger('tts')

class TTSManager:
    """Manages text-to-speech generation using multiple engines."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize TTS manager.
        
        Args:
            output_dir: Directory to save generated audio files
        """
        self.output_dir = output_dir or Path("runtime/voice_queue")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def generate_speech(
        self,
        text: str,
        engine: str = "gtts",
        voice: str = "en-US-GuyNeural",
        output_file: Optional[str] = None
    ) -> Path:
        """Generate speech from text using specified engine.
        
        Args:
            text: Text to convert to speech
            engine: TTS engine to use (gtts, edge)
            voice: Voice to use (for edge-tts)
            output_file: Optional output filename
            
        Returns:
            Path to generated audio file
        """
        # Create temporary file for initial generation
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp:
            temp_path = Path(temp.name)
            
        try:
            # Generate speech to temp file
            if engine.lower() == "gtts":
                await self._generate_gtts(text, temp_path)
            elif engine.lower() == "edge":
                await self._generate_edge_tts(text, voice, temp_path)
            else:
                raise ValueError(f"Unsupported TTS engine: {engine}")
                
            # Determine final output path
            if output_file:
                final_path = Path(output_file)
            else:
                filename = f"{uuid.uuid4()}.mp3"
                final_path = self.output_dir / filename
                
            # Move temp file to final location
            shutil.move(str(temp_path), str(final_path))
            return final_path
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise
            
    async def _generate_gtts(self, text: str, output_path: Path) -> None:
        """Generate speech using Google TTS."""
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(str(output_path))
        except Exception as e:
            logger.error(f"Error with gTTS: {e}")
            raise Exception("Error with gTTS")
            
    async def _generate_edge_tts(self, text: str, voice: str, output_path: Path) -> None:
        """Generate speech using Edge TTS."""
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
        except Exception as e:
            logger.error(f"Error with Edge TTS: {e}")
            raise Exception("Error with Edge TTS")
            
    async def list_voices(self, engine: str = "edge") -> Dict[str, Any]:
        """List available voices for the specified engine."""
        if engine.lower() == "edge":
            return await self._list_edge_voices()
        else:
            raise ValueError(f"Voice listing not supported for engine: {engine}")
            
    async def _list_edge_voices(self) -> Dict[str, Any]:
        """List available Edge TTS voices."""
        try:
            voices = await edge_tts.list_voices()
            return voices
        except Exception as e:
            logger.error(f"Error listing Edge TTS voices: {e}")
            raise 
