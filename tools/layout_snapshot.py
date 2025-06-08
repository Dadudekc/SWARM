"""
Layout Snapshot System

Tracks and manages agent layout snapshots over time for version control and debugging.
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse
from dataclasses import dataclass, asdict
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class LayoutSnapshot:
    """Represents a snapshot of agent layouts."""
    timestamp: str
    hash: str
    coordinates: Dict
    screen_info: Dict
    metadata: Dict

class LayoutSnapshotManager:
    """Manages layout snapshots."""
    
    def __init__(self, snapshot_dir: str = "runtime/layout_snapshots"):
        """Initialize snapshot manager.
        
        Args:
            snapshot_dir: Directory to store snapshots
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_screen_info(self) -> Dict:
        """Get current screen configuration."""
        try:
            import pyautogui
            screen_width, screen_height = pyautogui.size()
            
            info = {
                "total_width": screen_width,
                "total_height": screen_height,
                "monitors": []
            }
            
            try:
                from screeninfo import get_monitors
                for m in get_monitors():
                    info["monitors"].append({
                        "name": m.name,
                        "x": m.x,
                        "y": m.y,
                        "width": m.width,
                        "height": m.height,
                        "is_primary": m.is_primary
                    })
            except ImportError:
                logger.warning("screeninfo not available - using basic screen info")
                
            return info
        except Exception as e:
            logger.error(f"Error getting screen info: {e}")
            return {}
            
    def _compute_hash(self, data: Dict) -> str:
        """Compute hash of layout data."""
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        
    def create_snapshot(self, coordinates: Dict, metadata: Dict = None) -> Optional[LayoutSnapshot]:
        """Create a new layout snapshot.
        
        Args:
            coordinates: Agent coordinates
            metadata: Optional metadata about the snapshot
            
        Returns:
            LayoutSnapshot if successful, None otherwise
        """
        try:
            # Get current screen info
            screen_info = self._get_screen_info()
            
            # Create snapshot
            snapshot = LayoutSnapshot(
                timestamp=datetime.now().isoformat(),
                hash=self._compute_hash(coordinates),
                coordinates=coordinates,
                screen_info=screen_info,
                metadata=metadata or {}
            )
            
            # Save snapshot
            self._save_snapshot(snapshot)
            
            return snapshot
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            return None
            
    def _save_snapshot(self, snapshot: LayoutSnapshot):
        """Save snapshot to disk."""
        try:
            # Create filename with timestamp and hash
            filename = f"layout_{snapshot.timestamp.replace(':', '-')}_{snapshot.hash[:8]}.json"
            filepath = self.snapshot_dir / filename
            
            # Save snapshot
            with open(filepath, 'w') as f:
                json.dump(asdict(snapshot), f, indent=2)
                
            logger.info(f"Saved snapshot to {filepath}")
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
            
    def load_snapshot(self, snapshot_id: str) -> Optional[LayoutSnapshot]:
        """Load a specific snapshot.
        
        Args:
            snapshot_id: Either timestamp or hash of snapshot
            
        Returns:
            LayoutSnapshot if found, None otherwise
        """
        try:
            # Find matching snapshot file
            for file in self.snapshot_dir.glob("layout_*.json"):
                if snapshot_id in file.name:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        return LayoutSnapshot(**data)
            return None
        except Exception as e:
            logger.error(f"Error loading snapshot: {e}")
            return None
            
    def list_snapshots(self) -> List[Dict]:
        """List all available snapshots.
        
        Returns:
            List of snapshot metadata
        """
        snapshots = []
        for file in self.snapshot_dir.glob("layout_*.json"):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    snapshots.append({
                        "timestamp": data["timestamp"],
                        "hash": data["hash"],
                        "metadata": data["metadata"]
                    })
            except Exception as e:
                logger.error(f"Error reading snapshot {file}: {e}")
        return sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)
        
    def compare_snapshots(self, snapshot1_id: str, snapshot2_id: str) -> Dict:
        """Compare two snapshots.
        
        Args:
            snapshot1_id: ID of first snapshot
            snapshot2_id: ID of second snapshot
            
        Returns:
            Dictionary of differences
        """
        snap1 = self.load_snapshot(snapshot1_id)
        snap2 = self.load_snapshot(snapshot2_id)
        
        if not snap1 or not snap2:
            return {"error": "One or both snapshots not found"}
            
        differences = {
            "timestamp_diff": (datetime.fromisoformat(snap2.timestamp) - 
                             datetime.fromisoformat(snap1.timestamp)).total_seconds(),
            "coordinate_changes": {},
            "screen_changes": {}
        }
        
        # Compare coordinates
        for agent_id in set(snap1.coordinates.keys()) | set(snap2.coordinates.keys()):
            if agent_id not in snap1.coordinates:
                differences["coordinate_changes"][agent_id] = "Added"
            elif agent_id not in snap2.coordinates:
                differences["coordinate_changes"][agent_id] = "Removed"
            else:
                agent_diffs = {}
                for key in set(snap1.coordinates[agent_id].keys()) | set(snap2.coordinates[agent_id].keys()):
                    if key not in snap1.coordinates[agent_id]:
                        agent_diffs[key] = "Added"
                    elif key not in snap2.coordinates[agent_id]:
                        agent_diffs[key] = "Removed"
                    elif snap1.coordinates[agent_id][key] != snap2.coordinates[agent_id][key]:
                        agent_diffs[key] = {
                            "from": snap1.coordinates[agent_id][key],
                            "to": snap2.coordinates[agent_id][key]
                        }
                if agent_diffs:
                    differences["coordinate_changes"][agent_id] = agent_diffs
                    
        # Compare screen info
        if snap1.screen_info != snap2.screen_info:
            differences["screen_changes"] = {
                "from": snap1.screen_info,
                "to": snap2.screen_info
            }
            
        return differences

def main():
    """Run the snapshot manager."""
    parser = argparse.ArgumentParser(description="Manage layout snapshots")
    parser.add_argument("--dir", default="runtime/layout_snapshots",
                      help="Snapshot directory")
    parser.add_argument("--list", action="store_true",
                      help="List all snapshots")
    parser.add_argument("--compare", nargs=2,
                      help="Compare two snapshots")
    parser.add_argument("--load", help="Load specific snapshot")
    args = parser.parse_args()
    
    manager = LayoutSnapshotManager(args.dir)
    
    if args.list:
        snapshots = manager.list_snapshots()
        print("\nAvailable Snapshots:")
        for snap in snapshots:
            print(f"\nTimestamp: {snap['timestamp']}")
            print(f"Hash: {snap['hash']}")
            if snap['metadata']:
                print("Metadata:")
                for key, value in snap['metadata'].items():
                    print(f"  {key}: {value}")
                    
    elif args.compare:
        diff = manager.compare_snapshots(args.compare[0], args.compare[1])
        print("\nSnapshot Differences:")
        print(f"Time between snapshots: {diff['timestamp_diff']} seconds")
        
        if diff['coordinate_changes']:
            print("\nCoordinate Changes:")
            for agent_id, changes in diff['coordinate_changes'].items():
                print(f"\n{agent_id}:")
                if isinstance(changes, dict):
                    for key, value in changes.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {changes}")
                    
        if diff['screen_changes']:
            print("\nScreen Changes:")
            print(f"From: {diff['screen_changes']['from']}")
            print(f"To: {diff['screen_changes']['to']}")
            
    elif args.load:
        snapshot = manager.load_snapshot(args.load)
        if snapshot:
            print("\nSnapshot Details:")
            print(f"Timestamp: {snapshot.timestamp}")
            print(f"Hash: {snapshot.hash}")
            print("\nCoordinates:")
            print(json.dumps(snapshot.coordinates, indent=2))
            print("\nScreen Info:")
            print(json.dumps(snapshot.screen_info, indent=2))
            if snapshot.metadata:
                print("\nMetadata:")
                print(json.dumps(snapshot.metadata, indent=2))
        else:
            print(f"No snapshot found with ID: {args.load}")

if __name__ == "__main__":
    main() 
