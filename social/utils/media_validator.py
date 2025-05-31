"""
Media Validator Module
-------------------
Validates media files for upload.
"""

import os
from typing import List, Optional, Union

class MediaValidator:
    """Validates media files for upload."""
    
    def __init__(self, max_size: int = 10 * 1024 * 1024):  # 10MB default
        """Initialize validator.
        
        Args:
            max_size: Maximum file size in bytes
        """
        self.max_size = max_size
        self.supported_formats = [
            '.jpg', '.jpeg', '.png', '.gif',  # Images
            '.mp4', '.mov', '.avi', '.wmv'    # Videos
        ]
    
    def validate_files(
        self,
        files: Union[str, List[str]],
        is_video: bool = False
    ) -> Optional[str]:
        """Validate one or more files.
        
        Args:
            files: Single file path or list of file paths
            is_video: Whether files should be validated as videos
            
        Returns:
            Error message if validation fails, None if successful
        """
        if isinstance(files, str):
            files = [files]
            
        if not files:
            return "No files provided"
            
        for file_path in files:
            if not os.path.exists(file_path):
                return f"File not found: {file_path}"
                
            if not os.path.isfile(file_path):
                return f"Not a file: {file_path}"
                
            file_size = os.path.getsize(file_path)
            if file_size > self.max_size:
                return f"File too large: {file_path}"
                
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.supported_formats:
                return f"Unsupported format: {file_path}"
                
            if is_video and ext not in ['.mp4', '.mov', '.avi', '.wmv']:
                return f"Not a video file: {file_path}"
                
        return None
    
    def validate(self, file_path: str) -> Optional[str]:
        """Validate a single file.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Error message if validation fails, None if successful
        """
        return self.validate_files(file_path)
    
    def validate_media(
        self,
        files: Union[str, List[str]],
        is_video: bool = False
    ) -> Optional[str]:
        """Validate media files.
        
        Args:
            files: Single file path or list of file paths
            is_video: Whether files should be validated as videos
            
        Returns:
            Error message if validation fails, None if successful
        """
        return self.validate_files(files, is_video) 