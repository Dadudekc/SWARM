"""Mock Discord voice-related classes."""
class VoiceClient:
    """Simplified mock of ``discord.VoiceClient``."""
    async def connect(self, *args, **kwargs):
        pass
    async def disconnect(self, *args, **kwargs):
        pass
    async def play(self, *args, **kwargs):
        pass
    def stop(self, *args, **kwargs):
        pass

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
