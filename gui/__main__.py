"""
Main Entry Point
--------------
Entry point for the GUI application.
"""

import sys
from PyQt5.QtWidgets import QApplication
from .main_window import MainWindow

def main():
    """Run the GUI application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 