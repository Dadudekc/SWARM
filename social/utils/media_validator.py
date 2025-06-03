"""
Media Validator Module
-------------------
Validates media files for upload.
"""

import os
from typing import List, Optional, Union, Tuple

class MediaValidator:
    """Validates media files for upload."""
    
    def __init__(
        self,
        max_size: int = 10 * 1024 * 1024,  # 10MB default
        max_files: int = 20,  # Default max files
        supported_formats: Optional[List[str]] = None
    ):
        """Initialize validator.
        
        Args:
            max_size: Maximum file size in bytes
            max_files: Maximum number of files allowed
            supported_formats: List of supported file formats
        """
        self.max_size = max_size
        self.max_files = max_files
        self.supported_formats = supported_formats or [
            '.jpg', '.jpeg', '.png', '.gif',  # Images
            '.mp4', '.mov', '.avi', '.wmv'    # Videos
        ]
    
    def validate_files(
        self,
        files: Union[str, List[str]],
        is_video: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Validate one or more files.
        
        Args:
            files: Single file path or list of file paths
            is_video: Whether files should be validated as videos
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if isinstance(files, str):
            files = [files]
            
        if not files:
            return True, None
            
        if len(files) > self.max_files:
            return False, f"Too many files (max: {self.max_files})"
            
        for file_path in files:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
                
            if not os.path.isfile(file_path):
                return False, f"Not a file: {file_path}"
                
            file_size = os.path.getsize(file_path)
            if file_size > self.max_size:
                return False, f"File too large: {file_path}"
                
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.supported_formats:
                return False, f"Unsupported format: {file_path}"
                
            if is_video and ext not in ['.mp4', '.mov', '.avi', '.wmv']:
                return False, f"Not a video file: {file_path}"
                
        return True, None
    
    def validate(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate a single file.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.validate_files(file_path)
    
    def validate_media(
        self,
        files: Union[str, List[str]],
        is_video: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Validate media files.
        
        Args:
            files: Single file path or list of file paths
            is_video: Whether files should be validated as videos
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.validate_files(files, is_video) 