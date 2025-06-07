"""
Script to test coordinate movements with visual feedback.
"""

import pyautogui
import keyboard
import time

# Known coordinates
AGENT1_INPUT = (-1173, 462)

def move_to_coords(x, y, duration=0.5):
    """Move to coordinates with visual feedback."""
    print(f"\nMoving to: ({x}, {y})")
    pyautogui.moveTo(x, y, duration=duration)
    current_x, current_y = pyautogui.position()
    print(f"Current position: ({current_x}, {current_y})")
    print(f"Distance from target: ({current_x - x}, {current_y - y})")

def main():
    print("\nCoordinate Test Tool")
    print("-------------------")
    print("1. Press '1' to move to Agent-1 Input Box")
    print("2. Press 'c' to check current coordinates")
    print("3. Press 'q' to quit")
    print("\nWaiting for commands...")

    try:
        while True:
            if keyboard.is_pressed('q'):
                print("\nExiting...")
                break
                
            if keyboard.is_pressed('1'):
                move_to_coords(*AGENT1_INPUT)
                time.sleep(0.5)  # Prevent multiple triggers
                
            if keyboard.is_pressed('c'):
                x, y = pyautogui.position()
                print(f"\nCurrent coordinates: ({x}, {y})")
                time.sleep(0.5)  # Prevent multiple triggers
                
            time.sleep(0.1)  # Reduce CPU usage
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("\nDone!")

if __name__ == "__main__":
    main() 