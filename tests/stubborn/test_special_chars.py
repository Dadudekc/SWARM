"""
Test script for special character and multiline text handling in UI automation.
"""

import logging
import time
import os
from pathlib import Path
from dreamos.core.agent_control.ui_automation import UIAutomation

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_multiline_text():
    """Test sending messages with multiple lines."""
    logger.info("Starting multiline text test")
    
    # Get the config file path
    config_path = os.path.join(os.path.dirname(__file__), "tests", "test_config", "agent_coordinates.json")
    
    # Initialize UI automation with config
    ui = UIAutomation(config_path=config_path)
    
    try:
        # Test message with multiple lines
        test_message = """Line 1: Hello World!
Line 2: Testing multiline
Line 3: With special chars: !@#$%^&*()
Line 4: End of test"""
        
        logger.info(f"Sending multiline test message:\n{test_message}")
        
        # Send message to Agent-1
        success, response = ui.send_message("Agent-1", test_message)
        
        if success:
            logger.info("Message sent successfully")
            logger.info(f"Response: {response}")
        else:
            logger.error("Failed to send message")
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
    finally:
        ui.cleanup()

if __name__ == "__main__":
    test_multiline_text() 
