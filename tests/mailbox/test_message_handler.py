"""
Unit tests for the new mailbox message handler.
"""

import os
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from agent_tools.mailbox.message_handler import MessageHandler

class TestMessageHandler(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.handler = MessageHandler(base_dir=self.test_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
        
    def test_sequence_initialization(self):
        """Test sequence file initialization."""
        sequence_data = self.handler._get_sequence_data()
        self.assertEqual(sequence_data["current_sequence"], 0)
        self.assertIsNone(sequence_data["last_agent"])
        self.assertEqual(sequence_data["agent_order"], 
                        ["agent1", "agent2", "agent3", "agent6", "agent7", "agent8"])
        
    def test_sequence_advancement(self):
        """Test sequence number advancement."""
        # Send first message
        self.handler.send_message("agent1", "agent2", "test message 1")
        sequence_data = self.handler._get_sequence_data()
        self.assertEqual(sequence_data["current_sequence"], 1)
        self.assertEqual(sequence_data["last_agent"], "agent1")
        
        # Send second message
        self.handler.send_message("agent2", "agent3", "test message 2")
        sequence_data = self.handler._get_sequence_data()
        self.assertEqual(sequence_data["current_sequence"], 2)
        self.assertEqual(sequence_data["last_agent"], "agent2")
        
    def test_agent_routing(self):
        """Test message routing between agents."""
        # Send message from agent1 to agent2
        self.handler.send_message("agent1", "agent2", "test message")
        
        # Check agent2's inbox
        messages = self.handler.get_messages("agent2")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["from_agent"], "agent1")
        self.assertEqual(messages[0]["to_agent"], "agent2")
        self.assertEqual(messages[0]["content"], "test message")
        
    def test_invalid_agent(self):
        """Test sending message to invalid agent."""
        result = self.handler.send_message("agent1", "invalid_agent", "test message")
        self.assertFalse(result)
        
    def test_message_processing(self):
        """Test marking messages as processed."""
        # Send and get message
        self.handler.send_message("agent1", "agent2", "test message")
        messages = self.handler.get_messages("agent2")
        self.assertEqual(len(messages), 1)
        
        # Mark as processed
        self.handler.mark_as_processed(messages[0])
        
        # Check processed directory
        processed_files = os.listdir(self.handler.processed_dir)
        self.assertEqual(len(processed_files), 1)
        
        # Check inbox is empty
        inbox_files = os.listdir(self.handler.inbox_dir)
        self.assertEqual(len(inbox_files), 0)
        
    def test_cleanup_old_messages(self):
        """Test cleanup of old processed messages."""
        # Create old message
        old_time = datetime.utcnow() - timedelta(days=8)
        old_message = {
            "from_agent": "agent1",
            "to_agent": "agent2",
            "content": "old message",
            "timestamp": old_time.isoformat(),
            "sequence": 1
        }
        
        # Save old message
        filename = f"msg_1_agent1_to_agent2.json"
        file_path = os.path.join(self.handler.processed_dir, filename)
        with open(file_path, 'w') as f:
            json.dump(old_message, f)
            
        # Create recent message
        recent_time = datetime.utcnow() - timedelta(days=1)
        recent_message = {
            "from_agent": "agent2",
            "to_agent": "agent3",
            "content": "recent message",
            "timestamp": recent_time.isoformat(),
            "sequence": 2
        }
        
        # Save recent message
        filename = f"msg_2_agent2_to_agent3.json"
        file_path = os.path.join(self.handler.processed_dir, filename)
        with open(file_path, 'w') as f:
            json.dump(recent_message, f)
            
        # Run cleanup
        self.handler.cleanup_old_messages(max_age_days=7)
        
        # Check results
        remaining_files = os.listdir(self.handler.processed_dir)
        self.assertEqual(len(remaining_files), 1)
        self.assertTrue(remaining_files[0].startswith("msg_2_"))
        
    def test_agent_groups(self):
        """Test no cross-talk between agent groups."""
        # Send message within first group (1-3)
        self.handler.send_message("agent1", "agent2", "group1 message")
        messages = self.handler.get_messages("agent2")
        self.assertEqual(len(messages), 1)
        
        # Send message within second group (6-8)
        self.handler.send_message("agent6", "agent7", "group2 message")
        messages = self.handler.get_messages("agent7")
        self.assertEqual(len(messages), 1)
        
        # Verify no cross-group messages
        messages = self.handler.get_messages("agent4")
        self.assertEqual(len(messages), 0)
        messages = self.handler.get_messages("agent5")
        self.assertEqual(len(messages), 0)
        
if __name__ == '__main__':
    unittest.main() 
