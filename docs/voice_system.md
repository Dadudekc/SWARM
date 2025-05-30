# Swarm Voice System Documentation

## Overview

The Swarm Voice System provides text-to-speech and voice channel capabilities for the swarm through Discord. It supports multiple TTS engines, voice channel management, and a queue-based audio playback system.

## Components

### 1. Voice Bot (`discord_bot/voicebot.py`)

The main Discord bot that handles voice channel connections and audio playback.

#### Features:
- Voice channel connection management
- Audio file queue processing
- Discord command interface
- Status monitoring

#### Commands:
- `!join` - Join the voice channel
- `!leave` - Leave the voice channel
- `!say <text>` - Convert text to speech and play it
- `!voices` - List available voices
- `!voice <name>` - Set the voice to use
- `!status` - Show voice bot status

### 2. TTS Manager (`discord_bot/tts.py`)

Handles text-to-speech generation using multiple engines.

#### Supported Engines:
- **gTTS** (Google Text-to-Speech)
  - Free, requires internet
  - Good quality, limited voices
- **Edge TTS** (Microsoft Edge TTS)
  - Free, requires internet
  - High quality, many voices
  - Supports multiple languages

#### Features:
- Multiple TTS engine support
- Voice selection and management
- Custom output file support
- Error handling and logging

### 3. CLI Tool (`discord_bot/voice_cli.py`)

Command-line interface for testing voice functionality.

#### Commands:
- `list` - List available voices
- `generate` - Generate speech from text
- `test` - Test voice playback in Discord

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```env
DISCORD_TOKEN=your_bot_token
VOICE_CHANNEL_ID=your_voice_channel_id
```

3. Run the voice bot:
```bash
python -m discord_bot.voicebot
```

## Usage

### Basic Usage

1. Join a voice channel:
```
!join
```

2. Generate and play speech:
```
!say Hello, I am the swarm
```

3. List available voices:
```
!voices
```

4. Set a specific voice:
```
!voice en-US-GuyNeural
```

5. Check status:
```
!status
```

6. Leave the voice channel:
```
!leave
```

### CLI Testing

1. List available voices:
```bash
python -m discord_bot.voice_cli list
```

2. Generate speech:
```bash
python -m discord_bot.voice_cli generate "Hello, I am the swarm"
```

3. Test playback:
```bash
python -m discord_bot.voice_cli test "Testing voice output"
```

## Integration with Agents

Agents can generate voice output by:

1. Using the TTS Manager directly:
```python
from discord_bot.tts import TTSManager

async def generate_voice(text: str):
    tts = TTSManager()
    output_path = await tts.generate_speech(text)
    # File will be automatically played by the voice bot
```

2. Dropping audio files in the voice queue:
```python
from pathlib import Path

def queue_audio_file(file_path: str):
    queue_dir = Path("runtime/voice_queue")
    # Copy or move file to queue directory
    # Voice bot will automatically play it
```

## File Structure

```
discord_bot/
├── voicebot.py      # Main voice bot implementation
├── tts.py          # Text-to-speech manager
└── voice_cli.py    # CLI testing tool

runtime/
└── voice_queue/    # Audio file queue directory

tests/
├── test_voicebot.py # Voice bot tests
└── test_tts.py     # TTS manager tests
```

## Error Handling

The system includes comprehensive error handling:

1. **TTS Generation Errors**:
   - Invalid engine selection
   - Network connectivity issues
   - File system errors

2. **Voice Channel Errors**:
   - Connection failures
   - Permission issues
   - Channel availability

3. **Playback Errors**:
   - File format issues
   - Audio device problems
   - Queue processing errors

All errors are logged with appropriate context and handled gracefully.

## Best Practices

1. **Voice Selection**:
   - Use Edge TTS for high-quality output
   - Use gTTS as a fallback
   - Test voices before deployment

2. **Queue Management**:
   - Keep queue size reasonable
   - Monitor queue status
   - Clean up processed files

3. **Error Handling**:
   - Always check voice channel connection
   - Handle TTS generation errors
   - Monitor playback status

4. **Resource Management**:
   - Disconnect when not in use
   - Clean up temporary files
   - Monitor system resources

## Troubleshooting

### Common Issues

1. **Bot Can't Join Voice Channel**:
   - Check bot permissions
   - Verify channel ID
   - Ensure channel exists

2. **TTS Generation Fails**:
   - Check internet connection
   - Verify TTS engine availability
   - Check file system permissions

3. **Audio Playback Issues**:
   - Verify audio file format
   - Check voice channel connection
   - Monitor queue status

### Debug Commands

1. Check bot status:
```
!status
```

2. Test voice generation:
```bash
python -m discord_bot.voice_cli test "Test message"
```

3. List available voices:
```bash
python -m discord_bot.voice_cli list
```

## Future Enhancements

1. **Planned Features**:
   - Voice activity detection
   - Real-time voice processing
   - Multiple voice channel support
   - Voice command recognition

2. **Potential Improvements**:
   - Local TTS engine support
   - Voice customization options
   - Advanced queue management
   - Voice synthesis improvements 