"""
Tests for the agent control system.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pyautogui

from dreamos.core.agent_control.agent_control import AgentControl
from dreamos.core.agent_control.coordinate_transformer import CoordinateTransformer

# Test configuration paths
TEST_CONFIG_PATH = Path("tests/test_config/test_coords.json")

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment."""
    TEST_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_CONFIG_PATH.exists():
        TEST_CONFIG_PATH.unlink()

@pytest.fixture
def mock_coords():
    """Provide mock coordinates for testing."""
    return {
        "Agent-1": {
            "initial_spot": {"x": 100, "y": 100},
            "input_box": {"x": 300, "y": 200},
            "copy_button": {"x": 400, "y": 300},
            "response_region": {
                "top_left": {"x": 400, "y": 400},
                "bottom_right": {"x": 600, "y": 600}
            }
        }
    }

@pytest.fixture
def mock_config_file(tmp_path, mock_coords):
    """Create a temporary config file with mock coordinates."""
    config_file = tmp_path / "test_coords.json"
    with open(config_file, 'w') as f:
        json.dump(mock_coords, f)
    return str(config_file)

@pytest.fixture(autouse=True)
def mock_pyautogui():
    """Mock pyautogui functions for testing."""
    with patch('pyautogui.size') as mock_size, \
         patch('pyautogui.moveTo') as mock_move, \
         patch('pyautogui.click') as mock_click:
        mock_size.return_value = (1920, 1080)  # Standard HD resolution
        mock_move.return_value = True
        mock_click.return_value = True
        yield

@pytest.fixture
def agent_control(tmp_path):
    """Create an AgentControl instance for testing."""
    config_path = tmp_path / "test_coords.json"
    return AgentControl(config_path=str(config_path))

@pytest.fixture
def transformer():
    """Create a CoordinateTransformer instance for testing."""
    return CoordinateTransformer(transform_debug=True)

def test_agent_control_initialization(mock_config_file):
    """Test AgentControl initialization."""
    control = AgentControl(mock_config_file)
    assert control.config_path == Path(mock_config_file)
    assert isinstance(control.transformer, CoordinateTransformer)
    assert control.transformer.transform_debug is True

def test_load_coordinates(mock_config_file, mock_coords):
    """Test loading coordinates from config file."""
    control = AgentControl(mock_config_file)
    assert control.coords == mock_coords

def test_load_coordinates_missing_file():
    """Test loading coordinates with missing file."""
    control = AgentControl("nonexistent.json")
    assert control.coords == {}

@patch('pyautogui.moveTo')
def test_move_to_agent(mock_move_to, mock_config_file):
    """Test moving cursor to agent."""
    control = AgentControl(mock_config_file)
    assert control.move_to_agent("Agent-1") is True
    mock_move_to.assert_called_once_with(100, 100)  # Initial spot coordinates

@patch('pyautogui.click')
def test_click_input_box(mock_click, mock_config_file):
    """Test clicking input box."""
    control = AgentControl(mock_config_file)
    assert control.click_input_box("Agent-1") is True
    mock_click.assert_called_once_with(300, 200)  # Input box coordinates

@patch('pyautogui.click')
def test_click_copy_button(mock_click, mock_config_file):
    """Test clicking copy button."""
    control = AgentControl(mock_config_file)
    assert control.click_copy_button("Agent-1") is True
    mock_click.assert_called_once_with(400, 300)  # Copy button coordinates

def test_get_response_region(mock_config_file, mock_coords):
    """Test getting response region."""
    control = AgentControl(mock_config_file)
    region = control.get_response_region("Agent-1")
    assert region == mock_coords["Agent-1"]["response_region"]

def test_get_response_region_missing_agent(mock_config_file):
    """Test getting response region for missing agent."""
    control = AgentControl(mock_config_file)
    assert control.get_response_region("nonexistent") is None

def test_coordinate_transformer_initialization():
    """Test CoordinateTransformer initialization."""
    transformer = CoordinateTransformer(transform_debug=True)
    assert transformer.transform_debug is True
    assert hasattr(transformer, 'screen_width')
    assert hasattr(transformer, 'screen_height')
    assert hasattr(transformer, 'monitors')

@patch('pyautogui.size')
def test_coordinate_transformer_screen_size(mock_size):
    """Test screen size detection."""
    mock_size.return_value = (1920, 1080)
    transformer = CoordinateTransformer()
    assert transformer.screen_width == 1920
    assert transformer.screen_height == 1080

def test_transform_coordinates():
    """Test coordinate transformation."""
    transformer = CoordinateTransformer()
    x, y = transformer.transform_coordinates(100, 200)
    assert isinstance(x, int)
    assert isinstance(y, int)
    assert 0 <= x <= transformer.screen_width
    assert 0 <= y <= transformer.screen_height

def test_transform_coordinate_dict(mock_coords):
    """Test coordinate dictionary transformation."""
    transformer = CoordinateTransformer()
    transformed = transformer.transform_coordinate_dict(mock_coords["Agent-1"])
    assert "message_x" in transformed
    assert "message_y" in transformed
    assert "copy_x" in transformed
    assert "copy_y" in transformed
    assert "response_region" in transformed
    assert transformed["message_x"] == 300  # Input box x
    assert transformed["message_y"] == 200  # Input box y
    assert transformed["copy_x"] == 400  # Copy button x
    assert transformed["copy_y"] == 300  # Copy button y 