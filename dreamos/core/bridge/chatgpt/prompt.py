"""
Prompt Manager
------------
Manages prompt generation and template handling for the ChatGPT bridge.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import jinja2
from jinja2 import Environment, FileSystemLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptManager:
    """Manages prompt generation and template handling."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the prompt manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Set up template environment
        template_dir = Path(self.config.get("paths", {}).get(
            "templates",
            "dreamos/core/bridge/chatgpt/templates"
        ))
        self.template_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        
    async def generate_prompt(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a prompt from a message.
        
        Args:
            message: Message to generate prompt from
            metadata: Optional metadata
            
        Returns:
            Prompt dictionary
        """
        try:
            # Get template
            template_type = metadata.get("type", "general") if metadata else "general"
            template = self._get_template(template_type)
            
            # Render template
            prompt_text = template.render(
                message=message,
                metadata=metadata or {},
                timestamp=datetime.now().isoformat()
            )
            
            return {
                "content": prompt_text,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "type": template_type,
                    "source": "prompt_manager",
                    "original_message": message,
                    "original_metadata": metadata or {}
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            raise
            
    def _get_template(self, template_type: str) -> jinja2.Template:
        """Get a template by type.
        
        Args:
            template_type: Type of template to get
            
        Returns:
            Jinja2 template
        """
        try:
            template_name = f"{template_type}.j2"
            return self.template_env.get_template(template_name)
        except Exception as e:
            logger.warning(f"No template found for {template_type}, using default: {e}")
            return self.template_env.get_template("general.j2")
            
    def add_template(self, template_type: str, template_content: str) -> None:
        """Add a new template.
        
        Args:
            template_type: Type of template
            template_content: Template content
        """
        template_path = Path(self.template_env.loader.searchpath[0]) / f"{template_type}.j2"
        with open(template_path, 'w') as f:
            f.write(template_content)
            
    def remove_template(self, template_type: str) -> None:
        """Remove a template.
        
        Args:
            template_type: Type of template to remove
        """
        template_path = Path(self.template_env.loader.searchpath[0]) / f"{template_type}.j2"
        if template_path.exists():
            template_path.unlink()
            
    def list_templates(self) -> List[str]:
        """List all available templates.
        
        Returns:
            List of template types
        """
        template_dir = Path(self.template_env.loader.searchpath[0])
        return [f.stem for f in template_dir.glob("*.j2")] 