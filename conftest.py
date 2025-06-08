"""
Global pytest configuration.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add tests directory to Python path
tests_dir = project_root / "tests"
sys.path.insert(0, str(tests_dir))

# Add any other necessary paths
sys.path.insert(0, str(project_root / "dreamos"))
sys.path.insert(0, str(project_root / "agent_tools"))

# Import mock discord modules
from tests.utils.mock_discord import VoiceClient

# Set up mock discord voice client
sys.modules['discord.voice_client'] = VoiceClient 
