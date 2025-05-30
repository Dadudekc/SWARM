#!/usr/bin/env python3
"""
Dream.OS Menu Runner

Entry point for running the Dream.OS agent menu interface.
"""

import os
import sys
from dreamos.core.agent_control.menu_builder import MenuBuilder


def main():
    """Run the agent menu interface."""
    try:
        menu = MenuBuilder()
        menu.display_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 