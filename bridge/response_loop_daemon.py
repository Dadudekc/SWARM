"""
Response Loop Daemon
------------------
Monitors agent responses and generates new prompts for the ChatGPT bridge.
"""

from bridge.bridge_response_loop_daemon import BridgeResponseLoopDaemon

# Re-export the BridgeResponseLoopDaemon as ResponseLoopDaemon for backward compatibility
ResponseLoopDaemon = BridgeResponseLoopDaemon 
