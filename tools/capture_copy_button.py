"""
Tool to capture the copy button template for training.

This script helps capture screenshots of the copy button in Cursor
for use with the response collector's template matching.
"""

import os
import time
import logging
import pyautogui
from pathlib import Path
import cv2
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def capture_template(region: tuple, output_dir: str = "templates") -> bool:
    """Capture a template image from the specified region.
    
    Args:
        region: (left, top, right, bottom) coordinates to capture
        output_dir: Directory to save the template
        
    Returns:
        True if capture was successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Ensure coordinates are in correct order
        left = min(region[0], region[2])
        right = max(region[0], region[2])
        top = min(region[1], region[3])
        bottom = max(region[1], region[3])
        
        # Capture screenshot
        screenshot = pyautogui.screenshot(region=(left, top, right-left, bottom-top))
        screenshot_np = np.array(screenshot)
        screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        # Save template
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        template_path = os.path.join(output_dir, f"copy_button_{timestamp}.png")
        cv2.imwrite(template_path, screenshot_np)
        
        logger.info(f"Saved template to {template_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error capturing template: {e}")
        return False

def main():
    """Run the template capture tool."""
    print("\n=== Copy Button Template Capture Tool ===")
    print("This tool will help you capture the copy button template.")
    print("\nInstructions:")
    print("1. Position your mouse over the top-left corner of the region")
    print("2. Press Enter to capture that position")
    print("3. Move your mouse to the bottom-right corner of the region")
    print("4. Press Enter to capture that position")
    print("5. The template will be saved in the templates directory")
    print("\nPress Ctrl+C to exit")
    
    try:
        while True:
            input("\nPress Enter when your mouse is over the top-left corner...")
            x1, y1 = pyautogui.position()
            print(f"Captured top-left: ({x1}, {y1})")
            
            input("Press Enter when your mouse is over the bottom-right corner...")
            x2, y2 = pyautogui.position()
            print(f"Captured bottom-right: ({x2}, {y2})")
            
            region = (x1, y1, x2, y2)
            if capture_template(region):
                print("✅ Template captured successfully!")
            else:
                print("❌ Failed to capture template")
            
            time.sleep(0.5)  # Brief pause
            
    except KeyboardInterrupt:
        print("\nTool stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("\nTool complete!")

if __name__ == "__main__":
    main() 