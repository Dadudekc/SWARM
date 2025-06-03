import json
import pyautogui
import time
from pathlib import Path

def get_mouse_position():
    """Get current mouse position."""
    x, y = pyautogui.position()
    print(f"Current position: x={x}, y={y}")
    return x, y

def calibrate_agent(agent_number: int):
    """Calibrate coordinates for specified agent.
    
    Args:
        agent_number: The agent number to calibrate (1-8)
    """
    agent_id = f"Agent-{agent_number}"
    print(f"Starting calibration for {agent_id}...")
    print("Please move your mouse to each position when prompted.")
    
    # Get input box coordinates
    print(f"\nMove mouse to {agent_id}'s input box and press Enter...")
    input()
    input_box_x, input_box_y = get_mouse_position()
    
    # Get copy button coordinates
    print(f"\nMove mouse to {agent_id}'s copy button and press Enter...")
    input()
    copy_button_x, copy_button_y = get_mouse_position()
    
    # Get initial spot coordinates
    print(f"\nMove mouse to {agent_id}'s initial spot and press Enter...")
    input()
    initial_spot_x, initial_spot_y = get_mouse_position()
    
    # Load existing coordinates
    coords_file = Path("runtime/config/cursor_agent_coords.json")
    with open(coords_file, 'r') as f:
        coordinates = json.load(f)
    
    # Update agent coordinates
    coordinates[agent_id] = {
        "input_box": {
            "x": input_box_x,
            "y": input_box_y
        },
        "copy_button": {
            "x": copy_button_x,
            "y": copy_button_y
        },
        "input_box_initial": {
            "x": initial_spot_x,
            "y": initial_spot_y
        },
        "initial_spot": {
            "x": initial_spot_x,
            "y": initial_spot_y
        }
    }
    
    # Save updated coordinates
    with open(coords_file, 'w') as f:
        json.dump(coordinates, f, indent=2)
    
    print("\nCoordinates updated successfully!")
    print(f"New coordinates for {agent_id}:")
    print(f"Input box: ({input_box_x}, {input_box_y})")
    print(f"Copy button: ({copy_button_x}, {copy_button_y})")
    print(f"Initial spot: ({initial_spot_x}, {initial_spot_y})")

def calibrate_multiple_agents(start: int, end: int):
    """Calibrate multiple agents in sequence.
    
    Args:
        start: Starting agent number
        end: Ending agent number
    """
    for agent_num in range(start, end + 1):
        print(f"\n=== Calibrating Agent-{agent_num} ===")
        calibrate_agent(agent_num)
        print("\nPress Enter to continue to next agent...")
        input()

if __name__ == "__main__":
    print("Agent Coordinate Calibration Tool")
    print("1. Calibrate single agent")
    print("2. Calibrate multiple agents")
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "1":
        agent_num = int(input("Enter agent number (1-8): "))
        if 1 <= agent_num <= 8:
            calibrate_agent(agent_num)
        else:
            print("Invalid agent number. Must be between 1 and 8.")
    elif choice == "2":
        start = int(input("Enter starting agent number (1-8): "))
        end = int(input("Enter ending agent number (1-8): "))
        if 1 <= start <= 8 and 1 <= end <= 8 and start <= end:
            calibrate_multiple_agents(start, end)
        else:
            print("Invalid agent numbers. Must be between 1 and 8, and start must be less than or equal to end.")
    else:
        print("Invalid choice. Please enter 1 or 2.") 