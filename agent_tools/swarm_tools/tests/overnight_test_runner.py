"""
Overnight Test Runner
--------------------
Automatically runs tests and coordinates agent debugging efforts.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dreamos.core.messaging.cell_phone import CellPhone
from dreamos.core.messaging.message_handler import MessageHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("overnight_test_runner")

# Constants
ROOT = Path(__file__).resolve().parent.parent
AGENT_IDS = [f"agent-{i}" for i in range(1, 9)]
PROMPT_PATH = ROOT / "runtime" / "test_prompts" / "TEST_AND_DEBUG_AUTONOMY.yaml"
TEST_ANALYSIS_PATH = ROOT / "runtime" / "test_error_analysis.json"
HIGH_SCORE_PATH = ROOT / "runtime" / "high_score_tracker.json"

def run():
    """Run the test loop."""
    logger.info("Starting overnight test runner...")
    
    # Initialize test runner
    runner = TestRunner()
    
    while True:
        try:
            # Send prompts to all agents
            for agent_id in AGENT_IDS:
                runner.send_prompt_to_agent(agent_id)
            
            # Save state
            runner._save_test_analysis()
            runner._save_high_scores()
            
            # Wait for next cycle
            time.sleep(180)  # 3 minutes
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in test loop: {e}")
            time.sleep(60)  # Wait a minute before retrying

class TestRunner:
    """Coordinates test running and agent debugging."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.message_handler = MessageHandler(base_dir=str(ROOT / "agent_tools" / "mailbox"))
        self.cell_phones = {}
        
        # Initialize cell phones for each agent
        for agent_id in AGENT_IDS:
            self.cell_phones[agent_id] = CellPhone(config={
                "agent_id": agent_id,
                "message_handler": self.message_handler,
                "log_level": "INFO"
            })
            
        # Load or initialize test analysis
        self.test_analysis = self._load_test_analysis()
        self.high_scores = self._load_high_scores()
        
        logger.info("Test runner initialized")
    
    def _load_test_analysis(self) -> Dict:
        """Load test error analysis."""
        if TEST_ANALYSIS_PATH.exists():
            with open(TEST_ANALYSIS_PATH) as f:
                return json.load(f)
        return {
            "errors": [],
            "fixes": [],
            "blockers": [],
            "last_update": datetime.utcnow().isoformat()
        }
    
    def _load_high_scores(self) -> Dict:
        """Load high score tracker."""
        if HIGH_SCORE_PATH.exists():
            with open(HIGH_SCORE_PATH) as f:
                return json.load(f)
        return {
            "agents": {},
            "last_update": datetime.utcnow().isoformat()
        }
    
    def _save_test_analysis(self):
        """Save test error analysis."""
        self.test_analysis["last_update"] = datetime.utcnow().isoformat()
        with open(TEST_ANALYSIS_PATH, "w") as f:
            json.dump(self.test_analysis, f, indent=2)
    
    def _save_high_scores(self):
        """Save high score tracker."""
        self.high_scores["last_update"] = datetime.utcnow().isoformat()
        with open(HIGH_SCORE_PATH, "w") as f:
            json.dump(self.high_scores, f, indent=2)
    
    def send_prompt_to_agent(self, agent_id: str):
        """Send test and debug prompt to agent."""
        try:
            # Load prompt
            with open(PROMPT_PATH) as f:
                prompt = yaml.safe_load(f)
            
            # Send to agent
            success = self.cell_phones[agent_id].send_message(
                to_agent=agent_id,
                content=json.dumps(prompt)
            )
            
            if success:
                logger.info(f"Sent prompt to {agent_id}")
            else:
                logger.error(f"Failed to send prompt to {agent_id}")
                
        except Exception as e:
            logger.error(f"Error sending prompt to {agent_id}: {e}")

if __name__ == "__main__":
    run() 
