"""
Reddit Media Handler Module
-------------------------
Provides functionality for handling media uploads to Reddit.
"""

import os
from typing import List, Tuple, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from dreamos.social.utils.media_validator import MediaValidator
from dreamos.social.utils.social_common import SocialMediaUtils

class RedditMediaHandler:
    """Handler for Reddit media operations."""
    
    # Constants
    MAX_IMAGES = 20
    MAX_VIDEOS = 1
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
    
    def __init__(self, driver, utils: SocialMediaUtils, logger=None):
        """Initialize the Reddit media handler.
        
        Args:
            driver: Selenium WebDriver instance
            utils: SocialMediaUtils instance
            logger: Optional logger instance
        """
        self.driver = driver
        self.utils = utils
        self.logger = logger
        self.media_validator = MediaValidator()
        
        # Set supported formats
        self.supported_image_formats = [".jpg", ".jpeg", ".png", ".gif"]
        self.supported_video_formats = [".mp4", ".mov", ".avi"]
        
        # Set max limits
        self.max_images = self.MAX_IMAGES
        self.max_videos = self.MAX_VIDEOS
        self.max_video_size = self.MAX_VIDEO_SIZE

    def validate_media(self, files: List[str], is_video: bool = False) -> Tuple[bool, Optional[str]]:
        """Validate media files based on type and count."""
        if not files:
            return True, None
            
        # Check file existence
        for file in files:
            if not os.path.exists(file):
                return False, f"File not found: {file}"
                
        # Check file count
        max_files = self.max_videos if is_video else self.max_images
        if len(files) > max_files:
            return False, "Too many files"
            
        # Check file formats and sizes
        supported_formats = self.supported_video_formats if is_video else self.supported_image_formats
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() not in supported_formats:
                return False, f"Unsupported file format: {file}"
                
            # Check file size
            size = os.path.getsize(file)
            if is_video and size > self.max_video_size:
                return False, f"File too large: {file}"
            elif not is_video and size > 20 * 1024 * 1024:  # 20MB max for images
                return False, f"File too large: {file}"
                    
        return True, None

    def upload_media(self, files: List[str], is_video: bool = False) -> Tuple[bool, Optional[str]]:
        """Upload media files to Reddit.
        
        Args:
            files: List of media file paths
            is_video: Whether the files are videos
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate files first
            is_valid, error = self.validate_media(files, is_video)
            if not is_valid:
                return False, error
                
            # Find and click upload button
            try:
                upload_button = self.utils.wait_for_element(
                    self.driver,
                    By.XPATH,
                    "//input[@type='file']",
                    timeout=10
                )
                if not upload_button:
                    return False, "Upload button not found"
                    
                # Upload each file
                for file in files:
                    upload_button.send_keys(os.path.abspath(file))
                    
                return True, None
                
            except (TimeoutException, NoSuchElementException) as e:
                return False, f"Failed to upload media: {str(e)}"
                
        except Exception as e:
            return False, f"Error uploading media: {str(e)}"

    def _create_media_dir(self, path: str) -> bool:
        """Create media directory if it doesn't exist.
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create media directory: {str(e)}")
            return False 
