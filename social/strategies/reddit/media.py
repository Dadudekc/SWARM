"""
Reddit Media Handler
------------------
Handles media operations for Reddit posts.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import magic

logger = logging.getLogger(__name__)

class RedditMediaHandler:
    """Handles media operations for Reddit posts."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.gif']
        self.supported_video_formats = ['.mp4', '.mov', '.avi']
        self.max_file_size = config.get('max_file_size', 20 * 1024 * 1024)  # 20MB default
        self.max_images = config.get('max_images', 20)
    
    def validate_media(self, files: List[str], allow_video: bool = True) -> Dict[str, Any]:
        """
        Validate media files for Reddit posting.
        
        Args:
            files: List of file paths to validate
            allow_video: Whether to allow video files
            
        Returns:
            Dict containing validation results and any error messages
        """
        if not files:
            return {'valid': False, 'error': 'No media files provided'}
        
        if len(files) > self.max_images:
            return {
                'valid': False,
                'error': f'Too many files. Maximum allowed: {self.max_images}'
            }
        
        results = []
        for file_path in files:
            if not os.path.exists(file_path):
                return {'valid': False, 'error': f'File not found: {file_path}'}
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return {
                    'valid': False,
                    'error': f'File too large: {file_path} ({file_size / 1024 / 1024:.1f}MB)'
                }
            
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(file_path)
            
            if file_type.startswith('image/'):
                if not any(file_path.lower().endswith(fmt) for fmt in self.supported_image_formats):
                    return {
                        'valid': False,
                        'error': f'Unsupported image format: {file_path}'
                    }
            elif file_type.startswith('video/'):
                if not allow_video:
                    return {
                        'valid': False,
                        'error': 'Video files are not allowed'
                    }
                if not any(file_path.lower().endswith(fmt) for fmt in self.supported_video_formats):
                    return {
                        'valid': False,
                        'error': f'Unsupported video format: {file_path}'
                    }
            else:
                return {
                    'valid': False,
                    'error': f'Unsupported file type: {file_type}'
                }
            
            results.append({
                'path': file_path,
                'type': file_type,
                'size': file_size
            })
        
        return {
            'valid': True,
            'files': results
        }
    
    def prepare_media(self, files: List[str]) -> Dict[str, Any]:
        """
        Prepare media files for Reddit posting.
        
        Args:
            files: List of validated file paths
            
        Returns:
            Dict containing prepared media data
        """
        prepared = []
        for file_path in files:
            file_type = magic.Magic(mime=True).from_file(file_path)
            prepared.append({
                'path': file_path,
                'type': file_type,
                'name': os.path.basename(file_path)
            })
        
        return {
            'files': prepared,
            'total_size': sum(os.path.getsize(f) for f in files)
        } 