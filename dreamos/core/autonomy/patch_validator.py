"""
Patch validation module for Dream.OS.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from .codex_patch_tracker import CodexPatchTracker

logger = logging.getLogger(__name__)

class PatchValidator:
    """Validates patches before they are applied."""
    
    def __init__(self, patch_tracker: Optional[CodexPatchTracker] = None):
        """Initialize the patch validator.
        
        Args:
            patch_tracker: Optional CodexPatchTracker instance
        """
        self.patch_tracker = patch_tracker or CodexPatchTracker()
        self.logger = logger

    async def validate_patch(self, patch_id: str, file_path: str, patch_content: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate a patch before applying it.
        
        Args:
            patch_id: Unique identifier for the patch
            file_path: Path to the file being patched
            patch_content: Content of the patch
            
        Returns:
            Tuple of (is_valid, validation_results)
        """
        try:
            # Run scanner validation
            is_valid, scanner_results = await self.patch_tracker.validate_with_scanner(patch_id, file_path)
            
            if not is_valid:
                self.logger.warning(
                    f"Patch {patch_id} failed scanner validation",
                    extra={
                        "platform": "codex",
                        "status": "scanner_failed",
                        "patch_id": patch_id,
                        "file_path": file_path,
                        "scanner_results": scanner_results
                    }
                )
                return False, {
                    "error": "Scanner validation failed",
                    "scanner_results": scanner_results
                }
            
            # Track the patch
            await self.patch_tracker.track_patch(patch_id, file_path, "success")
            
            return True, {
                "status": "validated",
                "scanner_results": scanner_results
            }
            
        except Exception as e:
            self.logger.error(
                f"Patch validation failed: {str(e)}",
                extra={
                    "platform": "codex",
                    "status": "error",
                    "patch_id": patch_id,
                    "file_path": file_path,
                    "error": str(e)
                }
            )
            return False, {"error": str(e)}

    def get_validation_history(self, patch_id: str) -> Optional[Dict[str, Any]]:
        """Get validation history for a patch.
        
        Args:
            patch_id: Unique identifier for the patch
            
        Returns:
            Validation history if found, None otherwise
        """
        return self.patch_tracker.get_patch_status(patch_id)

    def get_all_validations(self) -> Dict[str, Dict[str, Any]]:
        """Get all patch validations.
        
        Returns:
            Dictionary of all patch validations
        """
        return self.patch_tracker.get_all_patches() 