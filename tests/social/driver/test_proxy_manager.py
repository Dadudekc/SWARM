import time
import pytest
from unittest.mock import patch, Mock
from social.driver.proxy_manager import ProxyManager

@pytest.fixture
def proxy_manager():
    """Create a ProxyManager instance for testing."""
    return ProxyManager()

@pytest.fixture
def mock_proxy_list():
    """Sample proxy list for testing."""
    return ["1.1.1.1:8080", "2.2.2.2:8080", "3.3.3.3:8080"]

def test_init_empty_proxy_list(proxy_manager):
    """Test initialization with empty proxy list."""
    assert proxy_manager.proxy_list == []
    assert proxy_manager.current_proxy is None
    assert proxy_manager.last_rotation == 0

def test_init_with_proxy_list():
    """Test initialization with provided proxy list."""
    proxy_list = ["1.1.1.1:8080", "2.2.2.2:8080"]
    manager = ProxyManager(proxy_list)
    assert manager.proxy_list == proxy_list

def test_add_proxy(proxy_manager):
    """Test adding a new proxy."""
    proxy = "1.1.1.1:8080"
    proxy_manager.add_proxy(proxy)
    assert proxy in proxy_manager.proxy_list

def test_add_duplicate_proxy(proxy_manager):
    """Test adding a duplicate proxy."""
    proxy = "1.1.1.1:8080"
    proxy_manager.add_proxy(proxy)
    proxy_manager.add_proxy(proxy)
    assert proxy_manager.proxy_list.count(proxy) == 1

@patch("requests.get")
def test_validate_proxy_success(mock_get, proxy_manager):
    """Test successful proxy validation."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    assert proxy_manager.validate_proxy("1.1.1.1:8080") is True
    mock_get.assert_called_once()

@patch("requests.get")
def test_validate_proxy_failure(mock_get, proxy_manager):
    """Test failed proxy validation."""
    mock_get.side_effect = Exception("Connection failed")
    assert proxy_manager.validate_proxy("1.1.1.1:8080") is False

def test_get_next_proxy_empty_list(proxy_manager):
    """Test getting next proxy with empty list."""
    assert proxy_manager.get_next_proxy() is None

@patch("time.time")
@patch("random.choice")
@patch.object(ProxyManager, "validate_proxy")
def test_get_next_proxy_rotation(mock_validate, mock_choice, mock_time, proxy_manager, mock_proxy_list):
    """Test proxy rotation logic."""
    proxy_manager.proxy_list = mock_proxy_list
    mock_time.return_value = 1000
    mock_choice.return_value = "1.1.1.1:8080"
    mock_validate.return_value = True
    
    proxy = proxy_manager.get_next_proxy()
    assert proxy == "1.1.1.1:8080"
    assert proxy_manager.current_proxy == proxy
    assert proxy_manager.last_rotation == 1000

@patch("time.time")
@patch("random.choice")
@patch.object(ProxyManager, "validate_proxy")
def test_get_next_proxy_no_valid_proxies(mock_validate, mock_choice, mock_time, proxy_manager, mock_proxy_list):
    """Test behavior when no valid proxies are found."""
    proxy_manager.proxy_list = mock_proxy_list
    mock_time.return_value = 1000
    mock_choice.return_value = "1.1.1.1:8080"
    mock_validate.return_value = False
    
    assert proxy_manager.get_next_proxy() is None

@patch("time.time")
def test_get_next_proxy_rotation_interval(mock_time, proxy_manager, mock_proxy_list):
    """Test proxy rotation interval."""
    proxy_manager.proxy_list = mock_proxy_list
    proxy_manager.current_proxy = "1.1.1.1:8080"
    proxy_manager.last_rotation = 1000
    mock_time.return_value = 1000 + 100  # Less than rotation interval
    
    assert proxy_manager.get_next_proxy() == "1.1.1.1:8080"  # Should return current proxy 