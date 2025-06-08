"""
Agent Layout Visualizer

Visualizes agent positions and regions on screen for debugging.
"""

import logging
import time
from pathlib import Path
import pyautogui
from PIL import Image, ImageDraw
import numpy as np
from typing import Dict, Tuple, List
import argparse

from dreamos.core.coordinate_utils import (
    load_coordinates,
    regions_overlap,
    validate_coordinates,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentLayoutVisualizer:
    """Visualizes agent positions and regions."""
    
    def __init__(self, config_path: str = "config/cursor_agent_coords.json"):
        """Initialize visualizer.
        
        Args:
            config_path: Path to coordinate configuration file
        """
        self.config_path = config_path
        self.coords = load_coordinates(config_path)
        
        # Validate coordinates
        is_valid, errors = validate_coordinates(self.coords)
        if not is_valid:
            logger.warning("Coordinate validation errors:")
            for error in errors:
                logger.warning(f"  - {error}")
        
        self.colors = {
            "initial_spot": (255, 0, 0),    # Red
            "input_box": (0, 255, 0),       # Green
            "copy_button": (0, 0, 255),     # Blue
            "response_region": (255, 255, 0) # Yellow
        }
        
    def _draw_point(self, draw: ImageDraw.ImageDraw, x: int, y: int, color: Tuple[int, int, int], label: str):
        """Draw a point with label."""
        # Draw point
        draw.ellipse([x-5, y-5, x+5, y+5], fill=color)
        
        # Draw label
        draw.text((x+10, y-10), label, fill=color)
        
    def _draw_region(self, draw: ImageDraw.ImageDraw, region: Dict, color: Tuple[int, int, int], label: str):
        """Draw a region with label."""
        if "top_left" in region and "bottom_right" in region:
            x1 = region["top_left"]["x"]
            y1 = region["top_left"]["y"]
            x2 = region["bottom_right"]["x"]
            y2 = region["bottom_right"]["y"]
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            
            # Draw label
            draw.text((x1, y1-20), label, fill=color)
            
    def visualize_agent(self, agent_id: str, output_path: str = None) -> Image.Image:
        """Visualize a single agent's layout.
        
        Args:
            agent_id: ID of the agent to visualize
            output_path: Optional path to save visualization
            
        Returns:
            PIL Image of the visualization
        """
        if agent_id not in self.coords:
            logger.error(f"No coordinates found for {agent_id}")
            return None
            
        # Take screenshot
        screenshot = pyautogui.screenshot()
        draw = ImageDraw.Draw(screenshot)
        
        # Get agent coordinates
        coords = self.coords[agent_id]
        
        # Draw initial spot
        if "initial_spot" in coords:
            self._draw_point(
                draw,
                coords["initial_spot"]["x"],
                coords["initial_spot"]["y"],
                self.colors["initial_spot"],
                f"{agent_id} Initial"
            )
            
        # Draw input box
        if "input_box" in coords:
            self._draw_point(
                draw,
                coords["input_box"]["x"],
                coords["input_box"]["y"],
                self.colors["input_box"],
                f"{agent_id} Input"
            )
            
        # Draw copy button
        if "copy_button" in coords:
            self._draw_point(
                draw,
                coords["copy_button"]["x"],
                coords["copy_button"]["y"],
                self.colors["copy_button"],
                f"{agent_id} Copy"
            )
            
        # Draw response region
        if "response_region" in coords:
            self._draw_region(
                draw,
                coords["response_region"],
                self.colors["response_region"],
                f"{agent_id} Response"
            )
            
        # Save if path provided
        if output_path:
            screenshot.save(output_path)
            logger.info(f"Saved visualization to {output_path}")
            
        return screenshot
        
    def visualize_all_agents(self, output_dir: str = "visualizations") -> List[Image.Image]:
        """Visualize all agents' layouts.
        
        Args:
            output_dir: Directory to save visualizations
            
        Returns:
            List of PIL Images of the visualizations
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        visualizations = []
        for agent_id in self.coords:
            output_file = output_path / f"{agent_id}_layout.png"
            viz = self.visualize_agent(agent_id, str(output_file))
            if viz:
                visualizations.append(viz)
                
        return visualizations
        
    def analyze_layout(self) -> Dict:
        """Analyze the layout for potential issues.
        
        Returns:
            Dictionary of analysis results
        """
        analysis = {
            "total_agents": len(self.coords),
            "overlapping_regions": [],
            "out_of_bounds": [],
            "monitor_distribution": {}
        }
        
        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        
        # Check for overlapping regions
        regions = []
        for agent_id, coords in self.coords.items():
            if "response_region" in coords:
                region = coords["response_region"]
                regions.append((agent_id, region))
                
        for i, (agent1, region1) in enumerate(regions):
            for agent2, region2 in regions[i+1:]:
                if regions_overlap(region1, region2):
                    analysis["overlapping_regions"].append((agent1, agent2))
                    
        # Check for out of bounds
        for agent_id, coords in self.coords.items():
            for point_type, point in coords.items():
                if isinstance(point, dict) and "x" in point and "y" in point:
                    if (point["x"] < 0 or point["x"] > screen_width or
                        point["y"] < 0 or point["y"] > screen_height):
                        analysis["out_of_bounds"].append((agent_id, point_type))
                        
        # Analyze monitor distribution
        for agent_id, coords in self.coords.items():
            if "response_region" in coords:
                region = coords["response_region"]
                center_x = (region["top_left"]["x"] + region["bottom_right"]["x"]) / 2
                center_y = (region["top_left"]["y"] + region["bottom_right"]["y"]) / 2
                
                # Determine which monitor the center point is on
                monitor = 0
                for i, monitor_info in enumerate(pyautogui.getAllMonitors()):
                    if (monitor_info.left <= center_x <= monitor_info.left + monitor_info.width and
                        monitor_info.top <= center_y <= monitor_info.top + monitor_info.height):
                        monitor = i
                        break
                        
                if monitor not in analysis["monitor_distribution"]:
                    analysis["monitor_distribution"][monitor] = []
                analysis["monitor_distribution"][monitor].append(agent_id)
                
        return analysis

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Visualize agent layouts")
    parser.add_argument("--config", default="config/cursor_agent_coords.json",
                      help="Path to coordinate configuration file")
    parser.add_argument("--output", default="visualizations",
                      help="Output directory for visualizations")
    parser.add_argument("--agent", help="Specific agent ID to visualize")
    args = parser.parse_args()
    
    visualizer = AgentLayoutVisualizer(args.config)
    
    if args.agent:
        visualizer.visualize_agent(args.agent, f"{args.output}/{args.agent}_layout.png")
    else:
        visualizer.visualize_all_agents(args.output)
        
    # Print analysis
    analysis = visualizer.analyze_layout()
    print("\nLayout Analysis:")
    print(f"Total Agents: {analysis['total_agents']}")
    
    if analysis["overlapping_regions"]:
        print("\nOverlapping Regions:")
        for agent1, agent2 in analysis["overlapping_regions"]:
            print(f"  - {agent1} overlaps with {agent2}")
            
    if analysis["out_of_bounds"]:
        print("\nOut of Bounds Points:")
        for agent_id, point_type in analysis["out_of_bounds"]:
            print(f"  - {agent_id} {point_type}")
            
    print("\nMonitor Distribution:")
    for monitor, agents in analysis["monitor_distribution"].items():
        print(f"  Monitor {monitor}: {', '.join(agents)}")

if __name__ == "__main__":
    main() 
