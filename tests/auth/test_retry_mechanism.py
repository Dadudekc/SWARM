"""
Tests for the retry mechanism implementation.
"""

import pytest
import time
from typing import Callable, Any, Optional
from unittest.mock import Mock

class RetryError(Exception):
    """Base class for retry-related errors."""
    pass

class RetryMechanism:
    """Implements retry logic with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """Initialize the retry mechanism.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a specific attempt using exponential backoff.
        
        Args:
            attempt: The current attempt number (0-based)
            
        Returns:
            Delay in seconds before next retry
        """
        return self.base_delay * (2 ** attempt)
    
    def execute(self, operation: Callable[[], Any]) -> Any:
        """Execute an operation with retry logic.
        
        Args:
            operation: Callable that performs the operation
            
        Returns:
            Result of the operation if successful
            
        Raises:
            RetryError: If all retry attempts fail
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return operation()
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    time.sleep(delay)
        
        raise RetryError(f"Operation failed after {self.max_retries} attempts") from last_error

def test_exponential_backoff():
    """Test exponential backoff calculation."""
    retry = RetryMechanism(max_retries=3, base_delay=1.0)
    delays = [retry.calculate_delay(i) for i in range(3)]
    assert delays[0] == 1.0
    assert delays[1] == 2.0
    assert delays[2] == 4.0

def test_retry_with_success():
    """Test retry mechanism with eventual success."""
    retry = RetryMechanism(max_retries=3)
    attempts = 0
    
    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    result = retry.execute(operation)
    assert result == "success"
    assert attempts == 3

def test_retry_with_failure():
    """Test retry mechanism with all attempts failing."""
    retry = RetryMechanism(max_retries=3)
    
    def operation():
        raise ValueError("Persistent failure")
    
    with pytest.raises(RetryError) as exc_info:
        retry.execute(operation)
    assert "Operation failed after 3 attempts" in str(exc_info.value)

def test_retry_delay_timing():
    """Test that retry delays are properly timed."""
    retry = RetryMechanism(max_retries=3, base_delay=0.1)
    start_time = time.time()
    attempts = 0
    
    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    retry.execute(operation)
    elapsed_time = time.time() - start_time
    
    # Expected delays: 0.1s + 0.2s = 0.3s
    # Add some buffer for execution time
    assert 0.3 <= elapsed_time <= 0.5

def test_retry_with_custom_error():
    """Test retry mechanism with custom error types."""
    retry = RetryMechanism(max_retries=3)
    attempts = 0
    
    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RetryError("Custom error")
        return "success"
    
    result = retry.execute(operation)
    assert result == "success"
    assert attempts == 3

def test_retry_with_mock():
    """Test retry mechanism using mock objects."""
    retry = RetryMechanism(max_retries=3)
    mock_operation = Mock(side_effect=[
        ValueError("First failure"),
        ValueError("Second failure"),
        "success"
    ])
    
    result = retry.execute(mock_operation)
    assert result == "success"
    assert mock_operation.call_count == 3 