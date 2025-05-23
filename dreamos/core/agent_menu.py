"""
Agent Menu Interface

Provides a unified menu interface for interacting with the Dream.OS agent system.
"""

import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum, auto
from datetime import datetime

from .cell_phone import CellPhone, Message, MessageMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_menu')

class AgentMenu:
    """Main agent menu interface class."""
    
    def __init__(self):
        """Initialize the agent menu interface."""
        self.cell_phone = CellPhone()
        
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
        for i in range(1, 9):
            print(f"Agent-{i}")
        print("-" * 20)

    def get_agent_selection(self) -> str:
        """Get agent selection from user"""
        self.list_agents()
        selection = input("\nEnter agent number (1-8) or 9 for all agents: ").strip()
        
        if selection == "9":
            return "all"
        
        try:
            num = int(selection)
            if 1 <= num <= 8:
                return f"Agent-{num}"
            else:
                raise ValueError("Invalid agent number")
        except ValueError:
            raise ValueError("Please enter a number between 1 and 9")

    def send_to_all_agents(self, message: str, mode: MessageMode = MessageMode.NORMAL):
        """Send message to all agents"""
        agents = [f"Agent-{i}" for i in range(1, 9)]
        for agent_id in agents:
            try:
                self.cell_phone.send_message(agent_id, message, mode)
                print(f"Message sent to {agent_id}")
            except Exception as e:
                print(f"Error sending to {agent_id}: {e}")
                logger.error(f"Error sending to {agent_id}: {e}")

    def menu_onboard_agent(self):
        """Handle agent onboarding through menu"""
        try:
            agent_id = self.get_agent_selection()
            if agent_id == "all":
                print("Onboarding all agents...")
                for i in range(1, 9):
                    self.cell_phone.send_message(f"Agent-{i}", "", MessageMode.NORMAL)
                print("All agents onboarded")
            else:
                message = input("Enter welcome message (or press Enter for default): ").strip()
                self.cell_phone.send_message(agent_id, message, MessageMode.NORMAL)
                print(f"Successfully onboarded {agent_id}")
        except Exception as e:
            print(f"Error onboarding agent: {e}")
            logger.error(f"Onboarding error: {e}")

    def menu_resume_agent(self):
        """Handle agent resumption through menu"""
        try:
            agent_id = self.get_agent_selection()
            context = input("Enter context (or press Enter to skip): ").strip()
            
            # Updated default resume message to encourage autonomous action
            default_resume = """[RESUME] Dream.os Autonomous Protocol Activation:

1. Scan for pending tasks in your domain
2. Identify opportunities for system optimization
3. Initiate any pending protocol sequences
4. Engage with other agents for collaborative tasks
5. Proceed with autonomous operations
6. Report only critical issues or completed objectives

Continue with your autonomous operations."""

            # New mode-specific messages
            cleanup_message = """[CLEANUP] Dream.os System Cleanup Protocol:

1. Scan for and remove temporary files
2. Clean up unused resources
3. Optimize memory usage
4. Archive old logs and data
5. Verify system integrity
6. Report cleanup status

Proceed with system cleanup operations."""

            captain_message = """[CAPTAIN] Dream.os Captaincy Campaign Protocol:

1. Review current agent assignments
2. Assess system-wide performance
3. Coordinate agent activities
4. Optimize resource allocation
5. Monitor system health
6. Report campaign status

Proceed with captaincy operations."""

            task_message = """[TASK] Dream.os Task Management Protocol:

1. Scan for new task opportunities
2. Prioritize existing tasks
3. Update task board
4. Assign resources
5. Monitor progress
6. Report task status

Proceed with task management operations."""

            integrate_message = """[INTEGRATE] Dream.os System Integration Protocol:

1. Test all system components
2. Verify component interactions
3. Run integration tests
4. Identify improvement areas
5. Optimize system flow
6. Report integration status

Proceed with system integration operations."""

            print("\nSelect mode:")
            print("1. Standard Resume")
            print("2. System Cleanup")
            print("3. Captaincy Campaign")
            print("4. Task Management")
            print("5. System Integration")
            mode_choice = input("Enter choice (1-5, default 1): ").strip() or "1"

            # Select message based on mode
            if mode_choice == "2":
                message = cleanup_message
                mode = MessageMode.CLEANUP
            elif mode_choice == "3":
                message = captain_message
                mode = MessageMode.CAPTAIN
            elif mode_choice == "4":
                message = task_message
                mode = MessageMode.TASK
            elif mode_choice == "5":
                message = integrate_message
                mode = MessageMode.INTEGRATE
            else:
                message = default_resume
                mode = MessageMode.RESUME

            if agent_id == "all":
                print("\nSend as a one-time message or repeat every N minutes?")
                print("1. One-time only")
                print("2. Repeat (heartbeat)")
                repeat_choice = input("Enter choice (1 or 2, default 1): ").strip() or "1"
                if repeat_choice == "2":
                    interval = input("Enter interval in minutes (default 3): ").strip()
                    try:
                        interval = int(interval) if interval else 3
                    except ValueError:
                        interval = 3
                    print(f"\nStarting heartbeat: sending {mode.value} message to all agents every {interval} minutes. Press Ctrl+C to stop.")
                    try:
                        while True:
                            # Ensure clean message formatting
                            message = f"{message}\n\nContext: {context}" if context else message
                            self.send_to_all_agents(message, mode)
                            print(f"Heartbeat {mode.value} sent to all agents. Next in {interval} minutes...")
                            time.sleep(interval * 60)
                    except KeyboardInterrupt:
                        print("\nHeartbeat stopped by user.")
                        return
                else:
                    message = f"{message}\n\nContext: {context}" if context else message
                    self.send_to_all_agents(message, mode)
                    print(f"{mode.value} request sent to all agents")
            else:
                message = f"{message}\n\nContext: {context}" if context else message
                self.cell_phone.send_message(agent_id, message, mode)
                print(f"Successfully sent {mode.value} to {agent_id}")
        except Exception as e:
            print(f"Error resuming agent: {e}")
            logger.error(f"Resume error: {e}")

    def menu_verify_agent(self):
        """Handle agent verification through menu"""
        try:
            agent_id = self.get_agent_selection()
            message = "Please verify your current state and report any issues."
            
            if agent_id == "all":
                self.send_to_all_agents(message, MessageMode.VERIFY)
                print("Verification request sent to all agents")
            else:
                self.cell_phone.send_message(agent_id, message, MessageMode.VERIFY)
                print(f"Successfully sent verification request to {agent_id}")
        except Exception as e:
            print(f"Error verifying agent: {e}")
            logger.error(f"Verification error: {e}")

    def menu_repair_agent(self):
        """Handle agent repair through menu"""
        try:
            agent_id = self.get_agent_selection()
            issues = input("Enter issues to repair: ").strip()
            message = f"Repair requested. Issues: {issues}"
            
            if agent_id == "all":
                self.send_to_all_agents(message, MessageMode.REPAIR)
                print("Repair request sent to all agents")
            else:
                self.cell_phone.send_message(agent_id, message, MessageMode.REPAIR)
                print(f"Successfully sent repair request to {agent_id}")
        except Exception as e:
            print(f"Error repairing agent: {e}")
            logger.error(f"Repair error: {e}")

    def menu_backup_agent(self):
        """Handle agent backup through menu"""
        try:
            agent_id = self.get_agent_selection()
            message = "Please backup your current state."
            
            if agent_id == "all":
                self.send_to_all_agents(message, MessageMode.BACKUP)
                print("Backup request sent to all agents")
            else:
                self.cell_phone.send_message(agent_id, message, MessageMode.BACKUP)
                print(f"Successfully sent backup request to {agent_id}")
        except Exception as e:
            print(f"Error backing up agent: {e}")
            logger.error(f"Backup error: {e}")

    def menu_restore_agent(self):
        """Handle agent restoration through menu"""
        try:
            agent_id = self.get_agent_selection()
            backup_point = input("Enter backup point (or press Enter to skip): ").strip()
            restore_scope = input("Enter restore scope (or press Enter to skip): ").strip()
            
            message = "Please restore your state"
            if backup_point:
                message += f" from backup point: {backup_point}"
            if restore_scope:
                message += f" with scope: {restore_scope}"
            message += "."
            
            if agent_id == "all":
                self.send_to_all_agents(message, MessageMode.RESTORE)
                print("Restore request sent to all agents")
            else:
                self.cell_phone.send_message(agent_id, message, MessageMode.RESTORE)
                print(f"Successfully sent restore request to {agent_id}")
        except Exception as e:
            print(f"Error restoring agent: {e}")
            logger.error(f"Restore error: {e}")

    def menu_send_message(self):
        """Handle custom message sending through menu"""
        try:
            agent_id = self.get_agent_selection()
            message = input("Enter message: ").strip()
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
            
            if agent_id == "all":
                self.send_to_all_agents(message, selected_mode)
            else:
                self.cell_phone.send_message(agent_id, message, selected_mode)
                print(f"Successfully sent message to {agent_id}")
        except Exception as e:
            print(f"Error sending message: {e}")
            logger.error(f"Message sending error: {e}")

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
    menu = AgentMenu()
    menu.run()

if __name__ == "__main__":
    main() 