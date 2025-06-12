"""Tests for GPT prompt router."""

import pytest
from pathlib import Path
from tests.utils.test_environment import TestEnvironment

@pytest.fixture(scope="session")
def test_env() -> TestEnvironment:
    """Create a test environment for prompt router tests."""
    env = TestEnvironment()
    env.setup()
    yield env
    env.cleanup()

@pytest.fixture(autouse=True)
def setup_test_environment(test_env: TestEnvironment):
    """Set up test environment for each test."""
    yield

@pytest.fixture
def profiles_dir(test_env: TestEnvironment) -> Path:
    """Get profiles directory for tests."""
    profiles_dir = test_env.get_test_dir("temp") / "profiles"
    profiles_dir.mkdir(exist_ok=True)
    return profiles_dir

def test_prompt_router_initialization(test_env: TestEnvironment, profiles_dir: Path):
    """Test prompt router initialization."""
    # Test implementation
    assert profiles_dir.exists()
    assert profiles_dir.is_dir()

def test_decide_prompt_tmp(tmp_path):
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    (profiles / "default.yaml").write_text("prompt: d\ngpt_profile: base")
    router = PromptRouter(profiles_dir=profiles)
    result = router.decide_prompt("http://example.com")
    assert result["prompt"] == "d"
    assert result["gpt_profile"] == "base"
