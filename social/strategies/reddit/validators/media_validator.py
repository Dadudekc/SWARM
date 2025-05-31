"""
Media Validator Module
--------------------
Provides functionality for validating media files.
"""

import os
from typing import List, Tuple

class MediaValidator:
    """Validates media files for Reddit posts."""
    
    def __init__(self):
        """Initialize the media validator."""
        self.supported_formats = {
            "image": [".jpg", ".jpeg", ".png", ".gif"],
            "video": [".mp4", ".mov", ".avi"]
        }
        
    def validate_media(self, files: List[str], media_type: str = "image") -> Tuple[bool, str]:
        """Validate media files.
        
        Args:
            files: List of file paths to validate
            media_type: Type of media ("image" or "video")
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not files:
            return False, "No files provided"
            
        if len(files) > 1:
            return False, "Only one file is allowed"
            
        file_path = files[0]
        
        # Check if file exists
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
            
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.supported_formats[media_type]:
            return False, f"Unsupported file format: {ext}"
            
        return True, "" 