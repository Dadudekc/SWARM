"""
Menu System Module

Provides a modular menu system with different styles and components.
"""

from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum, auto
import logging
import warnings
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QScrollArea, QFrame, QSizePolicy, QSpacerItem, QHBoxLayout
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette
from .ui.agent_status_panel import AgentStatusPanel
from .ui.log_console import LogConsole

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

logger = logging.getLogger(__name__)

class MenuStyle(Enum):
    """Available menu styles."""
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"

class MenuItemType(Enum):
    """Types of menu items."""
    COMMAND = auto()
    SUBMENU = auto()
    TOGGLE = auto()
    INPUT = auto()
    AGENT_SELECTION = auto()

@dataclass
class MenuItem:
    """Represents a menu item with its properties."""
    label: str
    description: str = ""
    action: Optional[Callable] = None
    shortcut: Optional[str] = None
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    type: MenuItemType = MenuItemType.COMMAND
    submenu: Optional['Menu'] = None
    agent_id: Optional[str] = None
    id: Optional[str] = None  # Added id field for menu item identification

class MenuTheme:
    """Handles menu theming and styling."""
    
    def __init__(self, style: MenuStyle = MenuStyle.DARK):
        self.style = style
        self.colors = self._get_theme_colors()
        self.fonts = self._get_theme_fonts()
        
    def _get_theme_colors(self) -> Dict[str, str]:
        """Get color scheme based on selected style."""
        if self.style == MenuStyle.DARK:
            return {
                "background": "#1e1e1e",
                "foreground": "#ffffff",
                "accent": "#007acc",
                "hover": "#2d2d2d",
                "disabled": "#666666",
                "border": "#3c3c3c"
            }
        elif self.style == MenuStyle.LIGHT:
            return {
                "background": "#ffffff",
                "foreground": "#000000",
                "accent": "#0078d4",
                "hover": "#f0f0f0",
                "disabled": "#999999",
                "border": "#e0e0e0"
            }
        else:  # SYSTEM
            return {
                "background": "system",
                "foreground": "system",
                "accent": "system",
                "hover": "system",
                "disabled": "system",
                "border": "system"
            }

    def _get_theme_fonts(self) -> Dict[str, QFont]:
        """Get font settings based on selected style."""
        base_font = QFont("Segoe UI", 10)
        return {
            "title": QFont("Segoe UI", 14, QFont.Bold),
            "item": base_font,
            "description": QFont("Segoe UI", 9),
            "footer": QFont("Segoe UI", 8)
        }

class MenuButton(QPushButton):
    """Custom button widget for menu items."""
    
    def __init__(self, item: MenuItem, theme: MenuTheme, parent=None):
        super().__init__(parent)
        self.item = item
        self.theme = theme
        self.setup_ui()
        
    def setup_ui(self):
        """Set up button appearance and behavior."""
        self.setText(self.item.label)
        self.setToolTip(self.item.description)
        self.setFont(self.theme.fonts["item"])
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        
        # Set style
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.colors["background"]};
                color: {self.theme.colors["foreground"]};
                border: 1px solid {self.theme.colors["border"]};
                border-radius: 4px;
                padding: 8px 16px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {self.theme.colors["hover"]};
            }}
            QPushButton:disabled {{
                color: {self.theme.colors["disabled"]};
            }}
        """)
        
        # Connect click handler
        if self.item.action:
            self.clicked.connect(self.item.action)

class MenuHeader(QFrame):
    """Header widget for the menu."""
    
    def __init__(self, title: str, theme: MenuTheme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setup_ui(title)
        
    def setup_ui(self, title: str):
        """Set up header appearance."""
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel(title)
        title_label.setFont(self.theme.fonts["title"])
        title_label.setStyleSheet(f"color: {self.theme.colors['foreground']};")
        layout.addWidget(title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {self.theme.colors['border']};")
        layout.addWidget(separator)
        
        self.setLayout(layout)

class MenuFooter(QFrame):
    """Footer widget for the menu."""
    
    def __init__(self, theme: MenuTheme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setup_ui()
        
    def setup_ui(self):
        """Set up footer appearance."""
        layout = QVBoxLayout(self)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {self.theme.colors['border']};")
        layout.addWidget(separator)
        
        # Footer text
        footer_label = QLabel("Press ESC to exit")
        footer_label.setFont(self.theme.fonts["footer"])
        footer_label.setStyleSheet(f"color: {self.theme.colors['foreground']};")
        footer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer_label)
        
        self.setLayout(layout)

class MenuSignals(QObject):
    """Signal handler for menu events."""
    item_selected = pyqtSignal(object, object)  # Emits (item_id, data) when selected
    menu_closed = pyqtSignal()  # Emits when menu is closed
    log_message = pyqtSignal(str, str)  # Emits (message, level) for logging

class Menu(QMainWindow):
    """Main menu window class."""
    
    _instance = None
    _app = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Menu, cls).__new__(cls)
            # Initialize instance attributes
            cls._instance.initialized = False
            cls._instance.title = kwargs.get('title', "Dream.OS Menu")
            cls._instance.items = {}
            cls._instance.parent = None
            cls._instance.signals = None  # Will be initialized in __init__
            cls._instance._menu_container = None
            cls._instance._menu_layout = None
            cls._instance._status_panel = None
            cls._instance._log_console = None
            cls._instance._theme = None  # Will be initialized in __init__
            cls._instance.controller = None  # Will store the controller reference
        return cls._instance
    
    def __init__(self, title: str = "Dream.OS Menu"):
        """Initialize the menu window."""
        # Only initialize once
        if not self.initialized:
            # Ensure QApplication exists
            if Menu._app is None:
                Menu._app = QApplication.instance()
                if Menu._app is None:
                    Menu._app = QApplication([])
            
            # Call parent's __init__
            super().__init__()
            
            # Initialize theme
            self._theme = MenuTheme(MenuStyle.DARK)
            
            # Initialize signals after parent initialization
            self.signals = MenuSignals()
            
            self.setup_ui()
            self.initialized = True
            
    def setup_ui(self):
        """Set up the main window UI."""
        # Window properties
        self.setWindowTitle(self.title)
        self.setMinimumSize(800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Left panel (menu)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title label
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 20px;")
        left_layout.addWidget(title_label)
        
        # Scroll area for menu items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3b3b3b;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Container for menu items
        self._menu_container = QWidget()
        self._menu_layout = QVBoxLayout(self._menu_container)
        self._menu_layout.setSpacing(10)
        self._menu_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._menu_container)
        left_layout.addWidget(scroll)
        
        # Right panel (status and logs)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        # Agent status panel
        self._status_panel = AgentStatusPanel()
        right_layout.addWidget(self._status_panel)
        
        # Log console
        self._log_console = LogConsole()
        right_layout.addWidget(self._log_console)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
            }
        """)
        
        # Connect log signal
        self.signals.log_message.connect(self._log_console.log)
        
        # Add exit button
        exit_button = QPushButton("Exit")
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        exit_button.clicked.connect(self.close)
        left_layout.addWidget(exit_button)
        
    def add_item(self, item: MenuItem) -> None:
        """Add a menu item."""
        if item.id in self.items:
            logger.warning(f"Menu item with id {item.id} already exists")
            return
            
        self.items[item.id] = item
        
        # Create and add button
        button = MenuButton(item, self._theme)
        button.clicked.connect(lambda: self.handle_item_click(item))
        self._menu_layout.addWidget(button)
        
        if item.type == MenuItemType.SUBMENU and item.submenu:
            item.submenu.parent = self
            
    def handle_item_click(self, item: MenuItem):
        """Handle menu item click."""
        if not item.enabled:
            return
            
        if item.type == MenuItemType.COMMAND and item.action:
            item.action()
            self.signals.item_selected.emit(item.id, None)
        elif item.type == MenuItemType.SUBMENU and item.submenu:
            item.submenu.show()
        elif item.type == MenuItemType.TOGGLE:
            item.enabled = not item.enabled
            # Update button state
            for i in range(self._menu_layout.count()):
                widget = self._menu_layout.itemAt(i).widget()
                if isinstance(widget, MenuButton) and widget.item.id == item.id:
                    widget.setEnabled(item.enabled)
                    break
        elif item.type == MenuItemType.AGENT_SELECTION:
            self._handle_agent_selection(item)
            
    def _handle_agent_selection(self, item: MenuItem):
        """Handle agent selection menu items.
        
        Args:
            item: The menu item that triggered the selection
        """
        if hasattr(self, 'controller') and self.controller:
            # Get list of available agents from the controller
            agents = self.controller.list_agents()
            
            # Create submenu for agent selection
            submenu = Menu("Select Agent")
            for agent in agents:
                submenu.add_item(MenuItem(
                    id=f"{item.id}_{agent}",
                    label=agent,
                    type=MenuItemType.COMMAND,
                    action=lambda a=agent: self.signals.item_selected.emit(item.id, a)
                ))
                
            # Show submenu
            submenu.show()
        else:
            logger.error("Controller not available for agent selection")
            
    def show(self):
        """Show the menu window."""
        if not self.isVisible():
            super().show()
            # Ensure window stays on top
            self.raise_()
            self.activateWindow()
        
    def run(self):
        """Run the menu event loop."""
        if Menu._app:
            # Show the window if not visible
            if not self.isVisible():
                self.show()
            # Start the event loop
            Menu._app.exec_()
            
    def _cleanup(self):
        """Clean up resources."""
        try:
            # Clean up status panel
            if self._status_panel:
                try:
                    self._status_panel.cleanup()
                except AttributeError:
                    pass  # Ignore if cleanup method doesn't exist
                
            # Clean up log console
            if self._log_console:
                try:
                    self._log_console.cleanup()
                except AttributeError:
                    pass  # Ignore if cleanup method doesn't exist
                
            # Clean up signals
            if self.signals:
                self.signals.deleteLater()
                
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")
            
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            # Emit menu closed signal
            if self.signals:
                self.signals.menu_closed.emit()
            
            # Clean up controller if exists
            if self.controller:
                self.controller.cleanup()
            
            # Clean up resources
            self._cleanup()
            
            # Accept the close event
            event.accept()
            
            # Quit the application
            if Menu._app:
                Menu._app.quit()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            event.accept()
            
    def __del__(self):
        """Clean up resources."""
        self._cleanup()

    def set_controller(self, controller):
        """Set the controller reference."""
        self.controller = controller

class MenuBuilder:
    """Builds and manages menu instances."""
    
    def __init__(self):
        """Initialize the menu builder."""
        self.menu = Menu()  # Get singleton instance
        
    def add_item(self, item: MenuItem) -> 'MenuBuilder':
        """Add a menu item."""
        self.menu.add_item(item)
        return self
        
    def add_items(self, items: List[MenuItem]) -> 'MenuBuilder':
        """Add multiple menu items."""
        for item in items:
            self.menu.add_item(item)
        return self
        
    def build(self) -> Menu:
        """Build and return the menu instance."""
        return self.menu
        
    def display_menu(self):
        """Display the menu."""
        if self.menu:
            self.menu.show()
            
    def close_menu(self):
        """Close the menu."""
        if self.menu:
            self.menu.hide()

def main():
    """Example usage of the menu system."""
    # Create a menu using the builder pattern
    menu = (MenuBuilder()
        .add_item(MenuItem(label="System Status", action=lambda: print("Checking system status...")))
        .add_item(MenuItem(label="Agent Control", action=lambda: print("Opening agent control...")))
        .add_item(MenuItem(label="Settings", action=lambda: print("Opening settings...")))
        .add_item(MenuItem(label="Help", description="View system documentation", action=lambda: print("Opening help...")))
        .add_item(MenuItem(label="Exit", action=lambda: QApplication.instance().quit()))
        .build())
    
    # Run the menu
    menu.run()

if __name__ == "__main__":
    main() 