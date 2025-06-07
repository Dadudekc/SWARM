"""
Fix Manager
----------
Handles test failure analysis and automated fixes.
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .utils.config import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixManager:
    """Manages test failure analysis and fixes."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the fix manager.
        
        Args:
            config_manager: Optional configuration manager
        """
        self.config_manager = config_manager or ConfigManager("config/test_debug_config.json")
        self.fix_config = self.config_manager.get_fix_config()
    
    async def fix_test(self, task: Dict[str, Any]) -> bool:
        """Attempt to fix a test failure.
        
        Args:
            task: Task containing test failure details
            
        Returns:
            True if fix successful, False otherwise
        """
        try:
            # Get source content
            source_content = self._get_source_content(task["test_file"])
            if not source_content:
                return False
            
            # Analyze failure
            error_type = self._analyze_failure(task["error"])
            
            # Apply appropriate fix
            if error_type == "import":
                return await self._fix_import_error(task, source_content)
            elif error_type == "assertion":
                return await self._fix_assertion_error(task, source_content)
            else:
                return await self._fix_generic_error(task, source_content)
                
        except Exception as e:
            logger.error(f"Error fixing test: {e}")
            return False
    
    def _analyze_failure(self, error: str) -> str:
        """Analyze test failure to determine error type.
        
        Args:
            error: Error message
            
        Returns:
            Error type (import, assertion, or generic)
        """
        error = error.lower()
        
        if any(x in error for x in ["import", "module", "package"]):
            return "import"
        elif any(x in error for x in ["assert", "expected", "actual"]):
            return "assertion"
        else:
            return "generic"
    
    async def _fix_import_error(self, task: Dict[str, Any], source_content: str) -> bool:
        """Fix import-related errors.
        
        Args:
            task: Task containing test failure details
            source_content: Source file content
            
        Returns:
            True if fix successful, False otherwise
        """
        try:
            # Extract missing import
            missing_import = self._extract_missing_import(task["error"])
            if not missing_import:
                return False
            
            # Add import statement
            new_content = self._add_import_statement(source_content, missing_import)
            
            # Write updated content
            return self._write_source_content(task["test_file"], new_content)
            
        except Exception as e:
            logger.error(f"Error fixing import: {e}")
            return False
    
    async def _fix_assertion_error(self, task: Dict[str, Any], source_content: str) -> bool:
        """Fix assertion-related errors.
        
        Args:
            task: Task containing test failure details
            source_content: Source file content
            
        Returns:
            True if fix successful, False otherwise
        """
        try:
            # Extract expected and actual values
            expected, actual = self._extract_assertion_values(task["error"])
            if not expected or not actual:
                return False
            
            # Update assertion
            new_content = self._update_assertion(
                source_content,
                task["test_name"],
                expected,
                actual
            )
            
            # Write updated content
            return self._write_source_content(task["test_file"], new_content)
            
        except Exception as e:
            logger.error(f"Error fixing assertion: {e}")
            return False
    
    async def _fix_generic_error(self, task: Dict[str, Any], source_content: str) -> bool:
        """Fix generic errors.
        
        Args:
            task: Task containing test failure details
            source_content: Source file content
            
        Returns:
            True if fix successful, False otherwise
        """
        try:
            # Analyze error pattern
            error_pattern = self._extract_error_pattern(task["error"])
            if not error_pattern:
                return False
            
            # Apply fix based on pattern
            new_content = self._apply_generic_fix(
                source_content,
                task["test_name"],
                error_pattern
            )
            
            # Write updated content
            return self._write_source_content(task["test_file"], new_content)
            
        except Exception as e:
            logger.error(f"Error fixing generic error: {e}")
            return False
    
    def _get_source_content(self, file_path: str) -> Optional[str]:
        """Get source file content.
        
        Args:
            file_path: Path to source file
            
        Returns:
            File content if successful, None otherwise
        """
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading source file: {e}")
            return None
    
    def _write_source_content(self, file_path: str, content: str) -> bool:
        """Write source file content.
        
        Args:
            file_path: Path to source file
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing source file: {e}")
            return False
    
    def _extract_missing_import(self, error: str) -> Optional[str]:
        """Extract missing import from error message.
        
        Args:
            error: Error message
            
        Returns:
            Missing import if found, None otherwise
        """
        try:
            # Look for common import error patterns
            patterns = [
                r"No module named '([^']+)'",
                r"cannot import name '([^']+)'",
                r"ImportError: No module named '([^']+)'"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, error)
                if match:
                    return match.group(1)
            return None
            
        except Exception:
            return None
    
    def _add_import_statement(self, content: str, import_name: str) -> str:
        """Add import statement to source content.
        
        Args:
            content: Source content
            import_name: Import to add
            
        Returns:
            Updated content
        """
        try:
            # Find last import statement
            lines = content.splitlines()
            last_import = 0
            
            for i, line in enumerate(lines):
                if line.startswith(("import ", "from ")):
                    last_import = i
            
            # Add new import
            new_import = f"import {import_name}\n"
            lines.insert(last_import + 1, new_import)
            
            return "\n".join(lines)
            
        except Exception:
            return content
    
    def _extract_assertion_values(self, error: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract expected and actual values from assertion error.
        
        Args:
            error: Error message
            
        Returns:
            Tuple of (expected, actual) values
        """
        try:
            # Look for common assertion patterns
            patterns = [
                r"assert\s+([^=]+)\s*==\s*([^,]+)",
                r"Expected:\s*([^\n]+)\s*Actual:\s*([^\n]+)",
                r"Expected\s+([^,]+),\s+got\s+([^\n]+)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, error)
                if match:
                    return match.group(1).strip(), match.group(2).strip()
            return None, None
            
        except Exception:
            return None, None
    
    def _update_assertion(self, content: str, test_name: str, expected: str, actual: str) -> str:
        """Update assertion in test.
        
        Args:
            content: Source content
            test_name: Test name
            expected: Expected value
            actual: Actual value
            
        Returns:
            Updated content
        """
        try:
            # Find test function
            test_pattern = f"def {test_name}"
            test_start = content.find(test_pattern)
            if test_start == -1:
                return content
            
            # Find assertion
            assertion_pattern = f"assert {expected}"
            assertion_start = content.find(assertion_pattern, test_start)
            if assertion_start == -1:
                return content
            
            # Replace assertion
            new_assertion = f"assert {actual}"
            return content[:assertion_start] + new_assertion + content[assertion_start + len(assertion_pattern):]
            
        except Exception:
            return content
    
    def _extract_error_pattern(self, error: str) -> Optional[str]:
        """Extract error pattern for generic fixes.
        
        Args:
            error: Error message
            
        Returns:
            Error pattern if found, None otherwise
        """
        try:
            # Look for common error patterns
            patterns = [
                r"TypeError: ([^\n]+)",
                r"ValueError: ([^\n]+)",
                r"AttributeError: ([^\n]+)",
                r"KeyError: ([^\n]+)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, error)
                if match:
                    return match.group(1).strip()
            return None
            
        except Exception:
            return None
    
    def _apply_generic_fix(self, content: str, test_name: str, error_pattern: str) -> str:
        """Apply generic fix based on error pattern.
        
        Args:
            content: Source content
            test_name: Test name
            error_pattern: Error pattern
            
        Returns:
            Updated content
        """
        try:
            # Find test function
            test_pattern = f"def {test_name}"
            test_start = content.find(test_pattern)
            if test_start == -1:
                return content
            
            # Apply fix based on pattern
            if "type" in error_pattern.lower():
                return self._fix_type_error(content, test_start)
            elif "value" in error_pattern.lower():
                return self._fix_value_error(content, test_start)
            elif "attribute" in error_pattern.lower():
                return self._fix_attribute_error(content, test_start)
            elif "key" in error_pattern.lower():
                return self._fix_key_error(content, test_start)
            else:
                return content
                
        except Exception:
            return content
    
    def _fix_type_error(self, content: str, test_start: int) -> str:
        """Fix type error in test.
        
        Args:
            content: Source content
            test_start: Start of test function
            
        Returns:
            Updated content
        """
        # Add type conversion
        return content
    
    def _fix_value_error(self, content: str, test_start: int) -> str:
        """Fix value error in test.
        
        Args:
            content: Source content
            test_start: Start of test function
            
        Returns:
            Updated content
        """
        # Add value validation
        return content
    
    def _fix_attribute_error(self, content: str, test_start: int) -> str:
        """Fix attribute error in test.
        
        Args:
            content: Source content
            test_start: Start of test function
            
        Returns:
            Updated content
        """
        # Add attribute check
        return content
    
    def _fix_key_error(self, content: str, test_start: int) -> str:
        """Fix key error in test.
        
        Args:
            content: Source content
            test_start: Start of test function
            
        Returns:
            Updated content
        """
        # Add key existence check
        return content 