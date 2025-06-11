"""
ChatGPT Response Handler
-----------------------
Handles processing and validation of ChatGPT responses.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class ChatGPTResponseHandler:
    """Handles processing and validation of ChatGPT responses."""
    
    def __init__(self, config: Dict[str, Any], bridge=None):
        """Initialize response handler.
        
        Args:
            config: Configuration dictionary containing paths and settings
            bridge: Optional bridge instance for additional functionality
        """
        self.config = config
        self.bridge = bridge
        self.output_dir = Path(config["paths"]["output"])
        self.archive_dir = Path(config["paths"]["archive"])
        
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_reply(self, response: Dict[str, Any]) -> str:
        """Extract reply content from response.
        
        Args:
            response: Response dictionary containing content and metadata
            
        Returns:
            Extracted reply content
        """
        content = response.get("content", "")
        if not content:
            return ""
            
        # Extract code blocks
        code_blocks = re.findall(r"```(?:python|javascript|.*?)\n(.*?)```", content, re.DOTALL)
        if code_blocks:
            return "\n".join(block.strip() for block in code_blocks)
            
        return content.strip()
        
    def parse_output(self, output: str) -> str:
        """Parse output string to extract code blocks.
        
        Args:
            output: Output string potentially containing code blocks
            
        Returns:
            Parsed output with code blocks extracted
        """
        if not output:
            return ""
            
        # Extract code blocks
        code_blocks = re.findall(r"```(?:python|javascript|.*?)\n(.*?)```", output, re.DOTALL)
        if code_blocks:
            return "\n".join(block.strip() for block in code_blocks)
            
        return output.strip()
        
    async def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process a response.
        
        Args:
            response: Response dictionary to process
            
        Returns:
            Processed response dictionary
        """
        if not response:
            raise ValueError("Response cannot be None")
            
        if not isinstance(response, dict):
            raise ValueError("Response must be a dictionary")
            
        # Validate response
        if not await self.validate_response(response):
            return {
                "status": "error",
                "error": "Invalid response format",
                "content": response.get("content", ""),
                "metadata": response.get("metadata", {})
            }
            
        # Extract reply
        content = self.extract_reply(response)
        
        # Create processed response
        processed = {
            "content": content,
            "metadata": response.get("metadata", {}),
            "timestamp": response.get("timestamp", datetime.now().isoformat()),
            "status": "success"
        }
        
        # Save response
        await self._save_response(processed)
        
        return processed
        
    async def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate a response.
        
        Args:
            response: Response dictionary to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        # Check required fields
        if not response.get("content"):
            return False
            
        if not isinstance(response.get("metadata"), dict):
            return False
            
        # Validate timestamp if present
        timestamp = response.get("timestamp")
        if timestamp:
            try:
                datetime.fromisoformat(timestamp)
            except ValueError:
                return False
                
        return True
        
    async def _save_response(self, response: Dict[str, Any]):
        """Save response to output directory.
        
        Args:
            response: Response dictionary to save
        """
        # Create filename from timestamp
        timestamp = response.get("timestamp", datetime.now().isoformat())
        filename = f"response_{timestamp.replace(':', '-')}.json"
        
        # Save to output directory
        output_path = self.output_dir / filename
        with open(output_path, "w") as f:
            json.dump(response, f, indent=2)
            
        # Archive response
        archive_path = self.archive_dir / filename
        with open(archive_path, "w") as f:
            json.dump(response, f, indent=2) 