"""
Social Package

Contains social media integration functionality.
"""

from .config.social_config import SocialConfig, social_config
from . import utils
from . import discord_webhooks

__all__ = [
    'SocialConfig',
    'social_config',
    'utils',
    'discord_webhooks',
]
