import os
import time
import pickle
import json
from typing import Dict, Any, Optional, List
from dreamos.social.log_writer import logger

class SessionState:
    """Manages session state and persistence."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state_file = os.path.join(os.getcwd(), "social", "cookies", f"{session_id}_state.json")
        self.cookies_file = os.path.join(os.getcwd(), "social", "cookies", f"{session_id}_cookies.pkl")
        self.last_activity = time.time()
        self.session_data = {
            "platforms": {},
            "last_successful_login": None,
            "failed_attempts": {},
            "proxy_history": [],
            "performance_metrics": {
                "avg_load_time": 0,
                "success_rate": 0,
                "total_requests": 0
            }
        }
        self._load_state()
    
    def _load_state(self) -> None:
        """Load session state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    self.session_data = json.load(f)
                logger.info(f"[Session] Loaded state for session {self.session_id}")
        except Exception as e:
            logger.error(f"[Session] Error loading state for session {self.session_id}: {str(e)}")
    
    def save_state(self) -> None:
        """Save session state to file."""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
            logger.info(f"[Session] Saved state for session {self.session_id}")
        except Exception as e:
            logger.error(f"[Session] Error saving state for session {self.session_id}: {str(e)}")
    
    def update_platform_state(self, platform: str, status: str, details: Dict[str, Any]) -> None:
        """Update state for a specific platform."""
        self.session_data["platforms"][platform] = {
            "status": status,
            "last_updated": time.time(),
            "details": details
        }
        self.save_state()
    
    def get_platform_state(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get state for a specific platform."""
        return self.session_data["platforms"].get(platform)
    
    def save_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Save cookies to file."""
        try:
            os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info(f"[Session] Saved cookies for session {self.session_id}")
        except Exception as e:
            logger.error(f"[Session] Error saving cookies for session {self.session_id}: {str(e)}")
    
    def load_cookies(self) -> Optional[List[Dict[str, Any]]]:
        """Load cookies from file."""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                logger.info(f"[Session] Loaded cookies for session {self.session_id}")
                return cookies
        except Exception as e:
            logger.error(f"[Session] Error loading cookies for session {self.session_id}: {str(e)}")
        return None 