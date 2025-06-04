"""
UI Module

Handles message display and interaction for the Dream.OS messaging system.
"""

import logging
import time
from typing import Optional, Dict, Any
import pyautogui

from .common import Message, MessageMode
from .processor import MessageProcessor

logger = logging.getLogger('messaging.ui')

class MessageUI:
    """Handles message display and interaction."""
    
    def __init__(self, processor: Optional[MessageProcessor] = None):
        """Initialize the message UI.
        
        Args:
            processor: Optional message processor instance
        """
        self.processor = processor or MessageProcessor()
        self._cursor_controller = None
        self._coordinate_manager = None
        
        # UI parameters
        self.message_delay = 0.1
        self.verification_delay = 0.2
        
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
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling resume message: {e}")
            return False
            
    def _handle_sync(self, message: Message) -> bool:
        """Handle sync message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Move cursor to sync position
            self._cursor_controller.move_to_sync()
            time.sleep(self.message_delay)
            
            # Click to sync
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling sync message: {e}")
            return False
            
    def _handle_verify(self, message: Message) -> bool:
        """Handle verify message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Move cursor to verify position
            self._cursor_controller.move_to_verify()
            time.sleep(self.message_delay)
            
            # Click to verify
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling verify message: {e}")
            return False
            
    def _handle_repair(self, message: Message) -> bool:
        """Handle repair message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Move cursor to repair position
            self._cursor_controller.move_to_repair()
            time.sleep(self.message_delay)
            
            # Click to repair
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling repair message: {e}")
            return False
            
    def _handle_backup(self, message: Message) -> bool:
        """Handle backup message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Move cursor to backup position
            self._cursor_controller.move_to_backup()
            time.sleep(self.message_delay)
            
            # Click to backup
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling backup message: {e}")
            return False
            
    def _handle_restore(self, message: Message) -> bool:
        """Handle restore message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Move cursor to restore position
            self._cursor_controller.move_to_restore()
            time.sleep(self.message_delay)
            
            # Click to restore
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling restore message: {e}")
            return False
            
    def _handle_cleanup(self, message: Message) -> bool:
        """Handle cleanup message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Move cursor to cleanup position
            self._cursor_controller.move_to_cleanup()
            time.sleep(self.message_delay)
            
            # Click to cleanup
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling cleanup message: {e}")
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
                
            # Move cursor to task position
            self._cursor_controller.move_to_task()
            time.sleep(self.message_delay)
            
            # Click to task
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling task message: {e}")
            return False
            
    def _handle_integrate(self, message: Message) -> bool:
        """Handle integrate message."""
        try:
            if not self._cursor_controller:
                return False
                
            # Move cursor to integrate position
            self._cursor_controller.move_to_integrate()
            time.sleep(self.message_delay)
            
            # Click to integrate
            self._cursor_controller.click()
            time.sleep(self.verification_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling integrate message: {e}")
            return False 