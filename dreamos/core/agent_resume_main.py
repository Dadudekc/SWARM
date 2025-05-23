"""
Agent Resume Main

Main interface for controlling agents through both menu and cursor control.
"""

import logging
import time
import pyautogui
import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum, auto
from datetime import datetime

from dreamos.core import CellPhone, Message, MessageMode
from dreamos.core.cursor_controller import CursorController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_resume')

class MessageMode(Enum):
    """Message modes for agent communication."""
    RESUME = "RESUME"
    SYNC = "SYNC"
    VERIFY = "VERIFY"
    REPAIR = "REPAIR"
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"
    CLEANUP = "CLEANUP"
    CAPTAIN = "CAPTAIN"
    TASK = "TASK"
    INTEGRATE = "INTEGRATE"
    NORMAL = "NORMAL"

class AgentResume:
    """Main agent control interface."""
    
    def __init__(self):
        """Initialize the agent control interface."""
        self.cell_phone = CellPhone()
        self.cursor = CursorController()
        self.coords = self._load_coordinates()
        
    def _load_coordinates(self) -> Dict:
        """Load cursor coordinates from JSON file."""
        try:
            # Use absolute path to the coordinates file
            config_path = Path("D:/SWARM/Dream.OS/runtime/config/cursor_agent_coords.json")
            
            if not config_path.exists():
                logger.error(f"Coordinates file not found at {config_path}")
                return {}
                
            with open(config_path, 'r') as f:
                coords = json.load(f)
                
            # Convert nested coordinate dictionaries to tuples
            processed_coords = {}
            for agent_id, agent_coords in coords.items():
                if agent_id == "global_ui":
                    continue
                    
                processed_coords[agent_id] = {
                    "input_box": (agent_coords["input_box"]["x"], agent_coords["input_box"]["y"]),
                    "initial_spot": (agent_coords["initial_spot"]["x"], agent_coords["initial_spot"]["y"]),
                    "copy_button": (agent_coords["copy_button"]["x"], agent_coords["copy_button"]["y"])
                }
                
            logger.info(f"Loaded coordinates for {len(processed_coords)} agents: {list(processed_coords.keys())}")
            return processed_coords
            
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            return {}

    def show_menu(self):
        """Display the main menu"""
        while True:
            print("\n" + "="*30)
            print("      Agent Cellphone Menu")
            print("="*30)
            print("1. List Available Agents")
            print("2. Onboard Agent")
            print("3. Resume Agent")
            print("4. Verify Agent State")
            print("5. Repair Agent State")
            print("6. Backup Agent State")
            print("7. Restore Agent State")
            print("8. Send Custom Message")
            print("9. Send to All Agents")
            print("0. Exit")
            print("="*30)
            
            try:
                choice = input("\nEnter your choice (0-9): ").strip()
                
                if choice == "0":
                    print("\nGoodbye!")
                    break
                elif choice == "1":
                    self.list_agents()
                elif choice == "2":
                    self.menu_onboard_agent()
                elif choice == "3":
                    self.menu_resume_agent()
                elif choice == "4":
                    self.menu_verify_agent()
                elif choice == "5":
                    self.menu_repair_agent()
                elif choice == "6":
                    self.menu_backup_agent()
                elif choice == "7":
                    self.menu_restore_agent()
                elif choice == "8":
                    self.menu_send_message()
                elif choice == "9":
                    self.menu_send_to_all()
                else:
                    print("\nInvalid choice. Please enter a number between 0 and 9.")
            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                break
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                logger.error(f"Menu error: {e}")

    def list_agents(self):
        """List all available agents"""
        print("\nAvailable Agents:")
        print("-" * 20)
        for agent_id in sorted(self.coords.keys()):
            print(f"- {agent_id}")
        print("-" * 20)

    def get_agent_selection(self) -> str:
        """Get agent selection from user"""
        self.list_agents()
        selection = input("\nEnter agent number (1-8), 0 for multiple agents, or 9 for all agents: ").strip()
        
        if selection == "9":
            return "all"
        elif selection == "0":
            # Handle multiple agent selection
            print("\nEnter agent numbers separated by commas (e.g., 1,3,5):")
            agent_nums = input().strip().split(',')
            selected_agents = []
            
            for num in agent_nums:
                try:
                    num = int(num.strip())
                    if 1 <= num <= 8:
                        selected_agents.append(f"Agent-{num}")
                    else:
                        print(f"Invalid agent number: {num}")
                except ValueError:
                    print(f"Invalid input: {num}")
            
            if not selected_agents:
                raise ValueError("No valid agents selected")
                
            return ",".join(selected_agents)
        
        try:
            num = int(selection)
            if 1 <= num <= 8:
                return f"Agent-{num}"
            else:
                raise ValueError("Invalid agent number")
        except ValueError:
            raise ValueError("Please enter a number between 1 and 9, or 0 for multiple agents")

    def send_to_all_agents(self, message: str, mode: MessageMode = MessageMode.NORMAL):
        """Send message to all agents"""
        for agent_id in self.coords.keys():
            try:
                self.send_message(agent_id, message, mode)
                print(f"Message sent to {agent_id}")
            except Exception as e:
                print(f"Error sending to {agent_id}: {e}")
                logger.error(f"Error sending to {agent_id}: {e}")

    def send_message(self, agent_id: str, message: str, mode: MessageMode = MessageMode.NORMAL):
        """Send a message to an agent using both cell phone script and cursor control."""
        try:
            # Send via cell phone script
            cmd = [
                sys.executable,
                str(Path("agent_tools/agent_cellphone.py")),
                "--to", agent_id,
                "--message", message,
                "--mode", mode.value
            ]
            
            logger.info(f"Executing cell phone command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                logger.error(f"Cell phone script error: {error_msg}")
                raise Exception(f"Failed to send message via cell phone: {error_msg}")
            
            logger.info(f"Message sent to {agent_id} via cell phone")
            
            # Send via cursor control if agent coordinates exist
            if agent_id in self.coords:
                coords = self.coords[agent_id]
                
                # Move to input box and click
                self.cursor.move_to(*coords["input_box"])
                self.cursor.click()
                
                # Type the message
                self.cursor.type_text(message)
                
                # Move to send button and click
                self.cursor.move_to(*coords["copy_button"])
                self.cursor.click()
                
                logger.info(f"Message sent to {agent_id} via cursor control")
            else:
                logger.warning(f"No coordinates found for {agent_id}, using cell phone only")
                
        except Exception as e:
            logger.error(f"Error sending message to {agent_id}: {e}")
            raise

    def menu_onboard_agent(self):
        """Handle agent onboarding through menu"""
        try:
            agent_selection = self.get_agent_selection()
            
            if agent_selection == "all":
                print("\nOnboarding all agents...")
                for agent_id in self.coords.keys():
                    self.onboard_single_agent(agent_id)
            elif "," in agent_selection:
                # Handle multiple agents
                agent_ids = agent_selection.split(",")
                print(f"\nOnboarding multiple agents: {', '.join(agent_ids)}")
                for agent_id in agent_ids:
                    self.onboard_single_agent(agent_id)
            else:
                self.onboard_single_agent(agent_selection)
                
        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            logger.error(f"Onboarding error: {e}")

    def onboard_single_agent(self, agent_id: str, message: str = ""):
        """Handle the onboarding sequence for a single agent.
        
        Sequence:
        1. Go to initial spot
        2. Click
        3. Press Ctrl+Enter
        4. Press Ctrl+N
        5. Send message chunks
        6. Press Enter
        """
        try:
            if agent_id not in self.coords:
                logger.warning(f"No coordinates found for {agent_id}, using cell phone only")
                self.send_message(agent_id, message, MessageMode.NORMAL)
                return

            coords = self.coords[agent_id]
            logger.info(f"Starting onboarding sequence for {agent_id}")

            # 1. Go to initial spot
            logger.debug(f"Moving to initial position for {agent_id}")
            self.cursor.move_to(*coords["initial_spot"])
            time.sleep(0.2)  # Small delay for stability

            # 2. Click
            logger.debug("Clicking at position")
            self.cursor.click()
            time.sleep(0.2)

            # 3. Press Ctrl+Enter
            logger.debug("Pressing Ctrl+Enter")
            self.cursor.press_ctrl_enter()
            time.sleep(0.3)  # Slightly longer delay for window creation

            # 4. Press Ctrl+N
            logger.debug("Pressing Ctrl+N")
            self.cursor.press_ctrl_n()
            time.sleep(0.3)

            # 5. Send message chunks
            logger.debug("Sending message chunks")
            chunks = self.split_message(message)
            for i, chunk in enumerate(chunks, 1):
                logger.debug(f"Sending chunk {i}/{len(chunks)}")
                self.cursor.type_text(chunk)
                time.sleep(0.2)  # Small delay between typing
                if i < len(chunks):  # Don't press enter after the last chunk
                    self.cursor.press_enter()
                    time.sleep(0.3)

            # 6. Press Enter for final chunk
            logger.debug("Pressing Enter for final chunk")
            self.cursor.press_enter()
            time.sleep(0.2)

            logger.info(f"Onboarding sequence completed for {agent_id}")

            # Also send via cell phone as backup
            logger.debug("Sending backup message via cell phone")
            self.send_message(agent_id, message, MessageMode.NORMAL)

        except Exception as e:
            logger.error(f"Error in onboarding sequence for {agent_id}: {e}")
            # Try to send via cell phone as fallback
            try:
                logger.info("Attempting fallback to cell phone only")
                self.send_message(agent_id, message, MessageMode.NORMAL)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
            raise

    def split_message(self, message: str, max_length: int = 100) -> List[str]:
        """Split a message into chunks of maximum length.
        
        Args:
            message: The message to split
            max_length: Maximum length of each chunk
            
        Returns:
            List of message chunks
        """
        words = message.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            # Check if adding this word would exceed max_length
            if current_length + len(word) + 1 <= max_length:
                current_chunk.append(word)
                current_length += len(word) + 1
            else:
                # Current chunk is full, add it to chunks
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    def menu_resume_agent(self):
        """Handle agent resume through menu"""
        try:
            agent_selection = self.get_agent_selection()
            
            if agent_selection == "all":
                print("\nResuming all agents...")
                for agent_id in self.coords.keys():
                    self.send_message(agent_id, "RESUME", MessageMode.RESUME)
                    print(f"Resume command sent to {agent_id}")
            elif "," in agent_selection:
                # Handle multiple agents
                agent_ids = agent_selection.split(",")
                print(f"\nResuming multiple agents: {', '.join(agent_ids)}")
                for agent_id in agent_ids:
                    self.send_message(agent_id, "RESUME", MessageMode.RESUME)
                    print(f"Resume command sent to {agent_id}")
            else:
                self.send_message(agent_selection, "RESUME", MessageMode.RESUME)
                print(f"Resume command sent to {agent_selection}")
                
        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            logger.error(f"Resume error: {e}")

    def menu_verify_agent(self):
        """Handle agent verification through menu"""
        try:
            agent_selection = self.get_agent_selection()
            
            if agent_selection == "all":
                print("\nVerifying all agents...")
                for agent_id in self.coords.keys():
                    self.send_message(agent_id, "VERIFY", MessageMode.VERIFY)
                    print(f"Verify command sent to {agent_id}")
            elif "," in agent_selection:
                # Handle multiple agents
                agent_ids = agent_selection.split(",")
                print(f"\nVerifying multiple agents: {', '.join(agent_ids)}")
                for agent_id in agent_ids:
                    self.send_message(agent_id, "VERIFY", MessageMode.VERIFY)
                    print(f"Verify command sent to {agent_id}")
            else:
                self.send_message(agent_selection, "VERIFY", MessageMode.VERIFY)
                print(f"Verify command sent to {agent_selection}")
                
        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            logger.error(f"Verify error: {e}")

    def menu_repair_agent(self):
        """Handle agent repair through menu"""
        try:
            agent_selection = self.get_agent_selection()
            
            if agent_selection == "all":
                print("\nRepairing all agents...")
                for agent_id in self.coords.keys():
                    self.send_message(agent_id, "REPAIR", MessageMode.REPAIR)
                    print(f"Repair command sent to {agent_id}")
            elif "," in agent_selection:
                # Handle multiple agents
                agent_ids = agent_selection.split(",")
                print(f"\nRepairing multiple agents: {', '.join(agent_ids)}")
                for agent_id in agent_ids:
                    self.send_message(agent_id, "REPAIR", MessageMode.REPAIR)
                    print(f"Repair command sent to {agent_id}")
            else:
                self.send_message(agent_selection, "REPAIR", MessageMode.REPAIR)
                print(f"Repair command sent to {agent_selection}")
                
        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            logger.error(f"Repair error: {e}")

    def menu_backup_agent(self):
        """Handle agent backup through menu"""
        try:
            agent_selection = self.get_agent_selection()
            
            if agent_selection == "all":
                print("\nBacking up all agents...")
                for agent_id in self.coords.keys():
                    self.send_message(agent_id, "BACKUP", MessageMode.BACKUP)
                    print(f"Backup command sent to {agent_id}")
            elif "," in agent_selection:
                # Handle multiple agents
                agent_ids = agent_selection.split(",")
                print(f"\nBacking up multiple agents: {', '.join(agent_ids)}")
                for agent_id in agent_ids:
                    self.send_message(agent_id, "BACKUP", MessageMode.BACKUP)
                    print(f"Backup command sent to {agent_id}")
            else:
                self.send_message(agent_selection, "BACKUP", MessageMode.BACKUP)
                print(f"Backup command sent to {agent_selection}")
                
        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            logger.error(f"Backup error: {e}")

    def menu_restore_agent(self):
        """Handle agent restore through menu"""
        try:
            agent_selection = self.get_agent_selection()
            
            if agent_selection == "all":
                print("\nRestoring all agents...")
                for agent_id in self.coords.keys():
                    self.send_message(agent_id, "RESTORE", MessageMode.RESTORE)
                    print(f"Restore command sent to {agent_id}")
            elif "," in agent_selection:
                # Handle multiple agents
                agent_ids = agent_selection.split(",")
                print(f"\nRestoring multiple agents: {', '.join(agent_ids)}")
                for agent_id in agent_ids:
                    self.send_message(agent_id, "RESTORE", MessageMode.RESTORE)
                    print(f"Restore command sent to {agent_id}")
            else:
                self.send_message(agent_selection, "RESTORE", MessageMode.RESTORE)
                print(f"Restore command sent to {agent_selection}")
                
        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            logger.error(f"Restore error: {e}")

    def menu_send_message(self):
        """Handle sending custom message through menu"""
        try:
            agent_selection = self.get_agent_selection()
            message = input("\nEnter your message: ").strip()
            
            if not message:
                print("\nMessage cannot be empty")
                return
                
            if agent_selection == "all":
                print("\nSending message to all agents...")
                self.send_to_all_agents(message)
            elif "," in agent_selection:
                # Handle multiple agents
                agent_ids = agent_selection.split(",")
                print(f"\nSending message to multiple agents: {', '.join(agent_ids)}")
                for agent_id in agent_ids:
                    self.send_message(agent_id, message)
                    print(f"Message sent to {agent_id}")
            else:
                self.send_message(agent_selection, message)
                print(f"Message sent to {agent_selection}")
                
        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            logger.error(f"Send message error: {e}")

    def menu_send_to_all(self):
        """Handle sending message to all agents through menu"""
        try:
            message = input("Enter message to broadcast: ").strip()
            mode = input("Enter mode (resume/sync/verify/repair/backup/restore/normal) [default: normal]: ").strip().lower()
            
            mode_map = {
                "resume": MessageMode.RESUME,
                "sync": MessageMode.SYNC,
                "verify": MessageMode.VERIFY,
                "repair": MessageMode.REPAIR,
                "backup": MessageMode.BACKUP,
                "restore": MessageMode.RESTORE,
                "normal": MessageMode.NORMAL
            }
            
            selected_mode = mode_map.get(mode, MessageMode.NORMAL)
            self.send_to_all_agents(message, selected_mode)
            print(f"Message sent to all agents with mode {selected_mode.value}")
        except Exception as e:
            print(f"Error broadcasting message: {e}")
            logger.error(f"Broadcast error: {e}")

    def run(self):
        """Run the menu interface."""
        try:
            self.show_menu()
        finally:
            # Cleanup
            self.cell_phone.shutdown()
            logger.info("Menu interface closed")

def main():
    """Main entry point."""
    menu = AgentResume()
    menu.run()

if __name__ == "__main__":
    main() 