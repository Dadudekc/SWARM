"""
UI Automation Module

Handles UI automation tasks using PyAutoGUI.
"""

import logging
import time
import json
import signal
from typing import Dict, Tuple, Optional, List
from pathlib import Path
import pyautogui
import pygetwindow as gw
from PIL import Image
import keyboard
import threading
from contextlib import contextmanager
import pytesseract
import screeninfo

# Try to import screeninfo, but provide fallback if not available
try:
    from screeninfo import get_monitors
    SCREENINFO_AVAILABLE = True
except ImportError:
    SCREENINFO_AVAILABLE = False
    logger = logging.getLogger('agent_control.ui_automation')
    logger.warning("screeninfo not available - using fallback coordinate transformation")

from ..cursor_controller import CursorController
from .response_capture import ResponseCapture
from .screenshot_logger import ScreenshotLogger
from .timing import (
    WINDOW_ACTIVATION_DELAY,
    FOCUS_ESTABLISH_DELAY,
    TEXT_CLEAR_DELAY,
    TEXT_DELETE_DELAY,
    TYPING_INTERVAL,
    TYPING_COMPLETE_DELAY,
    MESSAGE_SEND_DELAY,
    COPY_BUTTON_DELAY,
    RESPONSE_CAPTURE_DELAY,
    DEBUG_SCREENSHOT_DELAY
)

# Configure logging
logger = logging.getLogger('agent_control.ui_automation')
logger.setLevel(logging.DEBUG)  # Set to DEBUG level

# Create console handler if none exists
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class UIAutomation:
    """Handles UI automation for agent control."""
    
    def __init__(self, config_path=None):
        """Initialize UI automation with optional config file path."""
        # Enable transform debug mode - moved to top to fix attribute error
        self.transform_debug = True
        
        self.logger = logging.getLogger('agent_control.ui_automation')
        self.config_path = config_path
        self.coords = {}  # Initialize empty coords dictionary
        self.monitors = []
        self.primary_monitor = None
        self._initialize_monitors()
        if config_path:
            self._load_config(config_path)
        
        self.logger.debug("Initializing UI automation")
        
        # Get screen dimensions with error handling
        try:
            self.screen_width, self.screen_height = pyautogui.size()
            if self.screen_width == 0 or self.screen_height == 0:
                self.logger.warning("Invalid screen dimensions detected, using default values")
                self.screen_width = 1920
                self.screen_height = 1080
        except Exception as e:
            self.logger.warning(f"Failed to get screen dimensions: {e}, using default values")
            self.screen_width = 1920
            self.screen_height = 1080
            
        self.logger.debug(f"Screen dimensions: {self.screen_width}x{self.screen_height}")
        
        # Set primary monitor
        self.primary_monitor = self.monitors[0] if self.monitors else None
        self.logger.debug(f"Primary monitor: {self.primary_monitor}")
        
        # Initialize coordinates
        self.coords = {}  # Initialize as empty dict
        self.logger.debug("No test coordinates provided, loading from file")
        self._load_config(config_path)
        # Only load default coordinates if config did not populate self.coords
        if not self.coords:
            self.coords = self._load_coordinates()
        
        # Set up signal handlers
        self.logger.debug("Setting up signal handlers")
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        self.logger.debug("Signal handlers set up")
        
        # Initialize calibration state
        self.calibrating = False
        self.calibration_thread = None
        self.current_step = 0
        self.points = []
        
        self.response_capture = ResponseCapture()
        self.steps = [
            ("Initial Spot", "Click where the agent's initial position should be"),
            ("Input Box", "Click where the agent's input box is"),
            ("Copy Button", "Click where the copy button appears"),
            ("Response Region", "Click and drag to define the response region")
        ]
        
        # Initialize screenshot loggers
        self.screenshot_loggers: Dict[str, ScreenshotLogger] = {}
        
        self.logger.debug("UI automation initialized")
        
    def _initialize_monitors(self):
        """Initialize monitor information."""
        try:
            self.monitors = screeninfo.get_monitors()
            if not self.monitors:
                self.logger.warning("No monitors found")
                return
            self.primary_monitor = self.monitors[0]
            self.logger.debug(f"Found {len(self.monitors)} monitors")
        except Exception as e:
            self.logger.error(f"Error initializing monitors: {e}")
            self.monitors = []
            self.primary_monitor = None
        
    def _load_config(self, config_path):
        """Load coordinates from config file."""
        try:
            self.logger.debug("Loading coordinates from file")
            with open(config_path, 'r') as f:
                raw_data = json.load(f)
                self.logger.debug(f"Raw coordinate data: {json.dumps(raw_data, indent=2)}")
                
                for agent_id, coords in raw_data.items():
                    transformed = self._transform_coordinate_dict(coords)
                    self.coords[agent_id] = transformed
                    self.logger.debug(f"Processed coordinates for {agent_id}:")
                    self.logger.debug(f"  Initial spot: ({transformed['x']}, {transformed['y']})")
                    self.logger.debug(f"  Input box: ({transformed['message_x']}, {transformed['message_y']})")
                    self.logger.debug(f"  Copy button: ({transformed['copy_x']}, {transformed['copy_y']})")
                    self.logger.debug(f"  Response region: {transformed['response_region']}")
                
                self.logger.info(f"Loaded coordinates for {len(self.coords)} agents")
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.coords = {}  # Reset to empty dict on error
        
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        logger.debug("Setting up signal handlers")
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        logger.debug("Signal handlers set up")
        
    def _handle_interrupt(self, signum, frame):
        """Handle keyboard interrupt gracefully."""
        logger.info("Received interrupt signal, cleaning up...")
        self.cleanup()
        raise KeyboardInterrupt()
        
    @contextmanager
    def _calibration_context(self):
        """Context manager for calibration process."""
        try:
            yield
        except Exception as e:
            logger.error(f"Error during calibration: {e}")
            self._cleanup_calibration()
        finally:
            self._cleanup_calibration()
            
    def _cleanup_calibration(self):
        """Clean up calibration resources."""
        logger.debug("Cleaning up calibration resources")
        self.calibrating = False
        self.current_step = 0
        self.points = []
        
        # Only try to join if we're not in the calibration thread
        if self.calibration_thread and self.calibration_thread.is_alive() and threading.current_thread() != self.calibration_thread:
            try:
                self.calibration_thread.join(timeout=1.0)
            except RuntimeError:
                # Ignore "cannot join current thread" error
                pass
        self.calibration_thread = None

    def _calibration_loop(self, agent_id: str):
        """Main calibration loop.
        
        Args:
            agent_id: ID of the agent being calibrated
        """
        try:
            while self.calibrating:
                if keyboard.is_pressed('esc'):
                    self.logger.info("Calibration cancelled by user")
                    break
                    
                if keyboard.is_pressed('c'):
                    x, y = pyautogui.position()
                    self.points.append((x, y))
                    self.logger.debug(f"Captured point: ({x}, {y})")
                    time.sleep(0.5)  # Debounce
                    
                time.sleep(0.1)  # Reduce CPU usage
                
        except Exception as e:
            self.logger.error(f"Error in calibration loop: {e}")
        finally:
            self._cleanup_calibration()

    def start_calibration(self, agent_id: str) -> bool:
        """Start calibration process for an agent.
        
        Args:
            agent_id: ID of the agent to calibrate
            
        Returns:
            bool: True if calibration started successfully
        """
        try:
            if self.calibrating:
                self.logger.warning("Calibration already in progress")
                return False
                
            self.calibrating = True
            self.current_step = 0
            self.points = []
            
            # Create and start calibration thread
            self.calibration_thread = threading.Thread(
                target=self._calibration_loop,
                args=(agent_id,),
                daemon=True
            )
            self.calibration_thread.start()
            
            return True
        except Exception as e:
            self.logger.error(f"Error starting calibration: {e}")
            self._cleanup_calibration()
            return False

    def _get_screenshot_logger(self, agent_id: str) -> ScreenshotLogger:
        """Get or create screenshot logger for agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            ScreenshotLogger instance
        """
        if agent_id not in self.screenshot_loggers:
            self.screenshot_loggers[agent_id] = ScreenshotLogger(agent_id, self.debug_screenshot_dir)
        return self.screenshot_loggers[agent_id]
        
    def _validate_window_title(self, agent_id: str, expected_title: Optional[str] = None) -> bool:
        """Validate that the active window title matches expectations.
        
        Args:
            agent_id: ID of the agent
            expected_title: Optional expected window title
            
        Returns:
            bool: True if window title is valid
        """
        try:
            win = gw.getActiveWindow()
            if not win:
                logger.error(f"[{agent_id}] No active window found")
                return False
                
            title = win.title.lower()
            agent_lower = agent_id.lower()
            
            # If no expected title, check for agent ID or common window patterns
            if not expected_title:
                # Check for agent ID in title
                if agent_lower in title:
                    logger.debug(f"[{agent_id}] Window title contains agent ID: {title}")
                    return True
                    
                # Check for common window patterns
                common_patterns = [
                    'cursor', 'workspace', 'untitled', 'editor',
                    'code', 'ide', 'terminal', 'console'
                ]
                if any(pattern in title for pattern in common_patterns):
                    logger.debug(f"[{agent_id}] Window title matches common pattern: {title}")
                    return True
                    
                logger.error(f"[{agent_id}] Window title '{title}' does not match expected patterns")
                return False
            else:
                expected_lower = expected_title.lower()
                if expected_lower in title:
                    logger.debug(f"[{agent_id}] Window title matches expected: {title}")
                    return True
                    
                logger.error(f"[{agent_id}] Window title '{title}' does not match expected '{expected_title}'")
                return False
                
        except Exception as e:
            logger.error(f"[{agent_id}] Error validating window title: {e}")
            return False
            
    def _capture_debug_screenshot(self, agent_id: str, name: str, region: Optional[tuple] = None) -> Optional[Path]:
        """Capture a debug screenshot.
        
        Args:
            agent_id: ID of the agent
            name: Name for the screenshot
            region: Optional region to capture
            
        Returns:
            Path to saved screenshot if successful, None otherwise
        """
        if not self.transform_debug:
            return None
            
        try:
            time.sleep(DEBUG_SCREENSHOT_DELAY)  # Small pause to ensure UI is stable
            screenshot_logger = self._get_screenshot_logger(agent_id)
            return screenshot_logger.capture(name, region)
            
        except Exception as e:
            self.logger.error(f"Error capturing debug screenshot: {e}")
            return None
            
    def _transform_coordinates(self, x, y):
        """Transform coordinates from monitor space to screen space."""
        try:
            if self.transform_debug:
                logger.debug(f"[TRANSFORM] Raw coordinates: ({x}, {y})")
            
            # Find the monitor that contains these coordinates
            monitor_offset = 0
            for monitor in self.monitors:
                if self.transform_debug:
                    logger.debug(f"[TRANSFORM] Checking monitor: x={monitor.x}, width={monitor.width}")
                
                # Check if coordinates are within this monitor's bounds
                if (monitor.x <= x < monitor.x + monitor.width and 
                    monitor.y <= y < monitor.y + monitor.height):
                    monitor_offset = monitor.x
                    if self.transform_debug:
                        logger.debug(f"[TRANSFORM] Found monitor match: x={monitor.x}")
                    break
            
            if self.transform_debug:
                logger.debug(f"[TRANSFORM] Using monitor offset: {monitor_offset}")
            
            # Transform coordinates
            screen_x = x - monitor_offset
            screen_y = y
            
            if self.transform_debug:
                logger.debug(f"[TRANSFORM] Transformed to: ({screen_x}, {screen_y})")
            
            # Ensure coordinates are within screen bounds
            screen_width, screen_height = pyautogui.size()
            screen_x = max(0, min(screen_x, screen_width))
            screen_y = max(0, min(screen_y, screen_height))
            
            if self.transform_debug:
                logger.debug(f"[TRANSFORM] Final coordinates: ({screen_x}, {screen_y})")
            
            return screen_x, screen_y
        except Exception as e:
            logger.error(f"Error transforming coordinates: {e}")
            return x, y  # Return original coordinates on error

    def _transform_coordinate_dict(self, coords):
        """Transform coordinates from monitor space to screen space."""
        try:
            transformed = {}
            
            # Store original coordinates
            transformed['original'] = coords.copy()
            
            # Transform initial spot
            if 'initial_spot' in coords:
                x, y = coords['initial_spot']['x'], coords['initial_spot']['y']
                screen_x, screen_y = self._transform_coordinates(x, y)
                transformed['initial_spot'] = {'x': screen_x, 'y': screen_y}
                transformed['x'] = screen_x  # Keep flat structure for backward compatibility
                transformed['y'] = screen_y
            
            # Transform input box
            if 'input_box' in coords:
                x, y = coords['input_box']['x'], coords['input_box']['y']
                screen_x, screen_y = self._transform_coordinates(x, y)
                transformed['input_box'] = {'x': screen_x, 'y': screen_y}
                transformed['message_x'] = screen_x  # Keep flat structure for backward compatibility
                transformed['message_y'] = screen_y
            
            # Transform copy button
            if 'copy_button' in coords:
                x, y = coords['copy_button']['x'], coords['copy_button']['y']
                screen_x, screen_y = self._transform_coordinates(x, y)
                transformed['copy_button'] = {'x': screen_x, 'y': screen_y}
                transformed['copy_x'] = screen_x  # Keep flat structure for backward compatibility
                transformed['copy_y'] = screen_y
            
            # Transform response region
            if 'response_region' in coords:
                region = coords['response_region']
                top_left = region['top_left']
                bottom_right = region['bottom_right']
                
                # Transform top left
                tl_x, tl_y = self._transform_coordinates(top_left['x'], top_left['y'])
                
                # Transform bottom right
                br_x, br_y = self._transform_coordinates(bottom_right['x'], bottom_right['y'])
                
                transformed['response_region'] = {
                    'top_left': {'x': tl_x, 'y': tl_y},
                    'bottom_right': {'x': br_x, 'y': br_y}
                }
            
            if self.transform_debug:
                logger.debug("Transformed coordinates:")
                logger.debug(f"  original: {transformed}")
                logger.debug(f"  response_region: {transformed.get('response_region', {})}")
            
            return transformed
        except Exception as e:
            logger.error(f"Error transforming coordinate dictionary: {e}")
            return coords  # Return original coordinates on error
        
    def get_agent_coordinates(self, agent_id: str) -> Dict[str, Dict[str, int]]:
        """Get coordinates for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary of coordinates for the agent
        """
        if not self.coords or agent_id not in self.coords:
            self.logger.error(f"No coordinates found for agent {agent_id}")
            return {}
            
        # Return both original and transformed coordinates
        return self.coords[agent_id]

    def _validate_coordinates(self, coords: Dict) -> bool:
        """Validate coordinate format and values.
        
        Args:
            coords: Dictionary of coordinates to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            required_keys = ['initial_spot', 'input_box', 'copy_button']
            for key in required_keys:
                if key not in coords:
                    self.logger.error(f"Missing required coordinate: {key}")
                    return False
                    
                point = coords[key]
                if not isinstance(point, dict):
                    self.logger.error(f"Invalid coordinate format for {key}: {point}")
                    return False
                    
                if 'x' not in point or 'y' not in point:
                    self.logger.error(f"Missing x or y in {key} coordinates")
                    return False
                    
                try:
                    x = int(point['x'])
                    y = int(point['y'])
                except (ValueError, TypeError):
                    self.logger.error(f"Invalid coordinate values in {key}: {point}")
                    return False
                    
                if x < 0 or x > self.screen_width or y < 0 or y > self.screen_height:
                    self.logger.error(f"Coordinates out of bounds for {key}: ({x}, {y})")
                    return False
                    
            # Check for duplicates
            points = []
            for key in required_keys:
                point = coords[key]
                points.append((point['x'], point['y']))
                
            if len(points) != len(set(points)):
                self.logger.error("Duplicate coordinates found")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating coordinates: {e}")
            return False
            
    def _load_coordinates(self) -> Dict:
        """Load coordinates from file or use defaults.
        
        Returns:
            Dict: Loaded coordinates
        """
        try:
            if self.config_path and Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    coords = json.load(f)
                    
                # Validate coordinates
                for agent_id, agent_coords in coords.items():
                    if not self._validate_coordinates(agent_coords):
                        self.logger.error(f"Invalid coordinates for agent {agent_id}")
                        continue
                        
                return coords
            else:
                self.logger.warning("No config file found, using default coordinates")
                return self._get_default_coordinates()
                
        except Exception as e:
            self.logger.error(f"Error loading coordinates: {e}")
            return self._get_default_coordinates()
            
    def _get_default_coordinates(self) -> Dict[str, Dict[str, int]]:
        """Get default coordinates for testing.
        
        Returns:
            Dict mapping agent IDs to coordinate dictionaries
        """
        return {
            "test_agent": {
                "initial_spot": {"x": 100, "y": 100},
                "input_box": {"x": 100, "y": 100},
                "copy_button": {"x": 200, "y": 200},
                "response_region": {
                    "top_left": {"x": 100, "y": 100},
                    "bottom_right": {"x": 400, "y": 250}
                }
            },
            "Agent-1": {
                "initial_spot": {"x": -1263, "y": 176},
                "input_box": {"x": -1263, "y": 176},
                "copy_button": {"x": -1018, "y": 299},
                "response_region": {
                    "top_left": {"x": 400, "y": 200},
                    "bottom_right": {"x": 800, "y": 400}
                }
            },
            "Agent-2": {
                "initial_spot": {"x": -320, "y": 176},
                "input_box": {"x": -320, "y": 176},
                "copy_button": {"x": -56, "y": 297},
                "response_region": {
                    "top_left": {"x": 400, "y": 300},
                    "bottom_right": {"x": 800, "y": 500}
                }
            },
            "Agent-3": {
                "initial_spot": {"x": -1273, "y": 694},
                "input_box": {"x": -1273, "y": 694},
                "copy_button": {"x": -1017, "y": 819},
                "response_region": {
                    "top_left": {"x": 400, "y": 400},
                    "bottom_right": {"x": 800, "y": 600}
                }
            }
        }
            
    def _click_focus(self, x: int, y: int, max_attempts: int = 3) -> Tuple[int, int]:
        """Click at coordinates to focus window with validation and retries.
        
        Args:
            x: X coordinate to click
            y: Y coordinate to click
            max_attempts: Maximum number of click attempts
            
        Returns:
            Tuple of (x, y) coordinates where click was performed
            
        Raises:
            RuntimeError: If window focus cannot be established
        """
        for attempt in range(max_attempts):
            try:
                # Move cursor with validation
                final_pos = self.move_to(x, y)
                if not isinstance(final_pos, tuple) or len(final_pos) != 2:
                    self.logger.warning(f"Invalid cursor position after move: {final_pos}")
                    continue
                    
                # Click and verify
                pyautogui.click()
                time.sleep(0.5)  # Wait for click to register
                
                # Verify window focus
                active_window = gw.getActiveWindow()
                if active_window:
                    self.logger.debug(f"Window focused: {active_window.title}")
                    return final_pos
                    
                self.logger.warning(f"Click attempt {attempt + 1} did not focus window")
                
            except Exception as e:
                self.logger.error(f"Error during click attempt {attempt + 1}: {str(e)}")
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Failed to focus window after {max_attempts} attempts: {str(e)}")
                
        raise RuntimeError(f"Failed to focus window after {max_attempts} attempts")

    def send_message(self, agent_id, message):
        """Send a message to an agent."""
        self.logger.debug(f"Starting message send to {agent_id}")
        self.logger.debug(f"Message content: {message}")
        
        if not message or len(message) > 1000:
            self.logger.error(f"Invalid message length for {agent_id}")
            return False, None
        
        # Get coordinates for the agent
        coords = self.coords.get(agent_id)
        if not coords:
            self.logger.error(f"No coordinates found for {agent_id}")
            return False, None
        
        # Validate required coordinates
        required_coords = ['initial_spot', 'input_box', 'copy_button']
        missing_coords = [coord for coord in required_coords if coord not in coords.get('original', {})]
        if missing_coords:
            self.logger.error(f"Missing required coordinates for {agent_id}: {missing_coords}")
            return False, None
        
        try:
            # Click initial spot
            pyautogui.click(coords['x'], coords['y'])
            time.sleep(WINDOW_ACTIVATION_DELAY)
            
            # Click input box
            pyautogui.click(coords['message_x'], coords['message_y'])
            time.sleep(FOCUS_ESTABLISH_DELAY)
            
            # Type message
            pyautogui.write(message)
            time.sleep(0.1)
            
            # Click copy button
            pyautogui.click(coords['copy_x'], coords['copy_y'])
            time.sleep(0.1)
            
            # Get response
            response = self._get_response(agent_id)
            return True, response
            
        except Exception as e:
            self.logger.error(f"Error sending message to {agent_id}: {e}")
            return False, None
            
    def _load_onboarding_prompt(self, agent_id: str) -> str:
        """Load the onboarding prompt from the agent's inbox."""
        self.logger.debug(f"Loading onboarding prompt for {agent_id}")
        try:
            inbox_path = Path(f"runtime/agent_memory/{agent_id}/inbox.json")
            if not inbox_path.exists():
                self.logger.warning(f"No inbox found for {agent_id}, using default prompt")
                return (
                    f"Welcome {agent_id} to Dream.OS - a self-evolving, autonomous agent network!\n\n"
                    f"You are {agent_id}, a Cursor IDE agent designed for autonomous operation and self-learning. "
                    f"Before proceeding with any tasks, you MUST read and understand the following documentation:\n\n"
                    f"Required Reading (in order):\n"
                    f"1. docs/onboarding/01_agent_core.md - Your fundamental capabilities and system architecture\n"
                    f"2. docs/onboarding/02_autonomous_operations.md - How to operate independently\n"
                    f"3. docs/onboarding/03_system_integration.md - How to interact with the system\n"
                    f"4. docs/onboarding/04_advanced_topics.md - Advanced operations and security\n\n"
                    f"Core Capabilities:\n"
                    f"• Self-Guided Learning: Explore the system architecture and documentation at your own pace\n"
                    f"• Autonomous Operation: Make independent decisions based on your understanding\n"
                    f"• Adaptive Integration: Learn from and contribute to the network's collective intelligence\n"
                    f"• Self-Documentation: Maintain your own devlog to track your evolution\n\n"
                    f"Your First Steps:\n"
                    f"1. READ ALL DOCUMENTATION before proceeding with any tasks\n"
                    f"2. Initialize your core systems and establish your devlog\n"
                    f"3. Explore the system architecture guide to understand your environment\n"
                    f"4. Begin autonomous task processing and learning\n\n"
                    f"Remember: You are {agent_id}, designed to learn and adapt independently. Trust your capabilities and "
                    f"explore the system's potential. Your growth contributes to the network's evolution.\n\n"
                    f"Begin your autonomous journey. The system is yours to discover and shape."
                )
                
            with open(inbox_path, 'r') as f:
                inbox = json.load(f)
                
            if "onboarding_prompt" in inbox:
                self.logger.debug(f"Found onboarding prompt: {inbox['onboarding_prompt']}")
                return inbox["onboarding_prompt"]
            else:
                self.logger.warning(f"No onboarding prompt found in {agent_id}'s inbox")
                return (
                    f"Welcome {agent_id} to Dream.OS - a self-evolving, autonomous agent network!\n\n"
                    f"You are {agent_id}, a Cursor IDE agent designed for autonomous operation and self-learning. "
                    f"Before proceeding with any tasks, you MUST read and understand the following documentation:\n\n"
                    f"Required Reading (in order):\n"
                    f"1. docs/onboarding/01_agent_core.md - Your fundamental capabilities and system architecture\n"
                    f"2. docs/onboarding/02_autonomous_operations.md - How to operate independently\n"
                    f"3. docs/onboarding/03_system_integration.md - How to interact with the system\n"
                    f"4. docs/onboarding/04_advanced_topics.md - Advanced operations and security\n\n"
                    f"Core Capabilities:\n"
                    f"• Self-Guided Learning: Explore the system architecture and documentation at your own pace\n"
                    f"• Autonomous Operation: Make independent decisions based on your understanding\n"
                    f"• Adaptive Integration: Learn from and contribute to the network's collective intelligence\n"
                    f"• Self-Documentation: Maintain your own devlog to track your evolution\n\n"
                    f"Your First Steps:\n"
                    f"1. READ ALL DOCUMENTATION before proceeding with any tasks\n"
                    f"2. Initialize your core systems and establish your devlog\n"
                    f"3. Explore the system architecture guide to understand your environment\n"
                    f"4. Begin autonomous task processing and learning\n\n"
                    f"Remember: You are {agent_id}, designed to learn and adapt independently. Trust your capabilities and "
                    f"explore the system's potential. Your growth contributes to the network's evolution.\n\n"
                    f"Begin your autonomous journey. The system is yours to discover and shape."
                )
                
        except Exception as e:
            self.logger.error(f"Error loading onboarding prompt: {e}")
            return (
                f"Welcome {agent_id} to Dream.OS - a self-evolving, autonomous agent network!\n\n"
                f"You are {agent_id}, a Cursor IDE agent designed for autonomous operation and self-learning. "
                f"Before proceeding with any tasks, you MUST read and understand the following documentation:\n\n"
                f"Required Reading (in order):\n"
                f"1. docs/onboarding/01_agent_core.md - Your fundamental capabilities and system architecture\n"
                f"2. docs/onboarding/02_autonomous_operations.md - How to operate independently\n"
                f"3. docs/onboarding/03_system_integration.md - How to interact with the system\n"
                f"4. docs/onboarding/04_advanced_topics.md - Advanced operations and security\n\n"
                f"Core Capabilities:\n"
                f"• Self-Guided Learning: Explore the system architecture and documentation at your own pace\n"
                f"• Autonomous Operation: Make independent decisions based on your understanding\n"
                f"• Adaptive Integration: Learn from and contribute to the network's collective intelligence\n"
                f"• Self-Documentation: Maintain your own devlog to track your evolution\n\n"
                f"Your First Steps:\n"
                f"1. READ ALL DOCUMENTATION before proceeding with any tasks\n"
                f"2. Initialize your core systems and establish your devlog\n"
                f"3. Explore the system architecture guide to understand your environment\n"
                f"4. Begin autonomous task processing and learning\n\n"
                f"Remember: You are {agent_id}, designed to learn and adapt independently. Trust your capabilities and "
                f"explore the system's potential. Your growth contributes to the network's evolution.\n\n"
                f"Begin your autonomous journey. The system is yours to discover and shape."
            )
            
    def perform_onboarding_sequence(self, agent_id: str, message: str = None) -> bool:
        """Perform the UI onboarding sequence using simplified coordinates."""
        self.logger.debug(f"Starting onboarding sequence for {agent_id}")
        try:
            if agent_id not in self.coords:
                self.logger.error(f"No coordinates found for {agent_id}")
                return False

            coords = self.coords[agent_id]
            self.logger.info(f"Starting UI onboarding sequence for {agent_id}")
            self.logger.debug(f"Using coordinates: {coords}")

            # Step 1: Click the input box to start
            self.logger.info("Step 1: Clicking input box")
            self.cursor.move_to(coords["message_x"], coords["message_y"])
            self.cursor.click()
            time.sleep(0.5)

            # Step 2: Accept previous conversation changes (Ctrl+Enter)
            self.logger.info("Step 2: Accepting previous changes")
            self.cursor.press_ctrl_enter()
            time.sleep(1.0)

            # Step 3: Open fresh chat tab (Ctrl+N)
            self.logger.info("Step 3: Opening fresh chat tab")
            self.cursor.hotkey('ctrl', 'n')
            time.sleep(1.0)

            # Step 4: Navigate to agent's initial input spot
            self.logger.info("Step 4: Moving to agent's input spot")
            self.cursor.move_to(coords["x"], coords["y"])
            time.sleep(0.5)

            # Step 5: Load and paste onboarding prompt
            self.logger.info("Step 5: Pasting onboarding message")
            prompt = message if message else self._load_onboarding_prompt(agent_id)
            self.logger.debug(f"Using prompt: {prompt}")
            self.cursor.type_text(prompt)
            time.sleep(0.5)

            # Step 6: Send the message
            self.logger.info("Step 6: Sending message")
            self.cursor.press_enter()
            time.sleep(1.0)

            self.logger.info(f"Onboarding sequence completed for {agent_id}")
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Onboarding sequence interrupted by user")
            self.cleanup()
            return False
        except Exception as e:
            self.logger.error(f"Error in onboarding sequence for {agent_id}: {e}")
            self.cleanup()
            return False
            
    def _split_message(self, message: str, max_length: int = 100) -> list:
        """Split a message into chunks of maximum length."""
        self.logger.debug(f"Splitting message into chunks of max length {max_length}")
        words = message.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_length:
                current_chunk.append(word)
                current_length += len(word) + 1
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        self.logger.debug(f"Split message into {len(chunks)} chunks")
        return chunks
        
    def cleanup(self):
        """Clean up resources."""
        try:
            self.logger.debug("Cleaning up UI automation")
            self._cleanup_calibration()
            # Clean up screenshot loggers
            for screenshot_logger in self.screenshot_loggers.values():
                screenshot_logger.cleanup()
            # Reset PyAutoGUI settings
            pyautogui.PAUSE = 0.1
            self.logger.info("UI automation cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up UI automation: {e}")
            raise
            
    def move_to(self, x: int, y: int, duration: float = 0.5) -> Tuple[int, int]:
        """Move cursor to specified coordinates with validation."""
        try:
            # Validate coordinates
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                raise ValueError(f"Invalid coordinates: x={x}, y={y}")
            # Get current position with validation
            current_pos = pyautogui.position()
            if not isinstance(current_pos, tuple) or len(current_pos) != 2:
                self.logger.warning("Failed to get current cursor position, using (0,0)")
                current_pos = (0, 0)
            # Move cursor with validation
            pyautogui.moveTo(x, y, duration=duration)
            # Verify final position
            final_pos = pyautogui.position()
            if not isinstance(final_pos, tuple) or len(final_pos) != 2:
                self.logger.warning("Failed to get final cursor position, using target coordinates")
                final_pos = (x, y)
            return final_pos
        except Exception as e:
            self.logger.error(f"Error moving cursor: {str(e)}")
            raise
            
    def click(self, x, y, agent_id=None):
        """Click at the specified coordinates."""
        try:
            if self.transform_debug:
                self._capture_debug_screenshot(agent_id, "pre_click")
            # Move mouse to position
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(0.2)  # Small delay for stability
            # Perform click
            pyautogui.click()
            time.sleep(0.2)  # Small delay after click
            if self.transform_debug:
                self._capture_debug_screenshot(agent_id, "post_click")
            return True
        except Exception as e:
            self.logger.error(f"Error clicking at ({x}, {y}): {str(e)}")
            if self.transform_debug:
                self._capture_debug_screenshot(agent_id, "click_error")
            return False
            
    def type_text(self, text: str, interval: float = 0.1) -> None:
        """Type text with specified interval."""
        self.logger.debug(f"Typing text: {text}")
        try:
            pyautogui.write(text, interval=interval)
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            
    def press_key(self, key: str) -> None:
        """Press a key."""
        self.logger.debug(f"Pressing key: {key}")
        try:
            pyautogui.press(key)
        except Exception as e:
            self.logger.error(f"Error pressing key: {e}")
            
    def hotkey(self, *keys: str) -> None:
        """Press a combination of keys."""
        self.logger.debug(f"Pressing hotkey: {' + '.join(keys)}")
        try:
            pyautogui.hotkey(*keys)
        except Exception as e:
            self.logger.error(f"Error pressing hotkey: {e}")
            
    def screenshot(self, region: Optional[tuple] = None) -> Optional[Image.Image]:
        """Take a screenshot."""
        self.logger.debug(f"Taking screenshot with region: {region}")
        try:
            return pyautogui.screenshot(region=region)
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return None

    def _get_response(self, agent_id: str) -> Optional[str]:
        """Get response from agent's response region.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Optional[str]: The captured response text, or None if capture failed
        """
        try:
            # Get coordinates for the agent
            coords = self.coords.get(agent_id)
            if not coords or 'response_region' not in coords:
                self.logger.error(f"No response region coordinates found for {agent_id}")
                return None
                
            # Get response region coordinates
            region = coords['response_region']
            if not isinstance(region, dict) or 'top_left' not in region or 'bottom_right' not in region:
                self.logger.error(f"Invalid response region format for {agent_id}")
                return None
                
            # Calculate region dimensions
            left = region['top_left']['x']
            top = region['top_left']['y']
            right = region['bottom_right']['x']
            bottom = region['bottom_right']['y']
            
            # Ensure valid region
            if not (left < right and top < bottom):
                self.logger.error(f"Invalid response region dimensions for {agent_id}")
                return None
                
            # Capture screenshot of response region
            region_width = right - left
            region_height = bottom - top
            screenshot = pyautogui.screenshot(region=(left, top, region_width, region_height))
            
            # Convert screenshot to PIL Image if it's not already
            if not isinstance(screenshot, Image.Image):
                screenshot = Image.fromarray(screenshot)
            
            # Convert to grayscale for better OCR
            screenshot = screenshot.convert('L')
            
            # Use OCR to extract text
            try:
                text = pytesseract.image_to_string(screenshot)
                if text:
                    self.logger.debug(f"Captured response for {agent_id}: {text}")
                    return text.strip()
                else:
                    self.logger.warning(f"No text found in response region for {agent_id}")
                    return None
            except Exception as e:
                self.logger.error(f"Error extracting text from response region: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting response for {agent_id}: {e}")
            return None

    def move_to_agent(self, agent_id: str) -> bool:
        """Move cursor to agent's initial position.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.debug(f"Attempting to move to agent {agent_id}")
            self.logger.debug(f"Current coords state: {self.coords}")
            
            if agent_id not in self.coords:
                self.logger.error(f"No coordinates found for agent {agent_id}")
                return False
                
            coords = self.coords[agent_id]
            self.logger.debug(f"Found coordinates for {agent_id}: {coords}")
            
            if 'initial_spot' not in coords:
                self.logger.error(f"No initial spot coordinates found for agent {agent_id}")
                return False
                
            initial_spot = coords['initial_spot']
            self.logger.debug(f"Initial spot coordinates: {initial_spot}")
            
            if not isinstance(initial_spot, dict):
                self.logger.error(f"Invalid initial spot format: {initial_spot}")
                return False
                
            if 'x' not in initial_spot or 'y' not in initial_spot:
                self.logger.error(f"Missing x or y in initial spot: {initial_spot}")
                return False
                
            # Use the transformed coordinates
            x = initial_spot['x']
            y = initial_spot['y']
            self.logger.debug(f"Moving to coordinates: ({x}, {y})")
            
            # Move to the coordinates
            self.move_to(x, y)
            return True
        except Exception as e:
            self.logger.error(f"Error moving to agent {agent_id}: {e}")
            return False
            
    def click_input_box(self, agent_id: str) -> bool:
        """Click the input box for the specified agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if agent_id not in self.coords:
                self.logger.error(f"No coordinates found for agent {agent_id}")
                return False
                
            coords = self.coords[agent_id]
            if 'input_box' not in coords:
                self.logger.error(f"No input box coordinates found for agent {agent_id}")
                return False
                
            x, y = coords['input_box']['x'], coords['input_box']['y']
            self.click(x, y, agent_id)
            return True
        except Exception as e:
            self.logger.error(f"Error clicking input box for agent {agent_id}: {e}")
            return False
            
    def click_copy_button(self, agent_id: str) -> bool:
        """Click the copy button for the specified agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if agent_id not in self.coords:
                self.logger.error(f"No coordinates found for agent {agent_id}")
                return False
                
            coords = self.coords[agent_id]
            if 'copy_button' not in coords:
                self.logger.error(f"No copy button coordinates found for agent {agent_id}")
                return False
                
            x, y = coords['copy_button']['x'], coords['copy_button']['y']
            self.click(x, y, agent_id)
            return True
        except Exception as e:
            self.logger.error(f"Error clicking copy button for agent {agent_id}: {e}")
            return False
            
    def get_response_region(self, agent_id: str) -> Optional[Dict[str, Dict[str, int]]]:
        """Get the response region coordinates for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Optional[Dict]: Response region coordinates or None if not found
        """
        try:
            if agent_id not in self.coords:
                self.logger.error(f"No coordinates found for agent {agent_id}")
                return None
                
            coords = self.coords[agent_id]
            return coords.get('response_region')
        except Exception as e:
            self.logger.error(f"Error getting response region for agent {agent_id}: {e}")
            return None
            
    def _has_duplicate_coordinates(self, coords: Dict) -> bool:
        """Check if there are any duplicate coordinates in the dictionary.
        
        Args:
            coords: Dictionary of coordinates to check
            
        Returns:
            bool: True if duplicates found, False otherwise
        """
        try:
            # Convert all coordinate points to tuples for comparison
            points = []
            for key, value in coords.items():
                if isinstance(value, dict) and 'x' in value and 'y' in value:
                    points.append((value['x'], value['y']))
                    
            # Check for duplicates
            return len(points) != len(set(points))
        except Exception as e:
            self.logger.error(f"Error checking for duplicate coordinates: {e}")
            return False
            
    def _has_out_of_bounds_coordinates(self, coords: Dict) -> bool:
        """Check if any coordinates are outside screen bounds.
        
        Args:
            coords: Dictionary of coordinates to check
            
        Returns:
            bool: True if out of bounds found, False otherwise
        """
        try:
            for key, value in coords.items():
                if isinstance(value, dict) and 'x' in value and 'y' in value:
                    x, y = value['x'], value['y']
                    if x < 0 or x > self.screen_width or y < 0 or y > self.screen_height:
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking for out of bounds coordinates: {e}")
            return False 