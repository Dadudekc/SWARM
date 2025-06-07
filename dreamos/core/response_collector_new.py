"""
Response Collector

Captures and saves Cursor agent responses programmatically for SWARM agents.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import win32gui
import win32con
import win32clipboard
import keyboard
import re
import uiautomation as auto
import pyautogui
import numpy as np
from PIL import Image, ImageChops
import cv2
import os
import sys

from dreamos.core.utils.file_utils import (
    safe_read,
    safe_write,
    load_json,
    save_json,
    ensure_dir
)
from dreamos.core.log_manager import LogManager
from dreamos.core.logging.log_config import LogConfig

# Initialize logging
log_config = LogConfig(
    log_dir="logs",
    max_file_size=1024 * 1024,  # 1MB
    max_age_days=7
)
log_manager = LogManager(log_config)
logger = log_manager

# Rest of the file content... 