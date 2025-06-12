"""
UI Module for Message Processing
-----------------------------
Handles UI-related message processing functionality.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import logging
import time
import pyautogui
from pathlib import Path

from .common import Message, MessageMode
from .message_processor import MessageProcessor
from .message_builder import message_builder, MessageType

logger = logging.getLogger(__name__)

@dataclass
class MessageUI:
    """UI handler for message processing."""
    
    processor: Optional[MessageProcessor] = None
    runtime_dir: str = str(Path(__file__).parent.parent.parent / "runtime")
    
    def __post_init__(self):
        """Initialize with default processor if none provided."""
        if self.processor is None:
            self.processor = MessageProcessor(runtime_dir=self.runtime_dir)
            
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message through the UI layer."""
        try:
            return self.processor.process(message)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {"error": str(e)}

    def initialize(self, cursor_controller, coordinate_manager):
        """Initialize UI components.
        
        Args:
            cursor_controller: Cursor controller instance
            coordinate_manager: Coordinate manager instance
        """
        self._cursor_controller = cursor_controller
        self._coordinate_manager = coordinate_manager
        
        # Register handlers
        self.processor.register_handler(MessageMode.RESUME, self._handle_resume)
        self.processor.register_handler(MessageMode.SYNC, self._handle_sync)
        self.processor.register_handler(MessageMode.VERIFY, self._handle_verify)
        self.processor.register_handler(MessageMode.REPAIR, self._handle_repair)
        self.processor.register_handler(MessageMode.BACKUP, self._handle_backup)
        self.processor.register_handler(MessageMode.RESTORE, self._handle_restore)
        self.processor.register_handler(MessageMode.CLEANUP, self._handle_cleanup)
        self.processor.register_handler(MessageMode.CAPTAIN, self._handle_captain)
        self.processor.register_handler(MessageMode.TASK, self._handle_task)
        self.processor.register_handler(MessageMode.INTEGRATE, self._handle_integrate)
        
        # Start processor
        self.processor.start()
        logger.info("Message UI initialized")
        
    def shutdown(self):
        """Clean up resources."""
        try:
            self.processor.stop()
            logger.info("Message UI shut down")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
    def send_message(self, message: Message) -> bool:
        """Send a message through the UI.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if message was successfully sent
        """
        try:
            return self.processor.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
            
    def get_status(self) -> Dict[str, Any]:
        """Get current UI status.
        
        Returns:
            Dict containing UI statistics
        """
        try:
            return {
                'processor_status': self.processor.get_status(),
                'cursor_position': pyautogui.position() if self._cursor_controller else None
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {'error': str(e)}
            
    def _handle_resume(self, message: Message) -> bool:
        """Handle resume message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Move cursor to message position
            self._cursor_controller.move_to_message(message)
            time.sleep(self.message_delay)
            
            # Click to resume
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            # Send success message
            success_msg = message_builder.create_message(
                MessageType.SUCCESS,
                "task_complete",
                {"task_name": "Resume"}
            )
            self.send_message(success_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling resume message: {e}")
            # Send error message
            error_msg = message_builder.create_message(
                MessageType.ERROR,
                "task_failed",
                {"error": str(e)}
            )
            self.send_message(error_msg)
            return False
            
    def _handle_sync(self, message: Message) -> bool:
        """Handle sync message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Send start message
            start_msg = message_builder.create_message(
                MessageType.INFO,
                "sync_started"
            )
            self.send_message(start_msg)
            
            # Move cursor to sync position
            self._cursor_controller.move_to_sync()
            time.sleep(self.message_delay)
            
            # Click to sync
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            # Send success message
            success_msg = message_builder.create_message(
                MessageType.SUCCESS,
                "sync_complete"
            )
            self.send_message(success_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling sync message: {e}")
            # Send error message
            error_msg = message_builder.create_message(
                MessageType.ERROR,
                "sync_failed",
                {"error": str(e)}
            )
            self.send_message(error_msg)
            return False
            
    def _handle_verify(self, message: Message) -> bool:
        """Handle verify message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Send start message
            start_msg = message_builder.create_message(
                MessageType.INFO,
                "verify_started"
            )
            self.send_message(start_msg)
            
            # Move cursor to verify position
            self._cursor_controller.move_to_verify()
            time.sleep(self.message_delay)
            
            # Click to verify
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            # Send success message
            success_msg = message_builder.create_message(
                MessageType.SUCCESS,
                "verify_complete"
            )
            self.send_message(success_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling verify message: {e}")
            # Send error message
            error_msg = message_builder.create_message(
                MessageType.ERROR,
                "verify_failed",
                {"error": str(e)}
            )
            self.send_message(error_msg)
            return False
            
    def _handle_repair(self, message: Message) -> bool:
        """Handle repair message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Send start message
            start_msg = message_builder.create_message(
                MessageType.INFO,
                "repair_started"
            )
            self.send_message(start_msg)
            
            # Move cursor to repair position
            self._cursor_controller.move_to_repair()
            time.sleep(self.message_delay)
            
            # Click to repair
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            # Send success message
            success_msg = message_builder.create_message(
                MessageType.SUCCESS,
                "repair_complete"
            )
            self.send_message(success_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling repair message: {e}")
            # Send error message
            error_msg = message_builder.create_message(
                MessageType.ERROR,
                "repair_failed",
                {"error": str(e)}
            )
            self.send_message(error_msg)
            return False
            
    def _handle_backup(self, message: Message) -> bool:
        """Handle backup message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Send start message
            start_msg = message_builder.create_message(
                MessageType.INFO,
                "backup_started",
                {"backup_path": str(self.runtime_dir / "backups")}
            )
            self.send_message(start_msg)
            
            # Move cursor to backup position
            self._cursor_controller.move_to_backup()
            time.sleep(self.message_delay)
            
            # Click to backup
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            # Send success message
            success_msg = message_builder.create_message(
                MessageType.SUCCESS,
                "backup_complete",
                {"backup_path": str(self.runtime_dir / "backups")}
            )
            self.send_message(success_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling backup message: {e}")
            # Send error message
            error_msg = message_builder.create_message(
                MessageType.ERROR,
                "backup_failed",
                {"error": str(e)}
            )
            self.send_message(error_msg)
            return False
            
    def _handle_restore(self, message: Message) -> bool:
        """Handle restore message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Send start message
            start_msg = message_builder.create_message(
                MessageType.INFO,
                "restore_started",
                {"restore_path": str(self.runtime_dir / "backups")}
            )
            self.send_message(start_msg)
            
            # Move cursor to restore position
            self._cursor_controller.move_to_restore()
            time.sleep(self.message_delay)
            
            # Click to restore
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            # Send success message
            success_msg = message_builder.create_message(
                MessageType.SUCCESS,
                "restore_complete",
                {"restore_path": str(self.runtime_dir / "backups")}
            )
            self.send_message(success_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling restore message: {e}")
            # Send error message
            error_msg = message_builder.create_message(
                MessageType.ERROR,
                "restore_failed",
                {"error": str(e)}
            )
            self.send_message(error_msg)
            return False
            
    def _handle_cleanup(self, message: Message) -> bool:
        """Handle cleanup message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Send start message
            start_msg = message_builder.create_message(
                MessageType.INFO,
                "cleanup_started"
            )
            self.send_message(start_msg)
            
            # Move cursor to cleanup position
            self._cursor_controller.move_to_cleanup()
            time.sleep(self.message_delay)
            
            # Click to cleanup
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            # Send success message
            success_msg = message_builder.create_message(
                MessageType.SUCCESS,
                "cleanup_complete"
            )
            self.send_message(success_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling cleanup message: {e}")
            # Send error message
            error_msg = message_builder.create_message(
                MessageType.ERROR,
                "cleanup_failed",
                {"error": str(e)}
            )
            self.send_message(error_msg)
            return False
            
    def _handle_captain(self, message: Message) -> bool:
        """Handle captain message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Move cursor to captain position
            self._cursor_controller.move_to_captain()
            time.sleep(self.message_delay)
            
            # Click to captain
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling captain message: {e}")
            return False
            
    def _handle_task(self, message: Message) -> bool:
        """Handle task message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Send start message
            start_msg = message_builder.create_message(
                MessageType.INFO,
                "task_started",
                {"task_name": message.data.get("task_name", "Unknown task")}
            )
            self.send_message(start_msg)
            
            # Move cursor to task position
            self._cursor_controller.move_to_task()
            time.sleep(self.message_delay)
            
            # Click to task
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            # Send success message
            success_msg = message_builder.create_message(
                MessageType.SUCCESS,
                "task_complete",
                {"task_name": message.data.get("task_name", "Unknown task")}
            )
            self.send_message(success_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling task message: {e}")
            # Send error message
            error_msg = message_builder.create_message(
                MessageType.ERROR,
                "task_failed",
                {"error": str(e)}
            )
            self.send_message(error_msg)
            return False
            
    def _handle_integrate(self, message: Message) -> bool:
        """Handle integrate message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Send start message
            start_msg = message_builder.create_message(
                MessageType.INFO,
                "integrate_started",
                {"component": message.data.get("component", "Unknown component")}
            )
            self.send_message(start_msg)
            
            # Move cursor to integrate position
            self._cursor_controller.move_to_integrate()
            time.sleep(self.message_delay)
            
            # Click to integrate
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            # Send success message
            success_msg = message_builder.create_message(
                MessageType.SUCCESS,
                "integrate_complete",
                {"component": message.data.get("component", "Unknown component")}
            )
            self.send_message(success_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling integrate message: {e}")
            # Send error message
            error_msg = message_builder.create_message(
                MessageType.ERROR,
                "integrate_failed",
                {"error": str(e)}
            )
            self.send_message(error_msg)
            return False

    async def _send_success_message(self, template: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Send a success message.
        
        Args:
            template: Template name to use
            data: Optional data for the template
        """
        message = message_builder.create_message(
            MessageType.SUCCESS,
            template,
            data
        )
        await self.processor.process_message(message)
        
    async def _send_error_message(self, template: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Send an error message.
        
        Args:
            template: Template name to use
            data: Optional data for the template
        """
        message = message_builder.create_message(
            MessageType.ERROR,
            template,
            data
        )
        await self.processor.process_message(message)
        
    async def _send_info_message(self, template: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Send an info message.
        
        Args:
            template: Template name to use
            data: Optional data for the template
        """
        message = message_builder.create_message(
            MessageType.INFO,
            template,
            data
        )
        await self.processor.process_message(message)
        
    async def _send_progress_message(self, template: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Send a progress message.
        
        Args:
            template: Template name to use
            data: Optional data for the template
        """
        message = message_builder.create_message(
            MessageType.PROGRESS,
            template,
            data
        )
        await self.processor.process_message(message) 
