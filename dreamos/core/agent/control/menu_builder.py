"""
Menu Builder Module

Builds the agent control menu interface.
"""

import logging
from typing import Optional, Dict, List, Any, Callable
from ..menu import MenuBuilder as BaseMenuBuilder, MenuItem, MenuItemType, Menu

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
        self.menu = None  # Initialize menu as None
        self._controller = None  # Initialize controller as None
        self._build_menu()
        
    def set_controller(self, controller: Any) -> None:
        """Set the controller for the menu.
        
        Args:
            controller: The controller instance to use
        """
        self._controller = controller
        if self.menu:
            self.menu.controller = controller
            logger.info("Controller set for menu")
        
    def _handle_menu_action(self, action_id: str, agent_id: Optional[str] = None) -> None:
        """Handle menu action selection.
        
        Args:
            action_id: The ID of the selected action
            agent_id: Optional agent ID if action requires agent selection
        """
        if not self._controller:
            logger.error("No controller available for menu action")
            return
            
        if action_id == 'list':
            self._handle_list_agents()
        elif agent_id:
            if hasattr(self._controller, action_id):
                handler = getattr(self._controller, action_id)
                handler(agent_id)
            else:
                logger.error(f"No handler found for action: {action_id}")
        else:
            self._handle_agent_selection(self.menu.get_item(action_id))
            
    def cleanup(self) -> None:
        """Clean up menu resources."""
        if self.menu:
            try:
                self.disconnect_signals()
                self.menu.cleanup()
                self.menu = None
                self._controller = None
                logger.info("Menu resources cleaned up")
            except Exception as e:
                logger.error(f"Error during menu cleanup: {str(e)}")
            
    def _build_menu(self):
        """Build the menu structure."""
        # Create new menu instance
        self.menu = Menu()
        
        # Main menu items
        self.add_item(MenuItem(
            id='list',
            label='List Agents',
            type=MenuItemType.COMMAND,
            action=lambda: self._handle_menu_action('list')
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
                action=lambda a=action_id: self._handle_menu_action(a)
            ))
            
    def _handle_list_agents(self):
        """Handle list agents action."""
        if not self._controller:
            logger.error("No controller available for listing agents")
            return
            
        try:
            agents = self._controller.list_agents()
            if self.menu and hasattr(self.menu, 'signals'):
                self.menu.signals.item_selected.emit('list', agents)
            logger.info(f"Listed {len(agents)} agents")
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            
    def _handle_agent_selection(self, item: MenuItem):
        """Handle agent selection for menu items.
        
        Args:
            item: The menu item that triggered the selection
        """
        if not self._controller:
            logger.error("No controller available for agent selection")
            return
            
        try:
            agents = self._controller.list_agents()
            
            # Create submenu for agent selection
            submenu = MenuBuilder()
            for agent in agents:
                submenu.add_item(MenuItem(
                    id=f"{item.id}_{agent}",
                    label=agent,
                    type=MenuItemType.COMMAND,
                    action=lambda a=agent: self._handle_menu_action(item.id, a)
                ))
                
            # Show submenu
            submenu.display_menu()
            logger.info(f"Showing agent selection menu for action: {item.id}")
        except Exception as e:
            logger.error(f"Error handling agent selection: {str(e)}")
            
    def display_menu(self) -> None:
        """Display the menu."""
        if self.menu:
            try:
                # Ensure menu is properly initialized
                if not self.menu.initialized:
                    self.menu.setup_ui()
                self.menu.show()
                logger.info("Menu displayed")
            except Exception as e:
                logger.error(f"Error displaying menu: {str(e)}")
            
    def connect_signals(self, handler: Callable[[str, Any], None]) -> None:
        """Connect menu signals to a handler.
        
        Args:
            handler: Function to handle menu item selection
        """
        if self.menu:
            try:
                self.menu.signals.item_selected.connect(handler)
                self.menu.signals.menu_closed.connect(lambda: logger.debug("Menu closed"))
                logger.info("Menu signals connected")
            except Exception as e:
                logger.error(f"Error connecting menu signals: {str(e)}")
            
    def disconnect_signals(self) -> None:
        """Disconnect menu signals."""
        if self.menu:
            try:
                self.menu.signals.item_selected.disconnect()
                self.menu.signals.menu_closed.disconnect()
                logger.info("Menu signals disconnected")
            except (TypeError, RuntimeError) as e:
                logger.debug(f"Error disconnecting signals (may be already disconnected): {str(e)}") 
