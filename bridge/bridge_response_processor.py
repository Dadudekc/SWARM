"""
Bridge Response Processor
-----------------------
Processes responses for the bridge response loop.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import jinja2
from jinja2 import Environment, FileSystemLoader

from dreamos.core.autonomy.base.response_loop_daemon import ResponseProcessor
from .monitoring import BridgeMonitor
from .discord_hook import DiscordHook, EventType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeResponseProcessor(ResponseProcessor):
    """Processes responses for the bridge response loop."""
    
    def __init__(self, config: Dict[str, Any], discord_client=None):
        """Initialize the processor.
        
        Args:
            config: Configuration dictionary
            discord_client: Optional Discord client for notifications
        """
        self.config = config
        self.monitor = BridgeMonitor()
        self.discord = DiscordHook()
        
        # Initialize Jinja2 environment for templates
        self.template_env = Environment(
            loader=FileSystemLoader('bridge/prompt_templates'),
            autoescape=True
        )
    
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
    
    def _write_prompt(self, prompt: Dict[str, Any], agent_id: str) -> Tuple[bool, Optional[str]]:
        """Write a new prompt to the bridge outbox."""
        prompt_file = Path(self.config["paths"]["bridge_outbox"]) / f"agent-{agent_id}.json"
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
            
            return True, None
            
        except Exception as e:
            error_msg = f"Error writing prompt for agent {agent_id}: {e}"
            logger.error(error_msg)
            self.discord.send_prompt_status(
                agent_id=agent_id,
                prompt_type=prompt["metadata"]["context"],
                success=False,
                error=str(e)
            )
            return False, error_msg
    
    def _archive_response(self, response_file: Path) -> Tuple[bool, Optional[str]]:
        """Archive a processed response file."""
        try:
            # Create archive directory if it doesn't exist
            archive_dir = Path(self.config["paths"]["archive"]) / response_file.parent.parent.name
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file to archive
            shutil.move(str(response_file), str(archive_dir / response_file.name))
            logger.info(f"Archived response file {response_file}")
            return True, None
            
        except Exception as e:
            error_msg = f"Error archiving response file {response_file}: {e}"
            logger.error(error_msg)
            self.discord.send_event(
                EventType.ERROR_OCCURRED,
                summary=f"Failed to archive response file: {response_file}",
                details={"error": str(e)}
            )
            return False, error_msg
    
    async def process_response(self, response: Dict[str, Any], agent_id: str) -> Tuple[bool, Optional[str]]:
        """Process a response.
        
        Args:
            response: Response data
            agent_id: Agent ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Generate and write new prompt
            prompt = self._generate_prompt(response, agent_id)
            success, error = self._write_prompt(prompt, agent_id)
            
            if not success:
                return False, error
            
            return True, None
            
        except Exception as e:
            return False, str(e) 
