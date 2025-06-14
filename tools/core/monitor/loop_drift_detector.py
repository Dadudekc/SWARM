"""
Loop Drift Detector
-----------------
Detects agents stuck in dead loops or idle states.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LoopDriftDetector:
    """Detects agent loop drift and stuck states."""
    
    def __init__(self, config_path: str = "config/loop_drift_config.json"):
        """Initialize detector.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.threshold = self.config.get("drift_threshold_minutes", 5)
        self.auto_resume = self.config.get("auto_resume", False)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    async def check_agent(self, agent_id: str) -> Dict[str, Any]:
        """Check agent for drift.
        
        Args:
            agent_id: Agent ID to check
            
        Returns:
            Drift status dictionary
        """
        try:
            # Check inbox
            inbox_path = Path(f"data/agent_{agent_id}/inbox.json")
            if not inbox_path.exists():
                return {
                    "agent_id": agent_id,
                    "status": "error",
                    "message": "Inbox not found"
                }
            
            # Check devlog
            devlog_path = Path(f"data/agent_{agent_id}/devlog.md")
            if not devlog_path.exists():
                return {
                    "agent_id": agent_id,
                    "status": "error",
                    "message": "Devlog not found"
                }
            
            # Check working task
            task_path = Path(f"data/agent_{agent_id}/working_task.json")
            if not task_path.exists():
                return {
                    "agent_id": agent_id,
                    "status": "error",
                    "message": "Working task not found"
                }
            
            # Get last activity timestamps
            last_inbox = self._get_last_activity(inbox_path)
            last_devlog = self._get_last_activity(devlog_path)
            last_task = self._get_last_activity(task_path)
            
            # Find most recent activity
            last_activity = max(last_inbox, last_devlog, last_task)
            now = datetime.now()
            
            # Check for drift
            if now - last_activity > timedelta(minutes=self.threshold):
                status = {
                    "agent_id": agent_id,
                    "status": "drift",
                    "message": f"No activity for {(now - last_activity).total_seconds() / 60:.1f} minutes",
                    "last_activity": last_activity.isoformat(),
                    "threshold_minutes": self.threshold
                }
                
                # Auto-resume if enabled
                if self.auto_resume:
                    await self._resume_agent(agent_id)
                    status["resumed"] = True
                
                return status
            
            return {
                "agent_id": agent_id,
                "status": "active",
                "message": "Agent is active",
                "last_activity": last_activity.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking agent {agent_id}: {e}")
            return {
                "agent_id": agent_id,
                "status": "error",
                "message": str(e)
            }
    
    def _get_last_activity(self, file_path: Path) -> datetime:
        """Get last activity timestamp from file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Last activity timestamp
        """
        try:
            return datetime.fromtimestamp(file_path.stat().st_mtime)
        except Exception:
            return datetime.min
    
    async def _resume_agent(self, agent_id: str):
        """Resume a drifted agent.
        
        Args:
            agent_id: Agent ID to resume
        """
        try:
            # Create resume prompt
            prompt = {
                "type": "system",
                "content": "Agent appears to be stuck. Attempting to resume operation.",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "source": "loop_drift_detector",
                    "action": "resume"
                }
            }
            
            # Write to inbox
            inbox_path = Path(f"data/agent_{agent_id}/inbox.json")
            with open(inbox_path, 'w') as f:
                json.dump(prompt, f, indent=2)
            
            logger.info(f"Resumed agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error resuming agent {agent_id}: {e}")
    
    async def check_all_agents(self) -> List[Dict[str, Any]]:
        """Check all agents for drift.
        
        Returns:
            List of drift status dictionaries
        """
        # Find all agent directories
        agent_dirs = [d for d in Path("data").glob("agent_*") if d.is_dir()]
        agent_ids = [d.name.split("_")[1] for d in agent_dirs]
        
        # Check each agent
        tasks = [self.check_agent(agent_id) for agent_id in agent_ids]
        return await asyncio.gather(*tasks)

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Detect agent loop drift")
    parser.add_argument("--agents", default="all", help="Agent IDs to check (comma-separated or 'all')")
    parser.add_argument("--resume", action="store_true", help="Auto-resume drifted agents")
    parser.add_argument("--threshold", type=int, default=5, help="Drift threshold in minutes")
    parser.add_argument("--output", help="Output file for results")
    args = parser.parse_args()
    
    try:
        # Initialize detector
        detector = LoopDriftDetector()
        detector.threshold = args.threshold
        detector.auto_resume = args.resume
        
        # Check agents
        if args.agents == "all":
            results = await detector.check_all_agents()
        else:
            agent_ids = args.agents.split(",")
            results = await asyncio.gather(*[
                detector.check_agent(agent_id)
                for agent_id in agent_ids
            ])
        
        # Write results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            print(json.dumps(results, indent=2))
        
        # Exit with status
        if any(r["status"] == "drift" for r in results):
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 