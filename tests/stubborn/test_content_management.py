import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch

class ContentManager:
    """Content management system for social media platforms."""
    
    def __init__(self, platform: str):
        """
        Initialize content manager for a specific platform.
        
        Args:
            platform: The social media platform (e.g., 'twitter', 'facebook')
        """
        self.platform = platform
        self.content_queue: List[Dict[str, Any]] = []
        self.published_content: List[Dict[str, Any]] = []
        
    def create_content(self, content_type: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create new content for the platform.
        
        Args:
            content_type: Type of content (e.g., 'post', 'story', 'reel')
            content: The actual content text/media
            metadata: Additional content metadata
            
        Returns:
            Dict containing created content details
        """
        if not content.strip():
            raise ValueError("Content cannot be empty")
            
        content_item = {
            'id': len(self.content_queue) + 1,
            'type': content_type,
            'content': content,
            'metadata': metadata or {},
            'created_at': datetime.now(),
            'status': 'draft'
        }
        
        self.content_queue.append(content_item)
        return content_item
    
    def validate_content(self, content_id: int) -> bool:
        """
        Validate content against platform rules.
        
        Args:
            content_id: ID of the content to validate
            
        Returns:
            bool: True if content is valid, False otherwise
        """
        content = self._get_content_by_id(content_id)
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
            
        # Platform-specific validation rules
        if self.platform == 'twitter':
            if len(content['content']) > 280:
                return False
        elif self.platform == 'facebook':
            if len(content['content']) > 63206:
                return False
                
        return True
    
    def schedule_content(self, content_id: int, publish_time: datetime) -> Dict[str, Any]:
        """
        Schedule content for publishing.
        
        Args:
            content_id: ID of the content to schedule
            publish_time: When to publish the content
            
        Returns:
            Dict containing scheduling details
        """
        content = self._get_content_by_id(content_id)
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
            
        if not self.validate_content(content_id):
            raise ValueError(f"Content {content_id} failed validation")
            
        if publish_time < datetime.now():
            raise ValueError("Publish time must be in the future")
            
        content['scheduled_time'] = publish_time
        content['status'] = 'scheduled'
        
        return content
    
    def publish_content(self, content_id: int) -> Dict[str, Any]:
        """
        Publish content immediately.
        
        Args:
            content_id: ID of the content to publish
            
        Returns:
            Dict containing published content details
        """
        content = self._get_content_by_id(content_id)
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
            
        if not self.validate_content(content_id):
            raise ValueError(f"Content {content_id} failed validation")
            
        content['published_at'] = datetime.now()
        content['status'] = 'published'
        self.published_content.append(content)
        self.content_queue.remove(content)
        
        return content
    
    def _get_content_by_id(self, content_id: int) -> Optional[Dict[str, Any]]:
        """Get content by ID from queue."""
        for content in self.content_queue:
            if content['id'] == content_id:
                return content
        return None

class TestContentManager:
    """Test suite for content management system."""
    
    @pytest.fixture
    def content_manager(self):
        """Fixture providing a content manager instance."""
        return ContentManager('twitter')
    
    def test_content_creation(self, content_manager):
        """Test content creation functionality."""
        # Test basic content creation
        content = content_manager.create_content(
            content_type='post',
            content='Hello, world!',
            metadata={'tags': ['test', 'hello']}
        )
        
        assert content['type'] == 'post'
        assert content['content'] == 'Hello, world!'
        assert content['metadata']['tags'] == ['test', 'hello']
        assert content['status'] == 'draft'
        
        # Test empty content
        with pytest.raises(ValueError):
            content_manager.create_content('post', '')
    
    def test_content_validation(self, content_manager):
        """Test content validation rules."""
        # Test valid content
        content = content_manager.create_content('post', 'Short post')
        assert content_manager.validate_content(content['id']) is True
        
        # Test content exceeding length limit
        long_content = 'x' * 281  # Twitter's limit is 280
        content = content_manager.create_content('post', long_content)
        assert content_manager.validate_content(content['id']) is False
        
        # Test non-existent content
        with pytest.raises(ValueError):
            content_manager.validate_content(999)
    
    def test_content_scheduling(self, content_manager):
        """Test content scheduling functionality."""
        content = content_manager.create_content('post', 'Scheduled post')
        future_time = datetime.now() + timedelta(hours=1)
        
        # Test valid scheduling
        scheduled = content_manager.schedule_content(content['id'], future_time)
        assert scheduled['status'] == 'scheduled'
        assert scheduled['scheduled_time'] == future_time
        
        # Test scheduling invalid content
        invalid_content = content_manager.create_content('post', 'x' * 281)
        with pytest.raises(ValueError):
            content_manager.schedule_content(invalid_content['id'], future_time)
        
        # Test scheduling in the past
        past_time = datetime.now() - timedelta(hours=1)
        with pytest.raises(ValueError):
            content_manager.schedule_content(content['id'], past_time)
    
    def test_content_publishing(self, content_manager):
        """Test content publishing functionality."""
        content = content_manager.create_content('post', 'Publish test')
        
        # Test valid publishing
        published = content_manager.publish_content(content['id'])
        assert published['status'] == 'published'
        assert 'published_at' in published
        assert len(content_manager.published_content) == 1
        assert len(content_manager.content_queue) == 0
        
        # Test publishing non-existent content
        with pytest.raises(ValueError):
            content_manager.publish_content(999)
        
        # Test publishing invalid content
        invalid_content = content_manager.create_content('post', 'x' * 281)
        with pytest.raises(ValueError):
            content_manager.publish_content(invalid_content['id']) 