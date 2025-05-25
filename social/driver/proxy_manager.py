import time
import random
import requests
from typing import List, Optional
from dreamos.social.log_writer import logger

class ProxyManager:
    """Manages proxy rotation and validation."""
    
    def __init__(self, proxy_list: Optional[List[str]] = None):
        self.proxy_list = proxy_list or []
        self.current_proxy = None
        self.last_rotation = 0
        self.rotation_interval = 300  # 5 minutes
        
    def add_proxy(self, proxy: str) -> None:
        """Add a proxy to the rotation list."""
        if proxy not in self.proxy_list:
            self.proxy_list.append(proxy)
            logger.info(f"[Proxy] Added new proxy to rotation list")
    
    def validate_proxy(self, proxy: str) -> bool:
        """Validate if a proxy is working."""
        try:
            proxies = {
                "http": f"http://{proxy}",
                "https": f"https://{proxy}"
            }
            response = requests.get("https://api.ipify.org?format=json", 
                                 proxies=proxies, 
                                 timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"[Proxy] Validation failed for {proxy}: {str(e)}")
            return False
    
    def get_next_proxy(self) -> Optional[str]:
        """Get the next valid proxy from the rotation list."""
        if not self.proxy_list:
            return None
            
        current_time = time.time()
        if current_time - self.last_rotation < self.rotation_interval:
            return self.current_proxy
            
        # Try each proxy until we find a working one
        for _ in range(len(self.proxy_list)):
            proxy = random.choice(self.proxy_list)
            if self.validate_proxy(proxy):
                self.current_proxy = proxy
                self.last_rotation = current_time
                logger.info(f"[Proxy] Rotated to new proxy: {proxy}")
                return proxy
                
        logger.warning("[Proxy] No valid proxies found in rotation list")
        return None 