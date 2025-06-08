"""
Media Validator Module
--------------------
Provides functionality for validating media files.
"""

import os
from typing import List, Tuple

class MediaValidator:
    """Validates media files for social media posts."""
    
    def __init__(self, max_files: int = 1, max_size: int = 10 * 1024 * 1024):  # 10MB default
        """Initialize the media validator.
        
        Args:
            max_files: Maximum number of files allowed
            max_size: Maximum file size in bytes
        """
        self.max_files = max_files
        self.max_size = max_size
        self.supported_formats = {
            "image": [".jpg", ".jpeg", ".png", ".gif"],
            "video": [".mp4", ".mov", ".avi"]
        }
        
    def validate_media(self, files: List[str], is_video: bool = False) -> Tuple[bool, str]:
        """Validate media files.
        
        Args:
            files: List of file paths to validate
            is_video: Whether files should be validated as videos
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Empty files list is valid
        if not files:
            return True, ""
            
        # Check number of files first
        if len(files) > self.max_files:
            return False, f"Too many files (max: {self.max_files})"
            
        # Validate each file
        for file_path in files:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
                
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_size:
                return False, f"File too large: {file_path} (max: {self.max_size / (1024 * 1024):.1f}MB)"
                
            # Check file extension
            _, ext = os.path.splitext(file_path)
            media_type = "video" if is_video else "image"
            if ext.lower() not in self.supported_formats[media_type]:
                return False, f"Unsupported file format: {file_path} (supported: {', '.join(self.supported_formats[media_type])})"
                
        return True, "" 