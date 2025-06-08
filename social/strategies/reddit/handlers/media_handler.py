"""
Media handler for Reddit strategy.
"""

from pathlib import Path
from typing import List, Optional, Union
import os
import logging
from PIL import Image
import mimetypes

logger = logging.getLogger(__name__)

class MediaHandler:
    """Handles media validation and processing for Reddit posts."""
    
    def __init__(self, config: dict):
        """Initialize media handler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.max_file_size = config.get('max_file_size', 20 * 1024 * 1024)  # 20MB default
        self.allowed_image_types = {'.jpg', '.jpeg', '.png', '.gif'}
        self.allowed_video_types = {'.mp4', '.mov', '.avi'}
        self.max_images = config.get('max_images', 4)
        
    def validate_media(self, files: List[Union[str, Path]]) -> tuple[bool, str]:
        """Validate media files for Reddit posting.
        
        Args:
            files: List of file paths to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not files:
            return True, ""
            
        if len(files) > self.max_images:
            return False, f"Too many files. Maximum allowed is {self.max_images}"
            
        for file_path in files:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                return False, f"File not found: {file_path}"
                
            # Check file size
            if file_path.stat().st_size > self.max_file_size:
                return False, f"File too large: {file_path}"
                
            # Check file type
            ext = file_path.suffix.lower()
            if ext not in self.allowed_image_types and ext not in self.allowed_video_types:
                return False, f"Unsupported file type: {ext}"
                
            # Validate image dimensions if it's an image
            if ext in self.allowed_image_types:
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                        if width > 4096 or height > 4096:
                            return False, f"Image dimensions too large: {width}x{height}"
                except Exception as e:
                    return False, f"Failed to validate image: {str(e)}"
                    
        return True, ""
        
    def process_media(self, files: List[Union[str, Path]]) -> List[Path]:
        """Process media files for posting.
        
        Args:
            files: List of file paths to process
            
        Returns:
            List of processed file paths
        """
        valid, error = self.validate_media(files)
        if not valid:
            raise ValueError(error)
            
        return [Path(f) for f in files] 
