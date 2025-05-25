import os
import pytest
from unittest.mock import Mock
from selenium.webdriver.chrome.options import Options
from social.driver.driver_utils import DriverUtils
from social.driver.session_state import SessionState
from social.driver.proxy_manager import ProxyManager
from social.driver.performance_metrics import PerformanceMetrics

@pytest.fixture(scope="session")
def test_dir():
    """Create and return a test directory path."""
    test_dir = os.path.join(os.path.dirname(__file__), "test_data")
    os.makedirs(test_dir, exist_ok=True)
    return test_dir

@pytest.fixture
def mock_chrome_options():
    """Create mock Chrome options."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return options

@pytest.fixture
def mock_webdriver():
    """Create a mock WebDriver instance with common methods."""
    driver = Mock()
    driver.current_url = "https://example.com"
    driver.title = "Example Domain"
    driver.page_source = "<html><body>Test</body></html>"
    return driver

@pytest.fixture
def session_state(test_dir):
    """Create a SessionState instance for testing."""
    return SessionState(session_id="test_session", profile_dir=test_dir)

@pytest.fixture
def proxy_manager():
    """Create a ProxyManager instance for testing."""
    return ProxyManager()

@pytest.fixture
def performance_metrics():
    """Create a PerformanceMetrics instance for testing."""
    return PerformanceMetrics()

@pytest.fixture
def driver_utils(mock_webdriver):
    """Create a DriverUtils instance with mock driver."""
    return DriverUtils(mock_webdriver)

@pytest.fixture(autouse=True)
def cleanup_test_data(test_dir):
    """Clean up test data after each test."""
    yield
    for file in os.listdir(test_dir):
        file_path = os.path.join(test_dir, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error cleaning up {file_path}: {e}") 