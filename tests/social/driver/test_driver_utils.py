import os
import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from social.driver.driver_utils import DriverUtils

@pytest.fixture
def mock_driver():
    """Create a mock WebDriver instance."""
    return Mock()

@pytest.fixture
def driver_utils(mock_driver):
    """Create a DriverUtils instance with mock driver."""
    return DriverUtils(mock_driver)

def test_init(driver_utils, mock_driver):
    """Test initialization."""
    assert driver_utils.driver == mock_driver
    assert driver_utils.wait_timeout == 30

def test_init_custom_timeout(mock_driver):
    """Test initialization with custom timeout."""
    utils = DriverUtils(mock_driver, wait_timeout=60)
    assert utils.wait_timeout == 60

def test_wait_for_element_success(driver_utils, mock_driver):
    """Test successful element wait."""
    mock_element = Mock()
    mock_driver.find_element.return_value = mock_element
    
    element = driver_utils.wait_for_element(By.ID, "test-id")
    assert element == mock_element
    mock_driver.find_element.assert_called_once_with(By.ID, "test-id")

def test_wait_for_element_timeout(driver_utils, mock_driver):
    """Test element wait timeout."""
    mock_driver.find_element.side_effect = TimeoutException("Element not found")
    
    with pytest.raises(TimeoutException):
        driver_utils.wait_for_element(By.ID, "test-id")

def test_is_element_present_true(driver_utils, mock_driver):
    """Test element presence check when element exists."""
    mock_driver.find_element.return_value = Mock()
    assert driver_utils.is_element_present(By.ID, "test-id") is True

def test_is_element_present_false(driver_utils, mock_driver):
    """Test element presence check when element doesn't exist."""
    mock_driver.find_element.side_effect = WebDriverException("Element not found")
    assert driver_utils.is_element_present(By.ID, "test-id") is False

def test_execute_js_success(driver_utils, mock_driver):
    """Test successful JavaScript execution."""
    mock_driver.execute_script.return_value = "result"
    result = driver_utils.execute_js("return document.title")
    assert result == "result"
    mock_driver.execute_script.assert_called_once_with("return document.title")

def test_execute_js_error(driver_utils, mock_driver):
    """Test JavaScript execution error."""
    mock_driver.execute_script.side_effect = WebDriverException("JS error")
    with pytest.raises(WebDriverException):
        driver_utils.execute_js("invalid js")

@patch("os.makedirs")
@patch("os.path.join")
def test_take_screenshot(mock_join, mock_makedirs, driver_utils, mock_driver):
    """Test taking a screenshot."""
    mock_join.return_value = "test/path/screenshot.png"
    mock_driver.save_screenshot.return_value = None
    
    filepath = driver_utils.take_screenshot("screenshot.png")
    assert filepath == "test/path/screenshot.png"
    mock_makedirs.assert_called_once()
    mock_driver.save_screenshot.assert_called_once_with("test/path/screenshot.png")

@patch("os.makedirs")
@patch("os.path.join")
def test_take_screenshot_error(mock_join, mock_makedirs, driver_utils, mock_driver):
    """Test screenshot error handling."""
    mock_join.return_value = "test/path/screenshot.png"
    mock_driver.save_screenshot.side_effect = WebDriverException("Screenshot failed")
    
    with pytest.raises(WebDriverException):
        driver_utils.take_screenshot("screenshot.png") 