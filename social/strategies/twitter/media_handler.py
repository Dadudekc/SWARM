"""
Twitter Media Handler
-------------------
Handles media uploads and validation for Twitter.
"""

from typing import Tuple, List, Optional
import os
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

class TwitterMediaHandler:
    """Handles Twitter media operations."""
    
    # Supported formats
    SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".gif"]
    SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov"]
    
    # Size limits
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_VIDEO_SIZE = 512 * 1024 * 1024  # 512MB
    
    def __init__(self, driver, utils, logger):
        """Initialize the media handler.
        
        Args:
            driver: Selenium WebDriver instance
            utils: Utility functions
            logger: Logger instance
        """
        self.driver = driver
        self.utils = utils
        self.logger = logger
        self._last_error = None
        self._upload_retries = 3
        self._retry_delay = 2
        
    def validate_media(self, media_files: List[str], is_video: bool = False) -> Tuple[bool, Optional[str]]:
        """Validate media files before upload.
        
        Args:
            media_files: List of media file paths
            is_video: Whether the files are videos
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not media_files:
            return True, None
            
        # Check number of files
        if is_video and len(media_files) > 1:
            return False, "Only one video can be uploaded per post"
            
        # Check each file
        for file_path in media_files:
            try:
                # Convert to Path object
                path = Path(file_path)
                
                # Check file exists
                if not path.exists():
                    return False, f"File not found: {file_path}"
                    
                # Check file extension
                ext = path.suffix.lower()
                if is_video:
                    if ext not in self.SUPPORTED_VIDEO_FORMATS:
                        return False, f"Unsupported video format: {ext}"
                else:
                    if ext not in self.SUPPORTED_IMAGE_FORMATS:
                        return False, f"Unsupported image format: {ext}"
                        
                # Check file size
                size = path.stat().st_size
                if is_video and size > self.MAX_VIDEO_SIZE:
                    return False, f"Video too large: {size} bytes (max {self.MAX_VIDEO_SIZE})"
                elif not is_video and size > self.MAX_IMAGE_SIZE:
                    return False, f"Image too large: {size} bytes (max {self.MAX_IMAGE_SIZE})"
                    
                # Check file permissions
                if not os.access(path, os.R_OK):
                    return False, f"No read permission for file: {file_path}"
                    
            except Exception as e:
                return False, f"Error validating file {file_path}: {str(e)}"
                
        return True, None
        
    def upload_media(self, media_files: List[str], is_video: bool = False) -> bool:
        """Upload media files to Twitter.
        
        Args:
            media_files: List of media file paths
            is_video: Whether the files are videos
            
        Returns:
            True if upload was successful, False otherwise
        """
        # Validate files first
        is_valid, error = self.validate_media(media_files, is_video)
        if not is_valid:
            self._last_error = {
                "error": error,
                "context": "media_validation",
                "timestamp": datetime.now().isoformat()
            }
            if self.logger:
                self.logger.error(
                    message=f"Media validation failed: {error}",
                    platform="twitter",
                    status="error"
                )
            return False
            
        # Try upload with retries
        for attempt in range(self._upload_retries):
            try:
                # Click media button
                media_button = self.utils.wait_for_element(
                    self.driver,
                    By.XPATH,
                    "//input[@data-testid='fileInput']",
                    timeout=10
                )
                if not media_button:
                    raise NoSuchElementException("Media upload button not found")
                
                # Upload each file
                for file_path in media_files:
                    media_button.send_keys(str(Path(file_path).absolute()))
                    
                    # Wait for upload to complete
                    if not self.utils.wait_for_element(
                        self.driver,
                        By.XPATH,
                        "//div[@data-testid='attachments']",
                        timeout=30
                    ):
                        raise TimeoutException("Media upload timed out")
                
                return True
                
            except (TimeoutException, NoSuchElementException) as e:
                self._last_error = {
                    "error": str(e),
                    "context": "media_upload",
                    "attempt": attempt + 1,
                    "timestamp": datetime.now().isoformat()
                }
                if self.logger:
                    self.logger.error(
                        message=f"Media upload failed (attempt {attempt + 1}): {str(e)}",
                        platform="twitter",
                        status="error"
                    )
                if attempt < self._upload_retries - 1:
                    self.utils.sleep(self._retry_delay)
                    continue
                return False 