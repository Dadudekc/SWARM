from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime

from social.utils.social_common import SocialMediaUtils
from social.utils.log_manager import LogManager, LogLevel

class PlatformStrategy(ABC):
    """Base class for all social media platform strategies."""
    
    def __init__(self, driver, config: Dict[str, Any], memory_update: Dict[str, Any]):
        self.driver = driver
        self.config = config
        self.memory_update = memory_update
        self.platform = self.__class__.__name__.replace('Strategy', '').lower()
        self.utils = SocialMediaUtils(driver, config, self.platform)
        self.logger = LogManager()
        
        # Initialize memory tracking
        self.memory_updates = {
            "login_attempts": 0,
            "post_attempts": 0,
            "media_uploads": 0,
            "errors": [],
            "last_action": None,
            "last_error": None
        }

    def _update_memory(self, action: str, success: bool, error: Optional[Exception] = None) -> None:
        """Update memory with action results."""
        self.memory_updates["last_action"] = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "success": success
        }
        if error:
            self.memory_updates["errors"].append({
                "action": action,
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            })
            self.memory_updates["last_error"] = {
                "action": action,
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            }

    def _log_action(self, action: str, status: str, tags: List[str], error: Optional[str] = None) -> None:
        """Log an action with consistent format."""
        self.logger.write_log(
            platform=self.platform,
            status=status,
            tags=tags,
            error=error,
            level=LogLevel.ERROR if error else LogLevel.INFO
        )

    def _handle_media_upload(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Handle media upload with memory tracking."""
        try:
            self.memory_updates["media_uploads"] += 1
            success = self.utils.upload_media(media_paths, is_video)
            self._update_memory("media_upload", success)
            return success
        except Exception as e:
            self._update_memory("media_upload", False, e)
            self._log_action("media_upload", "error", ["media_upload"], str(e))
            return False

    def _validate_media(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Validate media files with memory tracking."""
        try:
            success = self.utils.validate_media(media_paths, is_video)
            self._update_memory("media_validation", success)
            return success
        except Exception as e:
            self._update_memory("media_validation", False, e)
            self._log_action("media_validation", "error", ["media_validation"], str(e))
            return False

    def get_memory_updates(self) -> Dict[str, Any]:
        """Get current memory state."""
        return self.memory_updates

    @abstractmethod
    def is_logged_in(self) -> bool:
        """Check if currently logged into the platform."""
        pass

    @abstractmethod
    def login(self) -> bool:
        """Attempt to log in to the platform."""
        pass

    @abstractmethod
    def post(self, content: str, media_paths: Optional[List[str]] = None, is_video: bool = False) -> bool:
        """Post content to the platform with optional media."""
        pass

    def create_post(self) -> str:
        """Generate platform-specific post content from memory update."""
        quests = self.memory_update.get("quest_completions", [])
        protocols = self.memory_update.get("newly_unlocked_protocols", [])
        loops = self.memory_update.get("feedback_loops_triggered", [])

        if self.platform == "linkedin":
            return f"🔗 Quest Complete: {quests[0]}\nNew Protocol: {protocols[0]}\nLoops Activated: {', '.join(loops)}"
        elif self.platform == "twitter":
            return f"🚀 Quest Complete: {quests[0]} - Protocols Deployed: {protocols[0]}"
        else:
            return f"📣 New Updates: {quests[0]} & Protocol {protocols[0]}" 