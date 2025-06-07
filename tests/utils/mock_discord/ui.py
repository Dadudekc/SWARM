"""Mock Discord UI components for testing."""
from typing import Any, List, Optional

class View:
    """Simplified mock of ``discord.ui.View``."""
    def __init__(self, *items: Any):
        self.children = list(items)

    def add_item(self, item: Any) -> None:
        self.children.append(item)

class Button:
    """Simplified mock of ``discord.ui.Button``."""
    def __init__(self, label: str = "", style: int = 0, **kwargs: Any):
        self.label = label
        self.style = style
        self.kwargs = kwargs

class Select:
    """Simplified mock of ``discord.ui.Select``."""
    def __init__(self, placeholder: str = "", options: Optional[List[Any]] = None, **kwargs: Any):
        self.placeholder = placeholder
        self.options = options or []
        self.kwargs = kwargs
