import json
import time
from pathlib import Path
from agent_tools.agent_cellphone import direct_send_message

def send_test_messages():
    """Send test messages to all agents."""
    # Load agent coordinates
    coords_file = Path("runtime/config/cursor_agent_coords.json")
    with open(coords_file, 'r') as f:
        coordinates = json.load(f)
    
    # Get list of agents (excluding global_ui)
    agents = [agent for agent in coordinates.keys() if agent.startswith("Agent-")]
    
    # Send test message to each agent
    for agent in agents:
        print(f"\nSending test message to {agent}...")
        try:
            success = direct_send_message(agent, "Test message - please confirm receipt", mode="NORMAL")
            if success:
                print(f"[OK] Message sent to {agent}")
            else:
                print(f"[ERROR] Failed to send message to {agent}")
            # Add a small delay between messages
            time.sleep(2)
        except Exception as e:
            print(f"[ERROR] Error sending message to {agent}: {e}")
    
    print("\nTest message sending complete!")

if __name__ == "__main__":
    send_test_messages() 