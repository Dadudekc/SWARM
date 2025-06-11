"""Bridge error handling module."""

class BridgeError(Exception):
    """Base exception for bridge-related errors."""
    
    def __init__(self, message: str, severity: str = "medium"):
        """Initialize the bridge error.
        
        Args:
            message: Error message
            severity: Error severity level (low, medium, high)
        """
        self.message = message
        self.severity = severity
        super().__init__(self.message)
        
    def __str__(self) -> str:
        """Get string representation of the error."""
        return f"{self.message} (Severity: {self.severity})" 