"""
Global pytest configuration.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Add tests directory to Python path
tests_dir = project_root / "tests"
sys.path.insert(0, str(tests_dir))

# Add any other necessary paths
sys.path.insert(0, str(project_root / "dreamos"))
sys.path.insert(0, str(project_root / "agent_tools"))

# Import mock discord modules
try:
    from tests.utils.mock_discord import VoiceClient, Gateway, Opus, OpusLoader, VoiceState, VoiceProtocol, VoiceRegion, VoiceRecv, VoiceSend, VoiceUtils, VoiceWebSocket, VoiceWebSocketClient, VoiceWebSocketServer, VoiceWebSocketUtils, VoiceWebSocketVoice, VoiceWebSocketVoiceClient, VoiceWebSocketVoiceServer, VoiceWebSocketVoiceUtils, VoiceWebSocketVoiceWebSocket, VoiceWebSocketVoiceWebSocketClient, VoiceWebSocketVoiceWebSocketServer, VoiceWebSocketVoiceWebSocketUtils
    
    # Set up mock discord modules
    sys.modules['discord.voice_client'] = VoiceClient
    sys.modules['discord.gateway'] = Gateway
    sys.modules['discord.opus'] = Opus
    sys.modules['discord.opus_loader'] = OpusLoader
    sys.modules['discord.voice_state'] = VoiceState
    sys.modules['discord.voice_protocol'] = VoiceProtocol
    sys.modules['discord.voice_region'] = VoiceRegion
    sys.modules['discord.voice_recv'] = VoiceRecv
    sys.modules['discord.voice_send'] = VoiceSend
    sys.modules['discord.voice_utils'] = VoiceUtils
    sys.modules['discord.voice_websocket'] = VoiceWebSocket
    sys.modules['discord.voice_websocket_client'] = VoiceWebSocketClient
    sys.modules['discord.voice_websocket_server'] = VoiceWebSocketServer
    sys.modules['discord.voice_websocket_utils'] = VoiceWebSocketUtils
    sys.modules['discord.voice_websocket_voice'] = VoiceWebSocketVoice
    sys.modules['discord.voice_websocket_voice_client'] = VoiceWebSocketVoiceClient
    sys.modules['discord.voice_websocket_voice_server'] = VoiceWebSocketVoiceServer
    sys.modules['discord.voice_websocket_voice_utils'] = VoiceWebSocketVoiceUtils
    sys.modules['discord.voice_websocket_voice_websocket'] = VoiceWebSocketVoiceWebSocket
    sys.modules['discord.voice_websocket_voice_websocket_client'] = VoiceWebSocketVoiceWebSocketClient
    sys.modules['discord.voice_websocket_voice_websocket_server'] = VoiceWebSocketVoiceWebSocketServer
    sys.modules['discord.voice_websocket_voice_websocket_utils'] = VoiceWebSocketVoiceWebSocketUtils
except ImportError as e:
    print(f"Warning: Could not import mock discord modules: {e}")
    # Create minimal mocks if import fails
    class VoiceClient:
        """Minimal mock of discord.VoiceClient."""
        async def connect(self, *args, **kwargs): pass
        async def disconnect(self, *args, **kwargs): pass
        async def play(self, *args, **kwargs): pass
        def stop(self, *args, **kwargs): pass
    
    class Gateway: pass
    class Opus: pass
    class OpusLoader: pass
    class VoiceState: pass
    class VoiceProtocol: pass
    class VoiceRegion: pass
    class VoiceRecv: pass
    class VoiceSend: pass
    class VoiceUtils: pass
    class VoiceWebSocket: pass
    class VoiceWebSocketClient: pass
    class VoiceWebSocketServer: pass
    class VoiceWebSocketUtils: pass
    class VoiceWebSocketVoice: pass
    class VoiceWebSocketVoiceClient: pass
    class VoiceWebSocketVoiceServer: pass
    class VoiceWebSocketVoiceUtils: pass
    class VoiceWebSocketVoiceWebSocket: pass
    class VoiceWebSocketVoiceWebSocketClient: pass
    class VoiceWebSocketVoiceWebSocketServer: pass
    class VoiceWebSocketVoiceWebSocketUtils: pass
    
    # Set up mock discord modules
    sys.modules['discord.voice_client'] = VoiceClient
    sys.modules['discord.gateway'] = Gateway
    sys.modules['discord.opus'] = Opus
    sys.modules['discord.opus_loader'] = OpusLoader
    sys.modules['discord.voice_state'] = VoiceState
    sys.modules['discord.voice_protocol'] = VoiceProtocol
    sys.modules['discord.voice_region'] = VoiceRegion
    sys.modules['discord.voice_recv'] = VoiceRecv
    sys.modules['discord.voice_send'] = VoiceSend
    sys.modules['discord.voice_utils'] = VoiceUtils
    sys.modules['discord.voice_websocket'] = VoiceWebSocket
    sys.modules['discord.voice_websocket_client'] = VoiceWebSocketClient
    sys.modules['discord.voice_websocket_server'] = VoiceWebSocketServer
    sys.modules['discord.voice_websocket_utils'] = VoiceWebSocketUtils
    sys.modules['discord.voice_websocket_voice'] = VoiceWebSocketVoice
    sys.modules['discord.voice_websocket_voice_client'] = VoiceWebSocketVoiceClient
    sys.modules['discord.voice_websocket_voice_server'] = VoiceWebSocketVoiceServer
    sys.modules['discord.voice_websocket_voice_utils'] = VoiceWebSocketVoiceUtils
    sys.modules['discord.voice_websocket_voice_websocket'] = VoiceWebSocketVoiceWebSocket
    sys.modules['discord.voice_websocket_voice_websocket_client'] = VoiceWebSocketVoiceWebSocketClient
    sys.modules['discord.voice_websocket_voice_websocket_server'] = VoiceWebSocketVoiceWebSocketServer
    sys.modules['discord.voice_websocket_voice_websocket_utils'] = VoiceWebSocketVoiceWebSocketUtils 
