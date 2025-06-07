import pytest
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from unittest.mock import Mock, patch

# Platform Interface Definition
class SocialPlatform(ABC):
    """Abstract base class defining the interface for social media platforms."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the platform with configuration."""
        pass
    
    @abstractmethod
    def login(self) -> bool:
        """Authenticate with the platform."""
        pass
    
    @abstractmethod
    def post(self, content: str, media_files: Optional[List[str]] = None) -> bool:
        """Post content to the platform."""
        pass
    
    @abstractmethod
    def create_post(self, title: str, content: str, media_files: Optional[List[str]] = None) -> bool:
        """Create a post with retry logic."""
        pass
    
    @abstractmethod
    def is_logged_in(self) -> bool:
        """Check if currently logged into the platform."""
        pass
    
    @abstractmethod
    def get_memory_updates(self) -> Dict[str, Any]:
        """Get current memory state."""
        pass

# Test Implementation
class TestPlatformInterface:
    """Test suite for platform interface implementation."""
    
    @pytest.fixture
    def mock_platform(self):
        """Fixture providing a mock platform implementation."""
        class MockPlatform(SocialPlatform):
            def __init__(self):
                self.initialized = False
                self.logged_in = False
                self.memory_updates = {
                    "last_action": None,
                    "last_error": None,
                    "retry_history": [],
                    "stats": {
                        "login": 0,
                        "post": 0,
                        "comment": 0,
                        "posts": 0,
                        "comments": 0,
                        "media_uploads": 0,
                        "errors": 0,
                        "retries": 0,
                        "login_attempts": 0
                    }
                }
                self.rate_limiter = Mock()
                self.rate_limiter.check_rate_limit.return_value = True
            
            def initialize(self, config: Dict[str, Any]) -> bool:
                if not isinstance(config, dict):
                    raise ValueError("Config must be a dictionary")
                if not config:
                    raise ValueError("Config cannot be empty")
                if "api_key" not in config or "api_secret" not in config:
                    raise ValueError("Config must contain api_key and api_secret")
                self.initialized = True
                return True
            
            def login(self) -> bool:
                if not self.initialized:
                    raise RuntimeError("Platform not initialized")
                self.logged_in = True
                self.memory_updates["last_action"] = "login"
                self.memory_updates["stats"]["login"] += 1
                return True
            
            def post(self, content: str, media_files: Optional[List[str]] = None) -> bool:
                if not self.logged_in:
                    self.memory_updates["last_error"] = {
                        "error": "Not logged in",
                        "context": "post",
                        "timestamp": datetime.now().isoformat()
                    }
                    return False
                if not self.rate_limiter.check_rate_limit("post"):
                    self.memory_updates["last_error"] = {
                        "error": "Rate limit exceeded",
                        "context": "post",
                        "timestamp": datetime.now().isoformat()
                    }
                    return False
                self.memory_updates["last_action"] = "post"
                self.memory_updates["stats"]["post"] += 1
                return True
            
            def create_post(self, title: str, content: str, media_files: Optional[List[str]] = None) -> bool:
                if not self.logged_in:
                    self.memory_updates["last_error"] = {
                        "error": "Not logged in",
                        "context": "create_post",
                        "timestamp": datetime.now().isoformat()
                    }
                    return False
                if not self.rate_limiter.check_rate_limit("post"):
                    self.memory_updates["last_error"] = {
                        "error": "Rate limit exceeded",
                        "context": "create_post",
                        "timestamp": datetime.now().isoformat()
                    }
                    return False
                self.memory_updates["last_action"] = "post"
                self.memory_updates["stats"]["posts"] += 1
                return True
            
            def is_logged_in(self) -> bool:
                self.memory_updates["last_action"] = "is_logged_in"
                return self.logged_in
            
            def get_memory_updates(self) -> Dict[str, Any]:
                return self.memory_updates
        
        return MockPlatform()
    
    def test_platform_interface_contract(self, mock_platform):
        """Test that platform implementation follows the interface contract."""
        # Verify all abstract methods are implemented
        assert hasattr(mock_platform, 'initialize')
        assert hasattr(mock_platform, 'login')
        assert hasattr(mock_platform, 'post')
        assert hasattr(mock_platform, 'create_post')
        assert hasattr(mock_platform, 'is_logged_in')
        assert hasattr(mock_platform, 'get_memory_updates')
        
        # Verify method signatures
        assert callable(mock_platform.initialize)
        assert callable(mock_platform.login)
        assert callable(mock_platform.post)
        assert callable(mock_platform.create_post)
        assert callable(mock_platform.is_logged_in)
        assert callable(mock_platform.get_memory_updates)
    
    def test_platform_initialization(self, mock_platform):
        """Test platform initialization with various configs."""
        # Test valid config
        valid_config = {"api_key": "test_key", "api_secret": "test_secret"}
        assert mock_platform.initialize(valid_config) is True
        assert mock_platform.initialized is True
        
        # Test invalid config
        with pytest.raises(ValueError):
            mock_platform.initialize("invalid_config")
        
        # Test missing required fields
        with pytest.raises(ValueError):
            mock_platform.initialize({})
        
        # Test missing api_key
        with pytest.raises(ValueError):
            mock_platform.initialize({"api_secret": "test_secret"})
        
        # Test missing api_secret
        with pytest.raises(ValueError):
            mock_platform.initialize({"api_key": "test_key"})
    
    def test_platform_memory_tracking(self, mock_platform):
        """Test platform memory tracking and state management."""
        # Initialize platform
        mock_platform.initialize({"api_key": "test", "api_secret": "test"})
        
        # Test login state tracking
        assert mock_platform.login() is True
        memory = mock_platform.get_memory_updates()
        assert memory["last_action"] == "login"
        assert memory["stats"]["login"] == 1
        
        # Test post state tracking
        assert mock_platform.post("Test post") is True
        memory = mock_platform.get_memory_updates()
        assert memory["last_action"] == "post"
        assert memory["stats"]["post"] == 1
        
        # Test create_post state tracking
        assert mock_platform.create_post("Test", "Test post") is True
        memory = mock_platform.get_memory_updates()
        assert memory["last_action"] == "post"
        assert memory["stats"]["posts"] == 1
        
        # Test is_logged_in state tracking
        assert mock_platform.is_logged_in() is True
        memory = mock_platform.get_memory_updates()
        assert memory["last_action"] == "is_logged_in"
    
    def test_platform_error_handling(self, mock_platform):
        """Test platform error handling and validation."""
        # Test posting without initialization
        with pytest.raises(RuntimeError):
            mock_platform.login()
        
        # Initialize platform
        mock_platform.initialize({"api_key": "test", "api_secret": "test"})
        
        # Test posting without login
        assert mock_platform.post("test") is False
        memory = mock_platform.get_memory_updates()
        assert memory["last_error"]["error"] == "Not logged in"
        assert memory["last_error"]["context"] == "post"
        
        # Test rate limit handling
        mock_platform.logged_in = True
        mock_platform.rate_limiter.check_rate_limit.return_value = False
        assert mock_platform.post("test") is False
        memory = mock_platform.get_memory_updates()
        assert memory["last_error"]["error"] == "Rate limit exceeded"
        assert memory["last_error"]["context"] == "post"
        
        # Test create_post without login
        mock_platform.logged_in = False
        assert mock_platform.create_post("Test", "test") is False
        memory = mock_platform.get_memory_updates()
        assert memory["last_error"]["error"] == "Not logged in"
        assert memory["last_error"]["context"] == "create_post" 