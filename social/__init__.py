"""
Social Package

Contains social media integration functionality.
"""

from .config.social_config import SocialConfig, social_config
from . import utils

__all__ = [
    'SocialConfig',
    'social_config',
    'utils',
]
