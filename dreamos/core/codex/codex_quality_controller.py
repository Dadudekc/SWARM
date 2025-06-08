"""
Codex Quality Controller
----------------------
Uses headless Chrome to validate agent responses through ChatGPT:
1. Launches stealth Chrome
2. Injects agent responses
3. Gets ChatGPT judgment
4. Applies or escalates fixes
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..logging.log_manager import LogManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodexController:
    """Quality control agent using headless Chrome and ChatGPT."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Codex controller.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = LogManager()
        
        # Default configuration
        self.chrome_options = {
            "headless": self.config.get("headless", True),
            "version_main": 135,  # Confirmed working version
            "use_subprocess": True
        }
        
        # Runtime state
        self.driver = None
        self.is_initialized = False
        self.judgment_dir = Path("codex_judgments")
        self.judgment_dir.mkdir(exist_ok=True)
        
        # Initialize logging
        self.logger.info(
            platform="codex",
            status="initialized",
            message="Codex controller initialized",
            tags=["init", "codex"]
        )
        
    async def start(self):
        """Start the Codex controller."""
        if self.is_initialized:
            return
            
        try:
            # Launch Chrome
            self.driver = uc.Chrome(options=self.chrome_options)
            self.driver.get("https://chat.openai.com")
            
            # Wait for ChatGPT to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
            )
            
            self.is_initialized = True
            self.logger.info(
                platform="codex",
                status="started",
                message="Codex controller started",
                tags=["start", "codex"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="codex",
                status="error",
                message=f"Error starting Codex: {str(e)}",
                tags=["start", "error"]
            )
            raise
            
    async def stop(self):
        """Stop the Codex controller."""
        if not self.is_initialized:
            return
            
        try:
            if self.driver:
                self.driver.quit()
                
            self.is_initialized = False
            self.logger.info(
                platform="codex",
                status="stopped",
                message="Codex controller stopped",
                tags=["stop", "codex"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="codex",
                status="error",
                message=f"Error stopping Codex: {str(e)}",
                tags=["stop", "error"]
            )
            
    async def validate_and_patch(self, file_path: str, agent_response: str) -> Tuple[bool, Optional[str]]:
        """Validate agent response and apply patch if valid.
        
        Args:
            file_path: Path to file being patched
            agent_response: Agent's proposed fix
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Format prompt for ChatGPT
            prompt = self._format_validation_prompt(file_path, agent_response)
            
            # Get ChatGPT judgment
            judgment = await self._get_judgment(prompt)
            
            # Log judgment
            self._log_judgment(file_path, agent_response, judgment)
            
            if not judgment.get("valid", False):
                return False, judgment.get("feedback")
                
            # Apply patch
            if not await self._apply_patch(file_path, agent_response):
                return False, "Failed to apply patch"
                
            # Run tests
            if not await self._run_tests(file_path):
                return False, "Tests failed after patch"
                
            return True, None
            
        except Exception as e:
            self.logger.error(
                platform="codex",
                status="error",
                message=f"Error validating patch: {str(e)}",
                tags=["validate", "error"]
            )
            return False, str(e)
            
    def _format_validation_prompt(self, file_path: str, code: str) -> str:
        """Format prompt for ChatGPT validation."""
        return f"""
Please validate this code fix for {file_path}:

```python
{code}
```

Check for:
1. Syntax validity
2. Logical correctness
3. Style consistency
4. Potential bugs

Respond with:
- "valid": true/false
- "feedback": Detailed explanation
- "suggestions": List of improvements
"""
        
    async def _get_judgment(self, prompt: str) -> Dict[str, Any]:
        """Get judgment from ChatGPT."""
        try:
            # Find input field
            textarea = self.driver.find_element(By.CSS_SELECTOR, "textarea")
            
            # Type prompt
            textarea.send_keys(prompt)
            textarea.submit()
            
            # Wait for response
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-message-author-role='assistant']"))
            )
            
            # Get response
            response = self.driver.find_element(
                By.CSS_SELECTOR,
                "[data-message-author-role='assistant']"
            ).text
            
            # Parse response
            try:
                return json.loads(response)
            except:
                return {
                    "valid": "valid" in response.lower(),
                    "feedback": response,
                    "suggestions": []
                }
                
        except Exception as e:
            self.logger.error(
                platform="codex",
                status="error",
                message=f"Error getting judgment: {str(e)}",
                tags=["judgment", "error"]
            )
            return {
                "valid": False,
                "feedback": f"Error: {str(e)}",
                "suggestions": []
            }
            
    def _log_judgment(self, file_path: str, code: str, judgment: Dict[str, Any]):
        """Log judgment to file."""
        try:
            timestamp = datetime.utcnow().isoformat()
            log_file = self.judgment_dir / f"judgment_{timestamp}.json"
            
            with open(log_file, 'w') as f:
                json.dump({
                    "timestamp": timestamp,
                    "file": file_path,
                    "code": code,
                    "judgment": judgment
                }, f, indent=4)
                
        except Exception as e:
            self.logger.error(
                platform="codex",
                status="error",
                message=f"Error logging judgment: {str(e)}",
                tags=["log", "error"]
            )
            
    async def _apply_patch(self, file_path: str, code: str) -> bool:
        """Apply code patch to file."""
        try:
            with open(file_path, 'w') as f:
                f.write(code)
            return True
        except Exception as e:
            self.logger.error(
                platform="codex",
                status="error",
                message=f"Error applying patch: {str(e)}",
                tags=["patch", "error"]
            )
            return False
            
    async def _run_tests(self, file_path: str) -> bool:
        """Run tests for patched file."""
        try:
            process = await asyncio.create_subprocess_exec(
                "pytest",
                file_path,
                "-v",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception as e:
            self.logger.error(
                platform="codex",
                status="error",
                message=f"Error running tests: {str(e)}",
                tags=["test", "error"]
            )
            return False 
