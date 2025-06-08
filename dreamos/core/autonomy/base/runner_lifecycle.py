"""Runner lifecycle management mixin."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Protocol
import json

from ..state import State, StateManager

logger = logging.getLogger(__name__)

class RunnerConfig(Protocol):
    """Configuration protocol for runners."""
    check_interval: float
    max_retries: int
    poll_timeout: float
    state_file: str

class RunnerLifecycleMixin(ABC):
    """Mixin for managing runner lifecycle.
    
    This mixin provides core functionality for:
    - Starting/stopping runners
    - Managing state transitions
    - Handling errors and retries
    - Resource cleanup
    """
    
    def __init__(self, config: RunnerConfig):
        """Initialize runner lifecycle.
        
        Args:
            config: Runner configuration
        """
        self.config = config
        self.is_running = False
        self.worker_task: Optional[asyncio.Task] = None
        self.start_time: Optional[datetime] = None
        self.last_update: Optional[datetime] = None
        
        # State management
        self.state_manager = StateManager()
        
        # Metrics
        self.total_processed = 0
        self.total_failed = 0
        self.total_retries = 0
    
    async def start(self) -> None:
        """Start the runner."""
        if self.is_running:
            logger.warning("Runner already running")
            return
        
        logger.info("Starting runner")
        self.is_running = True
        self.start_time = datetime.now()
        self.last_update = self.start_time
        
        # Initialize state
        await self.state_manager.transition_to(State.IDLE)
        
        # Start worker
        self.worker_task = asyncio.create_task(self._run_loop())
    
    async def stop(self) -> None:
        """Stop the runner."""
        if not self.is_running:
            logger.warning("Runner not running")
            return
        
        logger.info("Stopping runner")
        self.is_running = False
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        # Update state
        await self.state_manager.transition_to(State.STOPPED)
        
        # Cleanup
        await self._cleanup()
    
    async def _run_loop(self) -> None:
        """Main runner loop."""
        try:
            while self.is_running:
                try:
                    # Run iteration
                    await self.state_manager.transition_to(State.PROCESSING)
                    result = await self._run_iteration()
                    
                    # Handle result
                    await self._handle_result(result)
                    
                    # Update state
                    await self.state_manager.transition_to(State.IDLE)
                    
                except Exception as e:
                    logger.error(f"Error in runner loop: {e}")
                    await self.state_manager.transition_to(State.ERROR)
                    
                    # Handle error
                    await self._handle_error(e)
                    
                    # Retry if possible
                    if self.total_retries < self.config.max_retries:
                        self.total_retries += 1
                        logger.info(f"Retrying (attempt {self.total_retries})")
                        continue
                    
                    # Stop on max retries
                    logger.error("Max retries exceeded")
                    await self.stop()
                    break
                
                # Wait for next iteration
                await asyncio.sleep(self.config.check_interval)
                
        except asyncio.CancelledError:
            logger.info("Runner loop cancelled")
        except Exception as e:
            logger.error(f"Fatal error in runner loop: {e}")
            await self.stop()
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Save state
            await self._save_state()
            
            # Reset metrics
            self.total_processed = 0
            self.total_failed = 0
            self.total_retries = 0
            
            # Update timestamp
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def _save_state(self) -> None:
        """Save current state to file."""
        state = {
            "is_running": self.is_running,
            "current_state": self.state_manager.current_state.name,
            "total_processed": self.total_processed,
            "total_failed": self.total_failed,
            "total_retries": self.total_retries,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
        
        try:
            with open(self.config.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    @abstractmethod
    async def _run_iteration(self) -> Any:
        """Run a single iteration of the runner.
        
        Returns:
            Result of the iteration
        """
        pass
    
    @abstractmethod
    async def _handle_result(self, result: Any) -> None:
        """Handle the result of a runner iteration.
        
        Args:
            result: Result to handle
        """
        pass
    
    @abstractmethod
    async def _handle_error(self, error: Exception) -> None:
        """Handle an error in the runner.
        
        Args:
            error: Error to handle
        """
        pass 
