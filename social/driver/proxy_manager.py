# from social.log_writer import logger  # Removed to avoid circular import 

from typing import Optional, Dict, Any, List
import random

class ProxyManager:
    """Manages proxy rotation and selection for social media platforms."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the proxy manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.proxies: List[str] = []
        self.current_proxy: Optional[str] = None
        
    def add_proxy(self, proxy: str) -> None:
        """Add a proxy to the pool.
        
        Args:
            proxy: Proxy string in format 'ip:port' or 'protocol://ip:port'
        """
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            
    def remove_proxy(self, proxy: str) -> None:
        """Remove a proxy from the pool.
        
        Args:
            proxy: Proxy to remove
        """
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            if self.current_proxy == proxy:
                self.current_proxy = None
                
    def get_proxy(self) -> Optional[str]:
        """Get a proxy from the pool.
        
        Returns:
            A proxy string or None if no proxies available
        """
        if not self.proxies:
            return None
        self.current_proxy = random.choice(self.proxies)
        return self.current_proxy
        
    def rotate_proxy(self) -> Optional[str]:
        """Rotate to a new proxy.
        
        Returns:
            The new proxy string or None if no proxies available
        """
        if not self.proxies:
            return None
        available_proxies = [p for p in self.proxies if p != self.current_proxy]
        if not available_proxies:
            return self.current_proxy
        self.current_proxy = random.choice(available_proxies)
        return self.current_proxy 