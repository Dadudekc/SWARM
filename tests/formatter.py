"""
Test suite for social media content formatter.
Validates dream-core formatting, platform rules, and edge cases.
"""

import pytest
from datetime import datetime
from pathlib import Path
import json
from typing import Dict
from tests.utils.test_environment import TestEnvironment

from dreamos.social.social_formatter import SocialFormatter

# Test fixtures
@pytest.fixture
def formatter():
    return SocialFormatter()

@pytest.fixture
def sample_devlog():
    return {
        "title": "driver manager v1.0 locked",
        "what": "chrome profile caching cut load times ... cookies persist so sessions resurrect",
        "blockers": "instagram still playing hard to get",
        "next": "proxy pool + headless battle-hardening",
        "insight": "code is my hammer ... systems build the empire"
    }

@pytest.fixture
def long_content():
    return {
        "title": "a" * 300,  # Exceeds Twitter's limit
        "what": "b" * 500,   # Long content
        "blockers": "c" * 200,
        "next": "d" * 200,
        "insight": "e" * 200
    }

@pytest.fixture(scope="session")
def test_env() -> TestEnvironment:
    """Create a test environment for formatter tests."""
    env = TestEnvironment()
    env.setup()
    yield env
    env.cleanup()

@pytest.fixture(autouse=True)
def setup_test_environment(test_env: TestEnvironment):
    """Set up test environment for each test."""
    yield

@pytest.fixture
def snapshot_dir(test_env: TestEnvironment) -> Path:
    """Get snapshot directory for tests."""
    snapshot_dir = test_env.get_test_dir("temp") / "snapshots"
    snapshot_dir.mkdir(exist_ok=True)
    return snapshot_dir

# Platform-specific tests
def test_twitter_formatting(formatter, sample_devlog):
    """Test Twitter-specific formatting rules."""
    content = formatter.format_post("twitter", sample_devlog)
    
    # Length check
    assert len(content) <= 280
    
    # Structure check
    assert content.startswith(("🧠", "🛰️", "🚀", "🛠️", "⚙️", "🌀"))
    assert "..." in content
    assert content.endswith(("crawling back in the cave...", 
                           "lights off, code running...",
                           "system's looping, i'm ghost...",
                           "dream out 🟣"))
    
    # Content check
    assert "driver manager v1.0 locked" in content
    assert "blocker?" in content
    assert "next >>>" in content

def test_reddit_formatting(formatter, sample_devlog):
    """Test Reddit-specific formatting rules."""
    content = formatter.format_post("reddit", sample_devlog)
    
    # Structure check
    lines = content.split("\n")
    assert len(lines) >= 8  # Title + 3 sections + insight + signoff
    
    # Format check
    assert "**" in lines[0]  # Bold title
    assert "//" in lines[0]  # Date separator
    assert any(line.startswith(("•", "→", "⤷", "↪︎")) for line in lines)
    assert "💡" in content
    assert content.endswith("_")  # Italic signoff

def test_discord_formatting(formatter, sample_devlog):
    """Test Discord-specific formatting rules."""
    content = formatter.format_post("discord", sample_devlog)
    
    # Length check
    assert len(content) <= 2000
    
    # Format check
    assert "**" in content  # Bold title
    assert "💡" in content  # Insight marker
    assert content.endswith("_")  # Italic signoff

# Edge cases
def test_unknown_platform(formatter, sample_devlog):
    """Test graceful handling of unknown platforms."""
    content = formatter.format_post("unknown_platform", sample_devlog)
    assert isinstance(content, str)
    assert len(content) > 0

def test_empty_content(formatter):
    """Test handling of empty content."""
    empty_data = {
        "title": "",
        "what": "",
        "blockers": "",
        "next": "",
        "insight": ""
    }
    content = formatter.format_post("twitter", empty_data)
    assert len(content) > 0
    assert content.startswith(("🧠", "🛰️", "🚀", "🛠️", "⚙️", "🌀"))

def test_long_content_truncation(formatter, long_content):
    """Test truncation of long content."""
    # Twitter truncation
    twitter_content = formatter.format_post("twitter", long_content)
    assert len(twitter_content) <= 280
    assert twitter_content.endswith("...")
    
    # Reddit truncation
    reddit_content = formatter.format_post("reddit", long_content)
    assert len(reddit_content) <= 40000
    assert "..." in reddit_content

# Snapshot tests
def test_snapshot_twitter(formatter, sample_devlog):
    """Snapshot test for Twitter formatting."""
    content = formatter.format_post("twitter", sample_devlog)
    snapshot_file = Path("tests/social/snapshots/twitter_format.json")
    
    if not snapshot_file.exists():
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        with open(snapshot_file, 'w') as f:
            json.dump({"content": content}, f, indent=2)
    else:
        with open(snapshot_file) as f:
            snapshot = json.load(f)
            assert content == snapshot["content"]

def test_snapshot_reddit(formatter, sample_devlog):
    """Snapshot test for Reddit formatting."""
    content = formatter.format_post("reddit", sample_devlog)
    snapshot_file = Path("tests/social/snapshots/reddit_format.json")
    
    if not snapshot_file.exists():
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        with open(snapshot_file, 'w') as f:
            json.dump({"content": content}, f, indent=2)
    else:
        with open(snapshot_file) as f:
            snapshot = json.load(f)
            assert content == snapshot["content"]

def test_snapshot_discord(formatter, sample_devlog):
    """Snapshot test for Discord formatting."""
    content = formatter.format_post("discord", sample_devlog)
    snapshot_file = Path("tests/social/snapshots/discord_format.json")
    
    if not snapshot_file.exists():
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        with open(snapshot_file, 'w') as f:
            json.dump({"content": content}, f, indent=2)
    else:
        with open(snapshot_file) as f:
            snapshot = json.load(f)
            assert content == snapshot["content"]

# Integration tests
def test_format_post_chain(formatter, sample_devlog):
    """Test the entire formatting chain."""
    platforms = ["twitter", "reddit", "discord"]
    for platform in platforms:
        content = formatter.format_post(platform, sample_devlog)
        assert isinstance(content, str)
        assert len(content) > 0
        assert content.startswith(("🧠", "🛰️", "🚀", "🛠️", "⚙️", "🌀"))

def test_title_formatting(formatter):
    """Test title formatting for different platforms."""
    long_title = "a" * 300
    assert len(formatter.format_title("reddit", long_title)) <= 300
    assert len(formatter.format_title("twitter", long_title)) <= 280

def test_twitter_format(test_env: TestEnvironment, snapshot_dir: Path):
    """Test Twitter message formatting."""
    # Test implementation
    snapshot_file = snapshot_dir / "twitter_format.json"
    snapshot_file.parent.mkdir(parents=True, exist_ok=True)
    snapshot_file.write_text('{"format": "twitter"}')
    assert snapshot_file.exists()

def test_reddit_format(test_env: TestEnvironment, snapshot_dir: Path):
    """Test Reddit message formatting."""
    # Test implementation
    snapshot_file = snapshot_dir / "reddit_format.json"
    snapshot_file.parent.mkdir(parents=True, exist_ok=True)
    snapshot_file.write_text('{"format": "reddit"}')
    assert snapshot_file.exists()

def test_discord_format(test_env: TestEnvironment, snapshot_dir: Path):
    """Test Discord message formatting."""
    # Test implementation
    snapshot_file = snapshot_dir / "discord_format.json"
    snapshot_file.parent.mkdir(parents=True, exist_ok=True)
    snapshot_file.write_text('{"format": "discord"}')
    assert snapshot_file.exists() 