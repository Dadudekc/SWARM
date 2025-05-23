"""
Menu Interface

Provides a user-friendly menu interface for interacting with the Dream.OS system.
"""

import logging
import os
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum, auto

logger = logging.getLogger('menu')

class MenuItemType(Enum):
    """Types of menu items."""
    COMMAND = auto()
    SUBMENU = auto()
    TOGGLE = auto()
    INPUT = auto()

@dataclass
class MenuItem:
    """Represents a menu item with its properties."""
    id: str
    label: str
    type: MenuItemType
    action: Optional[Callable] = None
    submenu: Optional['Menu'] = None
    description: str = ""
    shortcut: Optional[str] = None
    enabled: bool = True
    visible: bool = True

class Menu:
    """Main menu interface class.
    
    Provides methods for creating and managing menu items, handling user input,
    and displaying the menu interface.
    """
    
    def __init__(self, title: str = "Dream.OS Menu"):
        """Initialize the menu interface.
        
        Args:
            title: The title of the menu
        """
        self.title = title
        self.items: Dict[str, MenuItem] = {}
        self.parent: Optional[Menu] = None
        self._current_selection = 0
        
    def add_item(self, item: MenuItem) -> None:
        """Add a menu item.
        
        Args:
            item: The MenuItem to add
        """
        if item.id in self.items:
            logger.warning(f"Menu item with id {item.id} already exists")
            return
            
        self.items[item.id] = item
        if item.type == MenuItemType.SUBMENU and item.submenu:
            item.submenu.parent = self
            
    def remove_item(self, item_id: str) -> None:
        """Remove a menu item.
        
        Args:
            item_id: The ID of the item to remove
        """
        if item_id in self.items:
            del self.items[item_id]
            
    def get_item(self, item_id: str) -> Optional[MenuItem]:
        """Get a menu item by ID.
        
        Args:
            item_id: The ID of the item to get
            
        Returns:
            The MenuItem if found, None otherwise
        """
        return self.items.get(item_id)
        
    def display(self) -> None:
        """Display the menu interface."""
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
        print(f"\n{self.title}")
        print("=" * len(self.title))
        
        visible_items = [item for item in self.items.values() if item.visible]
        for i, item in enumerate(visible_items):
            prefix = "→ " if i == self._current_selection else "  "
            shortcut = f" [{item.shortcut}]" if item.shortcut else ""
            print(f"{prefix}{item.label}{shortcut}")
            if item.description:
                print(f"    {item.description}")
                
        print("\nNavigation: ↑/↓ to move, Enter to select, 'q' to quit")
                
    def handle_input(self, key: str) -> Optional[Any]:
        """Handle user input.
        
        Args:
            key: The key pressed by the user
            
        Returns:
            The result of the action if any
        """
        visible_items = [item for item in self.items.values() if item.visible]
        if not visible_items:
            return None
            
        current_item = visible_items[self._current_selection]
        
        # Handle navigation
        if key == "up" or key == "w":
            self._current_selection = (self._current_selection - 1) % len(visible_items)
            return None
        elif key == "down" or key == "s":
            self._current_selection = (self._current_selection + 1) % len(visible_items)
            return None
        elif key == "enter" or key == "":
            if current_item.type == MenuItemType.COMMAND and current_item.action:
                return current_item.action()
            elif current_item.type == MenuItemType.SUBMENU and current_item.submenu:
                return current_item.submenu.run()
            elif current_item.type == MenuItemType.TOGGLE:
                current_item.enabled = not current_item.enabled
                return current_item.enabled
            elif current_item.type == MenuItemType.INPUT:
                # Handle input collection
                pass
                
        # Handle shortcuts
        for item in visible_items:
            if item.shortcut and key.lower() == item.shortcut.lower():
                if item.type == MenuItemType.COMMAND and item.action:
                    return item.action()
                elif item.type == MenuItemType.SUBMENU and item.submenu:
                    return item.submenu.run()
                    
        return None
        
    def run(self) -> Optional[Any]:
        """Run the menu interface.
        
        Returns:
            The result of the selected action if any
        """
        while True:
            self.display()
            key = input("\nEnter command (or 'q' to quit): ").strip()
            
            if key.lower() == 'q':
                return None
                
            result = self.handle_input(key)
            if result == '__exit__':
                return None 