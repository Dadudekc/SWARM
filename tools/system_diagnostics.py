"""
System Diagnostics Dashboard
--------------------------
Unified CLI for running system health checks.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from dreamos.core.monitor.loop_drift_detector import LoopDriftDetector
from dreamos.core.config.config_validator import ConfigValidator
from dreamos.core.utils.find_duplicate_classes import DuplicateClassFinder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemDiagnostics:
    """System diagnostics dashboard."""
    
    def __init__(self, root_dir: str = "."):
        """Initialize dashboard.
        
        Args:
            root_dir: Root directory to analyze
        """
        self.root_dir = Path(root_dir)
        self.tools = {
            "drift": LoopDriftDetector(self.root_dir),
            "config": ConfigValidator(self.root_dir),
            "duplicates": DuplicateClassFinder(self.root_dir)
        }
    
    def run_check(self, check_name: str, **kwargs) -> Dict[str, Any]:
        """Run a specific check.
        
        Args:
            check_name: Name of check to run
            **kwargs: Additional arguments for the check
            
        Returns:
            Check results
        """
        if check_name not in self.tools:
            raise ValueError(f"Unknown check: {check_name}")
        
        tool = self.tools[check_name]
        
        if check_name == "drift":
            return tool.check_all_agents()
        elif check_name == "config":
            return tool.validate_all(strict=kwargs.get("strict", False))
        elif check_name == "duplicates":
            return tool.find_duplicates(min_similarity=kwargs.get("min_similarity", 0.8))
    
    def run_all_checks(self, **kwargs) -> Dict[str, Any]:
        """Run all checks.
        
        Args:
            **kwargs: Additional arguments for checks
            
        Returns:
            Combined results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        for check_name in self.tools:
            try:
                results["checks"][check_name] = self.run_check(check_name, **kwargs)
            except Exception as e:
                logger.error(f"Error running {check_name}: {e}")
                results["checks"][check_name] = {"error": str(e)}
        
        # Calculate overall health score
        results["health_score"] = self._calculate_health_score(results["checks"])
        
        return results
    
    def _calculate_health_score(self, checks: Dict[str, Any]) -> float:
        """Calculate overall health score.
        
        Args:
            checks: Check results
            
        Returns:
            Health score (0-100)
        """
        scores = []
        
        # Drift check score
        if "drift" in checks:
            drift_results = checks["drift"]
            if not drift_results.get("drift_detected", True):
                scores.append(100)
            else:
                # Penalize based on number of drifted agents
                drifted = len([a for a in drift_results.get("agents", []) if a.get("drift")])
                total = len(drift_results.get("agents", []))
                if total > 0:
                    scores.append(100 * (1 - drifted/total))
        
        # Config check score
        if "config" in checks:
            config_results = checks["config"]
            valid = len(config_results.get("valid", []))
            invalid = len(config_results.get("invalid", []))
            total = valid + invalid
            if total > 0:
                scores.append(100 * valid/total)
        
        # Duplicate check score
        if "duplicates" in checks:
            duplicates = checks["duplicates"]
            if not duplicates:
                scores.append(100)
            else:
                # Penalize based on number of duplicates
                num_duplicates = len(duplicates)
                scores.append(max(0, 100 - num_duplicates * 10))
        
        # Average scores
        return sum(scores) / len(scores) if scores else 0
    
    def print_results(self, results: Dict[str, Any], format: str = "text"):
        """Print results in specified format.
        
        Args:
            results: Results to print
            format: Output format ("text" or "json")
        """
        if format == "json":
            print(json.dumps(results, indent=2))
            return
        
        # Print header
        print("\n=== System Diagnostics Report ===")
        print(f"Timestamp: {results['timestamp']}")
        print(f"Overall Health Score: {results['health_score']:.1f}%")
        print("\nDetailed Results:")
        
        # Print drift results
        if "drift" in results["checks"]:
            drift = results["checks"]["drift"]
            print("\n--- Loop Drift Check ---")
            if drift.get("drift_detected"):
                print("❌ Drift detected!")
                for agent in drift.get("agents", []):
                    if agent.get("drift"):
                        print(f"  - {agent['agent_id']} is drifting")
            else:
                print("✅ No drift detected")
        
        # Print config results
        if "config" in results["checks"]:
            config = results["checks"]["config"]
            print("\n--- Config Validation ---")
            if config.get("invalid"):
                print("❌ Invalid configs found:")
                for invalid in config["invalid"]:
                    print(f"  - {invalid['file']}:")
                    for error in invalid["errors"]:
                        print(f"    * {error}")
            else:
                print("✅ All configs valid")
        
        # Print duplicate results
        if "duplicates" in results["checks"]:
            duplicates = results["checks"]["duplicates"]
            print("\n--- Duplicate Classes ---")
            if duplicates:
                print("❌ Duplicate classes found:")
                for class_name, pairs in duplicates.items():
                    print(f"  - {class_name}:")
                    for pair in pairs:
                        print(f"    * {pair['file1']} <-> {pair['file2']}")
                        print(f"      Similarity: {pair['similarity']:.1%}")
            else:
                print("✅ No duplicates found")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="System diagnostics dashboard")
    parser.add_argument("--check", choices=["all", "drift", "config", "duplicates"],
                       default="all", help="Check to run")
    parser.add_argument("--root", default=".", help="Root directory to analyze")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Output format")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--strict", action="store_true",
                       help="Use strict validation for configs")
    parser.add_argument("--min-similarity", type=float, default=0.8,
                       help="Minimum similarity for duplicate detection")
    args = parser.parse_args()
    
    try:
        # Initialize dashboard
        dashboard = SystemDiagnostics(args.root)
        
        # Run checks
        if args.check == "all":
            results = dashboard.run_all_checks(
                strict=args.strict,
                min_similarity=args.min_similarity
            )
        else:
            results = dashboard.run_check(
                args.check,
                strict=args.strict,
                min_similarity=args.min_similarity
            )
        
        # Write results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            dashboard.print_results(results, args.format)
        
        # Exit with status
        if args.check == "all":
            if results["health_score"] < 50:
                sys.exit(1)
        elif args.check == "drift" and results.get("drift_detected"):
            sys.exit(1)
        elif args.check == "config" and results.get("invalid"):
            sys.exit(1)
        elif args.check == "duplicates" and results:
            sys.exit(1)
        
        sys.exit(0)
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 