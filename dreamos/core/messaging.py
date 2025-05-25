from enum import Enum

class MessageMode(Enum):
    """Message modes for different types of communication."""
    COMMAND = "COMMAND"
    QUERY = "QUERY"
    RESPONSE = "RESPONSE"
    ERROR = "ERROR"
    SELF_TEST = "SELF_TEST"  # For self-test protocol messages 