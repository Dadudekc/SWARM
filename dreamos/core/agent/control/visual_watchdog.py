"""Visual watchdog utilities for Cursor agents."""

from __future__ import annotations

import hashlib
import time
from typing import Tuple

import pyautogui


def hash_screen_region(region: Tuple[int, int, int, int]) -> str:
    """Capture a region of the screen and return an MD5 hash."""
    screenshot = pyautogui.screenshot(region=region)
    return hashlib.md5(screenshot.tobytes()).hexdigest()


def has_region_stabilized(region: Tuple[int, int, int, int], duration: int = 5) -> bool:
    """Return True if the region is unchanged for the given duration."""
    previous = hash_screen_region(region)
    for _ in range(duration):
        time.sleep(1)
        current = hash_screen_region(region)
        if current != previous:
            return False
    return True
