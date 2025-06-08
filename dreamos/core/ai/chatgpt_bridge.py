"""
Simplified ChatGPT Bridge
------------------------
Provides a streamlined interface for ChatGPT interactions.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
from datetime import datetime

class ChatGPTBridge:
    """Simplified ChatGPT integration."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.max_retries = 3
        self.timeout = 30
        self._session = None
    
    async def __aenter__(self):
        """Create aiohttp session."""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session."""
        if self._session:
            await self._session.close()
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send a chat request to ChatGPT.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
            
        Returns:
            Dict containing the response
        """
        if not self._session:
            self._session = aiohttp.ClientSession()
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        for attempt in range(self.max_retries):
            try:
                async with self._session.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        if stream:
                            return response
                        return await response.json()
                    else:
                        error = await response.text()
                        raise Exception(f"API error: {error}")
                        
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text.
        
        Args:
            text: Text to get embedding for
            
        Returns:
            List of floats representing the embedding
        """
        if not self._session:
            self._session = aiohttp.ClientSession()
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "text-embedding-ada-002",
            "input": text
        }
        
        async with self._session.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json=data,
            timeout=self.timeout
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result["data"][0]["embedding"]
            else:
                error = await response.text()
                raise Exception(f"API error: {error}")
    
    def format_message(self, role: str, content: str) -> Dict[str, str]:
        """Format a message for the API.
        
        Args:
            role: Message role (system, user, assistant)
            content: Message content
            
        Returns:
            Formatted message dictionary
        """
        return {
            "role": role,
            "content": content
        }
    
    def format_system_message(self, content: str) -> Dict[str, str]:
        """Format a system message.
        
        Args:
            content: System message content
            
        Returns:
            Formatted system message
        """
        return self.format_message("system", content)
    
    def format_user_message(self, content: str) -> Dict[str, str]:
        """Format a user message.
        
        Args:
            content: User message content
            
        Returns:
            Formatted user message
        """
        return self.format_message("user", content)
    
    def format_assistant_message(self, content: str) -> Dict[str, str]:
        """Format an assistant message.
        
        Args:
            content: Assistant message content
            
        Returns:
            Formatted assistant message
        """
        return self.format_message("assistant", content) 
