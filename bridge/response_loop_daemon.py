"""
Response Loop Daemon
------------------
Monitors agent responses and generates new prompts for the ChatGPT bridge.
"""

import json
import time
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import shutil
import jinja2
from jinja2 import Environment, FileSystemLoader

from .monitoring import BridgeMonitor
from .discord_hook import DiscordHook, EventType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/response_loop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ResponseLoopDaemon:
    """Monitors agent responses and generates new prompts for the ChatGPT bridge."""
    
    def __init__(self, config_path: str = "config/bridge_config.json"):
        """Initialize the response loop daemon."""
        self.config = self._load_config(config_path)
        self.agent_mailbox = Path(self.config["paths"]["agent_mailbox"])
        self.bridge_outbox = Path(self.config["paths"]["bridge_outbox"])
        self.archive_path = Path(self.config["paths"]["archive"])
        self.failed_path = Path(self.config["paths"]["failed"])
        self.processed_responses = set()
        
        # Initialize monitoring and Discord
        self.monitor = BridgeMonitor()
        self.discord = DiscordHook()
        
        # Initialize Jinja2 environment for templates
        self.template_env = Environment(
            loader=FileSystemLoader('bridge/prompt_templates'),
            autoescape=True
        )
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load bridge configuration."""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return {
                "paths": {
                    "agent_mailbox": "agent_tools/mailbox",
                    "bridge_outbox": "bridge_outbox",
                    "archive": "bridge_outbox/archive",
                    "failed": "runtime/bridge_failed"
                },
                "poll_interval": 30,
                "max_retries": 3,
                "retry_delay": 60,
                "health_check_interval": 600  # 10 minutes
            }
            
    def _get_agent_responses(self) -> List[Path]:
        """Get all agent response files."""
        responses = []
        for agent_dir in self.agent_mailbox.glob("agent-*"):
            response_file = agent_dir / "workspace" / "bridge_response.json"
            if response_file.exists():
                responses.append(response_file)
        return responses
        
    def _parse_response(self, response_file: Path) -> Optional[Dict[str, Any]]:
        """Parse an agent response file."""
        try:
            with open(response_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error parsing response file {response_file}: {e}")
            self.discord.send_event(
                EventType.ERROR_OCCURRED,
                summary=f"Failed to parse response file: {response_file}",
                details={"error": str(e)}
            )
            return None
            
    def _get_template(self, response_type: str) -> Optional[jinja2.Template]:
        """Get the appropriate template for the response type."""
        try:
            template_name = f"{response_type}.j2"
            return self.template_env.get_template(template_name)
        except Exception as e:
            logger.warning(f"No template found for {response_type}, using default: {e}")
            return None
            
    def _generate_prompt(self, response: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Generate a new prompt based on the agent's response."""
        response_type = response.get("type", "general")
        template = self._get_template(response_type)
        
        if template:
            # Render template with response data
            prompt_text = template.render(
                response=response,
                agent_id=agent_id,
                timestamp=datetime.now().isoformat()
            )
        else:
            # Fallback to default prompt generation
            if response_type == "patch_submission":
                prompt_text = f"Please review the following patch for {response.get('file_path', 'unknown file')}:\n\n{response.get('code_patch', '')}\n\nIs this patch correct and complete? If not, what improvements are needed?"
            elif response_type == "test_result":
                prompt_text = f"Test results for {response.get('test_name', 'unknown test')}:\n\n{response.get('result', '')}\n\nWhat should be the next step?"
            else:
                prompt_text = f"Please analyze the following response from agent {agent_id}:\n\n{json.dumps(response, indent=2)}\n\nWhat should be the next step?"
                
        return {
            "prompt": prompt_text,
            "timestamp": datetime.now().isoformat(),
            "priority": response.get("priority", 1),
            "metadata": {
                "source": "response_loop",
                "context": response_type,
                "original_response": response
            }
        }
        
    def _write_prompt(self, prompt: Dict[str, Any], agent_id: str):
        """Write a new prompt to the bridge outbox."""
        prompt_file = self.bridge_outbox / f"agent-{agent_id}.json"
        try:
            with open(prompt_file, 'w') as f:
                json.dump(prompt, f, indent=2)
            logger.info(f"Wrote new prompt for agent {agent_id}")
            
            # Update metrics and send Discord notification
            self.monitor.update_metrics(
                agent_id=agent_id,
                prompt_type=prompt["metadata"]["context"]
            )
            self.discord.send_prompt_status(
                agent_id=agent_id,
                prompt_type=prompt["metadata"]["context"],
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error writing prompt for agent {agent_id}: {e}")
            self.discord.send_prompt_status(
                agent_id=agent_id,
                prompt_type=prompt["metadata"]["context"],
                success=False,
                error=str(e)
            )
            
    def _archive_response(self, response_file: Path):
        """Archive a processed response file."""
        try:
            # Create archive directory if it doesn't exist
            archive_dir = self.archive_path / response_file.parent.parent.name
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file to archive
            shutil.move(str(response_file), str(archive_dir / response_file.name))
            logger.info(f"Archived response file {response_file}")
        except Exception as e:
            logger.error(f"Error archiving response file {response_file}: {e}")
            self.discord.send_event(
                EventType.ERROR_OCCURRED,
                summary=f"Failed to archive response file: {response_file}",
                details={"error": str(e)}
            )
            
    def _handle_failed_prompt(self, prompt_file: Path, retry_count: int):
        """Handle a failed prompt by moving it to the failed directory or retrying."""
        if retry_count >= self.config["max_retries"]:
            # Move to failed directory
            failed_dir = self.failed_path / prompt_file.parent.name
            failed_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(prompt_file), str(failed_dir / prompt_file.name))
            logger.error(f"Prompt failed after {retry_count} retries, moved to {failed_dir}")
            
            # Send Discord notification
            self.discord.send_event(
                EventType.PROMPT_FAILED,
                summary=f"Prompt failed after {retry_count} retries",
                details={"retry_count": retry_count}
            )
        else:
            # Wait before retry
            time.sleep(self.config["retry_delay"])
            logger.info(f"Retrying prompt (attempt {retry_count + 1}/{self.config['max_retries']})")
            
    def _process_responses(self):
        """Process all agent responses and generate new prompts."""
        start_time = time.time()
        
        for response_file in self._get_agent_responses():
            # Skip if already processed
            if response_file in self.processed_responses:
                continue
                
            # Parse response
            response = self._parse_response(response_file)
            if not response:
                continue
                
            # Extract agent ID
            agent_id = response_file.parent.parent.name.split('-')[1]
            
            # Generate and write new prompt
            prompt = self._generate_prompt(response, agent_id)
            self._write_prompt(prompt, agent_id)
            
            # Archive response
            self._archive_response(response_file)
            
            # Mark as processed
            self.processed_responses.add(response_file)
            
        # Update processing time
        processing_time = time.time() - start_time
        self.monitor.update_metrics(processing_time=processing_time)
        
    def _check_health(self):
        """Check bridge health and send status update."""
        is_healthy = self.monitor.check_health()
        status = self.monitor.get_status_summary()
        
        # Send health update to Discord
        self.discord.send_health_update(status)
        
        if not is_healthy:
            self.discord.send_event(
                EventType.ERROR_OCCURRED,
                summary="Bridge health check failed",
                details=status
            )
            
    def run(self):
        """Run the response loop daemon continuously."""
        logger.info("Starting Response Loop Daemon")
        self.discord.send_event(EventType.LOOP_START, summary="Bridge loop started")
        
        last_health_check = time.time()
        
        try:
            while True:
                self._process_responses()
                
                # Check health periodically
                current_time = time.time()
                if current_time - last_health_check >= self.config["health_check_interval"]:
                    self._check_health()
                    last_health_check = current_time
                    
                time.sleep(self.config["poll_interval"])
                
        except KeyboardInterrupt:
            logger.info("Response loop daemon stopped by user")
            self.discord.send_event(EventType.LOOP_END, summary="Bridge loop stopped by user")
        except Exception as e:
            logger.error(f"Response loop daemon error: {e}")
            self.discord.send_event(
                EventType.ERROR_OCCURRED,
                summary="Bridge loop crashed",
                details={"error": str(e)}
            )
            
if __name__ == "__main__":
    daemon = ResponseLoopDaemon()
    daemon.run() 