"""
Menu Builder Module

Builds the agent control menu interface.
"""

import logging
from typing import Optional, Dict, List, Any, Callable
from ..menu import MenuBuilder as BaseMenuBuilder, MenuItem, MenuItemType

logger = logging.getLogger('agent_control.menu_builder')

class MenuBuilder(BaseMenuBuilder):
    """Builds the agent control menu."""
    
    def __init__(self, actions: Optional[Dict[str, Callable]] = None):
        """Initialize the menu builder.
        
        Args:
            actions: Optional dictionary mapping action IDs to handler functions
        """
        super().__init__()
        self.actions = actions or {}
        self._build_menu()
        
    def _build_menu(self):
        """Build the menu structure."""
        # Main menu items
        self.add_item(MenuItem(
            id='list',
            label='List Agents',
            type=MenuItemType.COMMAND,
            action=lambda: self.menu.signals.item_selected.emit('list', None)
        ))
        
        # Add items for each action
        action_items = {
            'onboard': 'Onboard Agent',
            'resume': 'Resume Agent',
            'verify': 'Verify Agent',
            'repair': 'Repair Agent',
            'backup': 'Backup Agent',
            'restore': 'Restore Agent',
            'message': 'Send Message'
        }
        
        for action_id, label in action_items.items():
            self.add_item(MenuItem(
                id=action_id,
                label=label,
                type=MenuItemType.AGENT_SELECTION,
                action=lambda a=action_id: self.menu.signals.item_selected.emit(a, None)
            ))
        
    def _handle_agent_selection(self, item: MenuItem):
        """Handle agent selection for menu items.
        
        Args:
            item: The menu item that triggered the selection
        """
        # Get list of available agents
        agents = self.menu.coordinate_manager.list_agents()
        
        # Create submenu for agent selection
        submenu = MenuBuilder()
        for agent in agents:
            submenu.add_item(MenuItem(
                id=f"{item.id}_{agent}",
                label=agent,
                type=MenuItemType.COMMAND,
                action=lambda a=agent: item.action(a)
            ))
            
        # Show submenu
        submenu.display_menu()
        
    def display_menu(self) -> None:
        """Display the menu."""
        if self.menu:
            # Ensure menu is properly initialized
            if not self.menu.initialized:
                self.menu.setup_ui()
            self.menu.show()
            
    def connect_signals(self, handler: Callable[[str, Any], None]) -> None:
        """Connect menu signals to a handler.
        
        Args:
            handler: Function to handle menu item selection
        """
        if self.menu:
            self.menu.signals.item_selected.connect(handler)
            self.menu.signals.menu_closed.connect(lambda: logger.debug("Menu closed"))
            
    def disconnect_signals(self) -> None:
        """Disconnect all menu signals."""
        if self.menu:
            self.menu.signals.item_selected.disconnect() 