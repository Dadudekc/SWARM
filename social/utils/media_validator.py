"""
Media Validator Module
--------------------
Provides functionality for validating media files before upload.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import mimetypes
import os

class MediaValidator:
    """Validates media files for upload."""
    
    def __init__(
        self,
        max_size_mb: int = 20,
        allowed_types: Optional[List[str]] = None
    ):
        """Initialize the media validator.
        
        Args:
            max_size_mb: Maximum file size in megabytes
            allowed_types: List of allowed MIME types
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.allowed_types = allowed_types or [
            'image/jpeg',
            'image/png',
            'image/gif',
            'video/mp4',
            'video/quicktime'
        ]
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate a media file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dictionary containing validation results:
            {
                'valid': bool,
                'errors': List[str],
                'mime_type': str,
                'size_mb': float
            }
        """
        result = {
            'valid': True,
            'errors': [],
            'mime_type': '',
            'size_mb': 0.0
        }
        
        try:
            path = Path(file_path)
            if not path.exists():
                result['valid'] = False
                result['errors'].append(f"File not found: {file_path}")
                return result
            
            # Check file size
            size_bytes = path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            result['size_mb'] = size_mb
            
            if size_bytes > self.max_size_bytes:
                result['valid'] = False
                result['errors'].append(
                    f"File too large: {size_mb:.1f}MB > {self.max_size_mb}MB"
                )
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            result['mime_type'] = mime_type or 'application/octet-stream'
            
            if mime_type not in self.allowed_types:
                result['valid'] = False
                result['errors'].append(
                    f"Unsupported file type: {mime_type}"
                )
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Validation error: {str(e)}")
        
        return result
    
    def validate_files(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """Validate multiple media files.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Dictionary mapping file paths to their validation results
        """
        return {
            path: self.validate_file(path)
            for path in file_paths
        }

    def validate(self, files: List[str], is_video: bool = False) -> tuple[bool, str]:
        """Validate a list of media files.
        
        Args:
            files: List of file paths to validate
            is_video: Whether the files should be validated as video files
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not files:
            return False, "No files provided"
            
        # Validate each file
        results = self.validate_files(files)
        
        # Check if any files are invalid
        for path, result in results.items():
            if not result['valid']:
                return False, result['errors'][0]
                
        # Check if files are of correct type
        if is_video:
            for path, result in results.items():
                if not result['mime_type'].startswith('video/'):
                    return False, f"File {path} is not a video"
        else:
            for path, result in results.items():
                if not result['mime_type'].startswith('image/'):
                    return False, f"File {path} is not an image"
                    
        return True, "" 