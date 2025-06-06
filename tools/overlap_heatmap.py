"""
Overlap Heatmap Generator

Generates heatmaps showing agent region overlaps.
"""

import logging
import numpy as np
from PIL import Image, ImageDraw
import pyautogui
from typing import Dict, List, Tuple
import argparse

from dreamos.core.coordinate_utils import (
    load_coordinates,
    regions_overlap,
    calculate_overlap,
    validate_coordinates,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OverlapHeatmapGenerator:
    """Generates heatmaps of agent region overlaps."""
    
    def __init__(self, config_path: str = "config/cursor_agent_coords.json"):
        """Initialize generator.
        
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
                
        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
    def _create_density_map(self, regions: List[Dict]) -> np.ndarray:
        """Create a density map of region overlaps.
        
        Args:
            regions: List of region dictionaries
            
        Returns:
            2D numpy array representing overlap density
        """
        # Initialize density map
        density_map = np.zeros((self.screen_height, self.screen_width))
        
        # For each region
        for region in regions:
            if "top_left" in region and "bottom_right" in region:
                x1 = max(0, region["top_left"]["x"])
                y1 = max(0, region["top_left"]["y"])
                x2 = min(self.screen_width, region["bottom_right"]["x"])
                y2 = min(self.screen_height, region["bottom_right"]["y"])
                
                # Increment density in region
                density_map[y1:y2, x1:x2] += 1
                
        return density_map
        
    def generate_heatmap(self, output_path: str = "overlap_heatmap.png") -> Image.Image:
        """Generate a heatmap of region overlaps.
        
        Args:
            output_path: Path to save the heatmap
            
        Returns:
            PIL Image of the heatmap
        """
        # Get all response regions
        regions = []
        for agent_id, coords in self.coords.items():
            if "response_region" in coords:
                regions.append(coords["response_region"])
                
        # Create density map
        density_map = self._create_density_map(regions)
        
        # Normalize to 0-255 range
        max_density = density_map.max()
        if max_density > 0:
            density_map = (density_map / max_density * 255).astype(np.uint8)
            
        # Create heatmap image
        heatmap = Image.fromarray(density_map)
        
        # Apply colormap
        heatmap = heatmap.convert('RGB')
        pixels = heatmap.load()
        for i in range(heatmap.size[0]):
            for j in range(heatmap.size[1]):
                density = density_map[j, i]
                if density > 0:
                    # Red intensity based on density
                    r = min(255, int(density * 2))
                    # Green and blue decrease with density
                    g = max(0, 255 - r)
                    b = max(0, 255 - r)
                    pixels[i, j] = (r, g, b)
                    
        # Save heatmap
        heatmap.save(output_path)
        logger.info(f"Saved heatmap to {output_path}")
        
        return heatmap
        
    def analyze_overlaps(self) -> Dict:
        """Analyze region overlaps.
        
        Returns:
            Dictionary of overlap analysis
        """
        analysis = {
            "total_regions": 0,
            "overlapping_pairs": [],
            "max_overlap": 0,
            "overlap_distribution": {}
        }
        
        # Get all response regions
        regions = []
        for agent_id, coords in self.coords.items():
            if "response_region" in coords:
                regions.append((agent_id, coords["response_region"]))
                analysis["total_regions"] += 1
                
        # Check each pair of regions
        for i, (agent1, region1) in enumerate(regions):
            for agent2, region2 in regions[i+1:]:
                if regions_overlap(region1, region2):
                    overlap_info = calculate_overlap(region1, region2)
                    analysis["overlapping_pairs"].append({
                        "agents": (agent1, agent2),
                        "overlap_area": overlap_info["area"],
                        "overlap_percentage": overlap_info["percentage"]
                    })
                    
                    # Update max overlap
                    analysis["max_overlap"] = max(
                        analysis["max_overlap"],
                        overlap_info["percentage"]
                    )
                    
                    # Update distribution
                    percentage = int(overlap_info["percentage"] / 10) * 10
                    if percentage not in analysis["overlap_distribution"]:
                        analysis["overlap_distribution"][percentage] = 0
                    analysis["overlap_distribution"][percentage] += 1
                    
        return analysis

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate overlap heatmap")
    parser.add_argument("--config", default="config/cursor_agent_coords.json",
                      help="Path to coordinate configuration file")
    parser.add_argument("--output", default="overlap_heatmap.png",
                      help="Output path for heatmap")
    args = parser.parse_args()
    
    generator = OverlapHeatmapGenerator(args.config)
    
    # Generate heatmap
    generator.generate_heatmap(args.output)
    
    # Print analysis
    analysis = generator.analyze_overlaps()
    print("\nOverlap Analysis:")
    print(f"Total Regions: {analysis['total_regions']}")
    
    if analysis["overlapping_pairs"]:
        print("\nOverlapping Pairs:")
        for pair in analysis["overlapping_pairs"]:
            agent1, agent2 = pair["agents"]
            print(f"  - {agent1} and {agent2}:")
            print(f"    Area: {pair['overlap_area']} pixels")
            print(f"    Percentage: {pair['overlap_percentage']:.1f}%")
            
        print(f"\nMaximum Overlap: {analysis['max_overlap']:.1f}%")
        
        print("\nOverlap Distribution:")
        for percentage, count in sorted(analysis["overlap_distribution"].items()):
            print(f"  {percentage}-{percentage+10}%: {count} pairs")
    else:
        print("\nNo overlapping regions found")

if __name__ == "__main__":
    main() 