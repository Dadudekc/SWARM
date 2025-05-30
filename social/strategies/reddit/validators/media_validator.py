from typing import List, Optional, Tuple
import os
from PIL import Image
import mimetypes

class MediaValidator:
    """Validates media files for Reddit posts."""
    
    def __init__(self):
        """Initialize the media validator."""
        # Reddit media constraints
        self.constraints = {
            "image": {
                "max_size": 20 * 1024 * 1024,  # 20MB
                "allowed_types": [".jpg", ".jpeg", ".png", ".gif"],
                "max_dimensions": (4096, 4096)
            },
            "video": {
                "max_size": 1 * 1024 * 1024 * 1024,  # 1GB
                "allowed_types": [".mp4", ".mov"],
                "max_duration": 15 * 60  # 15 minutes
            }
        }
        
        self.max_size = 100 * 1024 * 1024  # 100MB
        self.max_files = 20
        self.supported_image_formats = [".jpg", ".jpeg", ".png", ".gif"]
        self.supported_video_formats = [".mp4", ".mov", ".avi"]
        
    def validate_media(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Validate media files for Reddit.
        
        Args:
            media_paths: List of media file paths
            is_video: Whether the media is video
            
        Returns:
            bool: True if all media files are valid, False otherwise
        """
        if not media_paths:
            return True
            
        media_type = "video" if is_video else "image"
        constraints = self.constraints[media_type]
        
        for path in media_paths:
            if not self._validate_single_file(path, constraints, is_video):
                return False
                
        return True
        
    def _validate_single_file(self, path: str, constraints: dict, is_video: bool) -> bool:
        """Validate a single media file.
        
        Args:
            path: Path to the media file
            constraints: Media type constraints
            is_video: Whether the file is a video
            
        Returns:
            bool: True if the file is valid, False otherwise
        """
        # Check if file exists
        if not os.path.exists(path):
            return False
            
        # Check file size
        file_size = os.path.getsize(path)
        if file_size > constraints["max_size"]:
            return False
            
        # Check file type
        file_ext = os.path.splitext(path)[1].lower()
        if file_ext not in constraints["allowed_types"]:
            return False
            
        # Additional validation for images
        if not is_video:
            try:
                with Image.open(path) as img:
                    width, height = img.size
                    if width > constraints["max_dimensions"][0] or height > constraints["max_dimensions"][1]:
                        return False
            except Exception:
                return False
                
        return True

    def validate(self, files: List[str], is_video: bool = False) -> Tuple[bool, Optional[str]]:
        """Validate media files.
        
        Args:
            files: List of file paths to validate
            is_video: Whether files are videos
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not files:
            return True, None
            
        if len(files) > self.max_files:
            return False, f"Too many files (max {self.max_files})"
            
        supported_formats = self.supported_video_formats if is_video else self.supported_image_formats
        
        for file_path in files:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
                
            file_size = os.path.getsize(file_path)
            if file_size > self.max_size:
                return False, f"File too large: {file_path} ({file_size} > {self.max_size})"
                
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in supported_formats:
                return False, f"Unsupported file format: {ext}"
                
        return True, None 