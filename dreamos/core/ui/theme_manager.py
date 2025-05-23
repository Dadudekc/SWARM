"""
Theme Manager Module

Handles consistent UI theming across the application.
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class ThemeManager:
    """Manages application-wide UI theming."""
    
    @staticmethod
    def get_dialog_stylesheet() -> str:
        """Get the stylesheet for dialogs.
        
        Returns:
            CSS stylesheet string
        """
        return """
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            QLabel {
                color: #000000;
                font-size: 12px;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #b0b0b0;
                border-radius: 4px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #b0b0b0;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #b0b0b0;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #e0e0e0;
                color: #000000;
            }
        """
    
    @staticmethod
    def apply_dialog_theme(dialog) -> None:
        """Apply the dialog theme to a QDialog instance.
        
        Args:
            dialog: QDialog instance to theme
        """
        dialog.setStyleSheet(ThemeManager.get_dialog_stylesheet())
        
    @staticmethod
    def is_dark_theme() -> bool:
        """Check if the application is using a dark theme.
        
        Returns:
            True if dark theme is active
        """
        palette = QApplication.palette()
        window_color = palette.color(QPalette.Window)
        return window_color.lightness() < 128 