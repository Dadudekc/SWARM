"""
Response file and ChatGPT communication handlers.
"""

import json
import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, Any
from dreamos.core.autonomy.utils.response_utils import extract_agent_id_from_file

logger = logging.getLogger(__name__)

async def process_response_file(daemon, file_path: Path):
    """Process a response file using the daemon's dependencies."""
    try:
        # Load response
        with open(file_path, 'r') as f:
            response = json.load(f)
        # Extract agent ID
        agent_id = extract_agent_id_from_file(file_path)
        if not agent_id:
            logger.error(f"Could not extract agent ID from {file_path}")
            return
        # Generate prompt
        prompt = daemon.prompt_processor.generate_prompt(response, agent_id)
        # Send to ChatGPT
        success = await send_to_chatgpt(daemon, prompt, agent_id)
        if not success:
            logger.error(f"Failed to send prompt to ChatGPT for agent {agent_id}")
            return
        # Move to archive
        archive_path = daemon.archive_dir / file_path.name
        file_path.rename(archive_path)
        # Update metrics
        daemon.monitor.update_metrics(
            agent_id=agent_id,
            prompt_type=prompt["metadata"]["context"]
        )
        # Send Discord notification
        daemon.discord.send_prompt_status(
            agent_id=agent_id,
            prompt_type=prompt["metadata"]["context"],
            success=True
        )
    except Exception as e:
        logger.error(f"Error processing response file {file_path}: {e}")
        # Move to failed directory
        failed_path = daemon.failed_dir / file_path.name
        file_path.rename(failed_path)
        # Send Discord notification
        daemon.discord.send_prompt_status(
            agent_id=agent_id if 'agent_id' in locals() else None,
            prompt_type="error",
            success=False,
            error=str(e)
        )

async def send_to_chatgpt(daemon, prompt: Dict[str, Any], agent_id: str) -> bool:
    """Send a prompt to ChatGPT using the daemon's config and validator."""
    try:
        # Write prompt to bridge outbox
        outbox_path = Path(daemon.config["paths"]["bridge_outbox"]) / f"agent-{agent_id}.json"
        with open(outbox_path, 'w') as f:
            json.dump(prompt, f, indent=2)
        # Wait for response
        validated_path = daemon.validated_dir / f"agent-{agent_id}.json"
        start_time = time.time()
        while time.time() - start_time < daemon.config["chatgpt"]["response_wait"]:
            if validated_path.exists():
                # Read and validate response
                with open(validated_path) as f:
                    response = json.load(f)
                if daemon.validator.validate_response(response):
                    return True
            await asyncio.sleep(1)
        logger.error(f"Timeout waiting for ChatGPT response for agent {agent_id}")
        return False
    except Exception as e:
        logger.error(f"Error sending prompt to ChatGPT: {e}")
        return False 