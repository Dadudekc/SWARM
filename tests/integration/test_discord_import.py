#!/usr/bin/env python3
"""Test discord.py imports."""

import sys
import os

def test_discord_import():
    """Test discord.py imports and print results."""
    try:
        import discord
        from discord.ext.commands import Context
        print("✅ discord.py Context import successful")
        print(f"Python path: {sys.path}")
        print(f"discord.py location: {os.path.dirname(discord.__file__)}")
    except ImportError as e:
        print(f"❌ discord.py import failed: {e}")
        print(f"Python path: {sys.path}")
        print(f"Current directory: {os.getcwd()}")

if __name__ == "__main__":
    test_discord_import() 
