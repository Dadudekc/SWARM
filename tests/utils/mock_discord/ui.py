"""Mock Discord UI module."""

from typing import Any, Optional, List, Dict, Union
from enum import Enum

class ButtonStyle(Enum):
    """Mock button styles."""
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5

class View:
    """Mock Discord view."""
    def __init__(self, timeout: Optional[float] = 180.0):
        self.timeout = timeout
        self.children: List[Any] = []

    def add_item(self, item: Any) -> None:
        """Add an item to the view."""
        self.children.append(item)

class Button:
    """Mock Discord button."""
    def __init__(self, style: ButtonStyle, label: str, custom_id: Optional[str] = None, **kwargs):
        self.style = style
        self.label = label
        self.custom_id = custom_id
        self.disabled = kwargs.get('disabled', False)
        self.url = kwargs.get('url')

class Select:
    """Mock Discord select menu."""
    def __init__(self, custom_id: str, placeholder: Optional[str] = None, **kwargs):
        self.custom_id = custom_id
        self.placeholder = placeholder
        self.options: List[Dict[str, Any]] = []
        self.disabled = kwargs.get('disabled', False)

    def add_option(self, label: str, value: str, **kwargs) -> None:
        """Add an option to the select menu."""
        self.options.append({
            'label': label,
            'value': value,
            'description': kwargs.get('description'),
            'emoji': kwargs.get('emoji'),
            'default': kwargs.get('default', False)
        })

class TextInput:
    """Mock Discord text input."""
    def __init__(self, label: str, custom_id: str, **kwargs):
        self.label = label
        self.custom_id = custom_id
        self.style = kwargs.get('style', 1)  # 1 = short, 2 = paragraph
        self.placeholder = kwargs.get('placeholder')
        self.min_length = kwargs.get('min_length')
        self.max_length = kwargs.get('max_length')
        self.required = kwargs.get('required', True)
        self.value = kwargs.get('value', '')

class Modal:
    """Mock Discord modal."""
    def __init__(self, title: str, custom_id: Optional[str] = None):
        self.title = title
        self.custom_id = custom_id
        self.children: List[TextInput] = []

    def add_item(self, item: TextInput) -> None:
        """Add an item to the modal."""
        self.children.append(item)
