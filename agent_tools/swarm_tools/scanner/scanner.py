"""
DryScanner Module

Note:
This module may emit a RuntimeWarning during import due to Python's module loading sequence.
The warning does not affect functionality and is safe to ignore.

For details, see:
https://github.com/python/cpython/issues/15922
"""

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="agent_tools.swarm_tools.scanner")

import os
import json
import yaml
import ast
import tokenize
import hashlib
import io
from pathlib import Path
from typing import List, Optional, Set, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from collections import defaultdict

@dataclass
class ScanResults:
    """Results from a project scan."""
    duplicates: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    scan_time: datetime = field(default_factory=datetime.now)
    total_files: int = 0
    total_duplicates: int = 0
    top_violators: List[Dict[str, Any]] = field(default_factory=list)
    narrative: str = ""
    themes: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    structural_insights: List[str] = field(default_factory=list)

    def format_summary(self) -> str:
        """Return a brief summary of scan results."""
        return f"""Scan Summary:
Total Files: {self.total_files}
Total Duplicates: {self.total_duplicates}
Scan Time: {self.scan_time.strftime('%Y-%m-%d %H:%M:%S')}
Top Violators: {', '.join(f"{v['file']} ({v['count']})" for v in self.top_violators[:3])}
Themes: {', '.join(f"{theme} ({len(items)} instances)" for theme, items in self.themes.items())}
"""

    def format_full_report(self) -> str:
        """Return a detailed human-readable report."""
        report = [self.format_summary(), "\nDetailed Findings:"]
        
        # Add structural insights
        if self.structural_insights:
            report.append("\nStructural Insights:")
            for insight in self.structural_insights:
                report.append(f"  - {insight}")
        
        # Add theme analysis
        if self.themes:
            report.append("\nTheme Analysis:")
            for theme, items in self.themes.items():
                report.append(f"\n{theme.upper()}:")
                for item in items:
                    report.append(f"  - {item['description']}")
                    report.append(f"    Files: {', '.join(item['files'])}")
        
        # Add detailed findings
        for category, items in self.duplicates.items():
            report.append(f"\n{category.upper()}:")
            for item in items:
                report.append(f"  - {item['name']} ({item['file']}:{item['line']})")
                if 'similar_to' in item:
                    report.append(f"    Similar to: {item['similar_to']}")
                if 'insight' in item:
                    report.append(f"    Insight: {item['insight']}")
        
        if self.narrative:
            report.append(f"\nNarrative:\n{self.narrative}")
        
        return "\n".join(report)

    def summary(self) -> Dict[str, Any]:
        """Return a dictionary with scan statistics."""
        return {
            "type": "scanner_report",
            "total_files": self.total_files,
            "total_duplicates": self.total_duplicates,
            "scan_time": self.scan_time.isoformat(),
            "categories": {
                cat: len(items) for cat, items in self.duplicates.items()
            },
            "top_violators": self.top_violators,
            "themes": self.themes,
            "structural_insights": self.structural_insights,
            "narrative": self.narrative
        }

    def count_duplicates(self) -> int:
        """Return the total number of duplicates found."""
        return self.total_duplicates

class Scanner:
    """Scanner for analyzing project structure."""
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = ScanResults()
        self.similarity_threshold = 0.8  # Configurable threshold for similarity detection
        self._node_cache: Dict[str, List[Dict[str, Any]]] = {}

    def _is_python_file(self, path: Path) -> bool:
        """Check if a file is a Python source file."""
        return path.suffix == '.py' and not path.name.startswith('__')

    def _normalize_source(self, source: str) -> str:
        """Normalize source code by removing docstrings and comments."""
        try:
            tokens = []
            for tok in tokenize.tokenize(io.BytesIO(source.encode('utf-8')).readline):
                if tok.type not in (tokenize.COMMENT, tokenize.STRING):
                    tokens.append(tok.string)
            return ''.join(tokens)
        except tokenize.TokenError:
            return source

    def _hash_code(self, source: str) -> str:
        """Generate a hash of normalized source code."""
        normalized = self._normalize_source(source)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def _get_ast_node_source(self, node: ast.AST, source: str) -> str:
        """Extract source code for an AST node."""
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            lines = source.splitlines()
            return '\n'.join(lines[node.lineno-1:node.end_lineno])
        return ''

    def _calculate_similarity(self, source1: str, source2: str) -> str:
        """Calculate similarity ratio and return insight about the difference."""
        norm1 = self._normalize_source(source1)
        norm2 = self._normalize_source(source2)
        ratio = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Generate insight about the difference
        if ratio == 1.0:
            return "Identical code blocks"
        elif ratio > 0.95:
            return "Nearly identical, differs only in whitespace/comments"
        elif ratio > 0.8:
            return "Similar structure with minor variations"
        else:
            return "Similar pattern but significant differences"

    def _analyze_node(self, node: ast.AST, file_path: Path, source: str) -> Dict[str, Any]:
        """Analyze an AST node and return its metadata."""
        node_source = self._get_ast_node_source(node, source)
        return {
            'name': getattr(node, 'name', str(type(node).__name__)),
            'file': str(file_path.relative_to(self.project_root)),
            'line': getattr(node, 'lineno', 0),
            'source': node_source,
            'hash': self._hash_code(node_source),
            'type': type(node).__name__
        }

    def _scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scans a single file and returns a list of AST node metadata."""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return []

        result = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                result.append(self._analyze_node(node, file_path, content))
        return result

    def _identify_theme(self, node1: Dict[str, Any], node2: Dict[str, Any]) -> str:
        """Identify the theme of duplicate code."""
        if node1['type'] == 'FunctionDef':
            if 'test' in node1['name'].lower() or 'test' in node2['name'].lower():
                return "test_fixtures"
            elif 'handler' in node1['name'].lower() or 'handler' in node2['name'].lower():
                return "request_handlers"
            elif 'process' in node1['name'].lower() or 'process' in node2['name'].lower():
                return "data_processors"
        elif node1['type'] == 'ClassDef':
            if 'Base' in node1['name'] or 'Base' in node2['name']:
                return "base_classes"
            elif 'Test' in node1['name'] or 'Test' in node2['name']:
                return "test_classes"
        return "general_duplicates"

    def _find_duplicates(self, nodes: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Find duplicate nodes based on similarity threshold."""
        duplicates = []
        hash_groups: Dict[str, List[Dict[str, Any]]] = {}
        themes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Group by hash for fast pre-filtering
        for node in nodes:
            hash_groups.setdefault(node['hash'], []).append(node)

        # Compare within hash groups
        for group in hash_groups.values():
            if len(group) > 1:
                for i, node1 in enumerate(group):
                    for node2 in group[i+1:]:
                        if node1['type'] == node2['type']:
                            similarity = self._calculate_similarity(node1['source'], node2['source'])
                            if similarity >= self.similarity_threshold:
                                duplicates.append((node1, node2))
                                
                                # Track theme
                                theme = self._identify_theme(node1, node2)
                                themes[theme].append({
                                    'description': f"{node1['name']} in {node1['file']} similar to {node2['name']} in {node2['file']}",
                                    'files': [node1['file'], node2['file']],
                                    'type': node1['type']
                                })

        self.results.themes = dict(themes)
        return duplicates

    def _generate_structural_insights(self, duplicates: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[str]:
        """Generate insights about code structure."""
        insights = []
        
        # Analyze patterns
        type_counts = defaultdict(int)
        file_pairs = defaultdict(int)
        
        for node1, node2 in duplicates:
            type_counts[node1['type']] += 1
            file_pairs[(node1['file'], node2['file'])] += 1
        
        # Generate insights
        if type_counts:
            most_common = max(type_counts.items(), key=lambda x: x[1])
            insights.append(f"Most common duplicate type: {most_common[0]} ({most_common[1]} instances)")
        
        if file_pairs:
            most_related = max(file_pairs.items(), key=lambda x: x[1])
            insights.append(f"Most related files: {most_related[0][0]} and {most_related[0][1]} ({most_related[1]} shared patterns)")
        
        return insights

    def _generate_narrative(self, duplicates: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> str:
        """Generate a narrative description of the scan results."""
        if not duplicates:
            return "No code duplication detected in this scan cycle."

        file_counts = {}
        for node1, _ in duplicates:
            file_counts[node1['file']] = file_counts.get(node1['file'], 0) + 1

        top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Generate narrative with themes
        narrative = f"Code duplication analysis detected {len(duplicates)} potential duplicate code blocks "
        narrative += f"across {len(file_counts)} modules. "
        
        if self.results.themes:
            narrative += "\n\nKey themes identified:\n"
            for theme, items in self.results.themes.items():
                narrative += f"- {theme.replace('_', ' ').title()}: {len(items)} instances\n"
        
        if top_files:
            narrative += "\nPrimary areas of concern:\n"
            for file, count in top_files:
                narrative += f"- {file}: {count} duplicate patterns\n"
        
        if self.results.structural_insights:
            narrative += "\nStructural insights:\n"
            for insight in self.results.structural_insights:
                narrative += f"- {insight}\n"
        
        narrative += "\nRecommendation: Consider refactoring these patterns into shared utilities or base classes."
        return narrative

    async def scan_project(self, ignore_patterns: Optional[List[str]] = None) -> ScanResults:
        """Scan the project and generate documentation."""
        ignore_set = set(ignore_patterns) if ignore_patterns else set()
        all_nodes = []
        
        # Collect all nodes from Python files
        for root, _, files in os.walk(self.project_root):
            for file in files:
                file_path = Path(root) / file
                if self._is_python_file(file_path) and not any(pattern in str(file_path) for pattern in ignore_set):
                    all_nodes.extend(self._scan_file(file_path))
        
        self.results.total_files = len(set(node['file'] for node in all_nodes))
        
        # Find duplicates
        duplicates = self._find_duplicates(all_nodes)
        self.results.total_duplicates = len(duplicates)
        
        # Generate structural insights
        self.results.structural_insights = self._generate_structural_insights(duplicates)
        
        # Organize duplicates by category
        for node1, node2 in duplicates:
            category = node1['type'].lower()
            if category not in self.results.duplicates:
                self.results.duplicates[category] = []
            
            similarity_insight = self._calculate_similarity(node1['source'], node2['source'])
            self.results.duplicates[category].append({
                'name': node1['name'],
                'file': node1['file'],
                'line': node1['line'],
                'similar_to': f"{node2['name']} ({node2['file']}:{node2['line']})",
                'insight': similarity_insight
            })
        
        # Generate top violators
        file_counts = {}
        for node1, _ in duplicates:
            file_counts[node1['file']] = file_counts.get(node1['file'], 0) + 1
        
        self.results.top_violators = [
            {"file": file, "count": count}
            for file, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Generate narrative
        self.results.narrative = self._generate_narrative(duplicates)
        
        return self.results

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="DryScanner CLI")
    parser.add_argument("--summary-only", action="store_true", help="Print summary only, omit full report")
    parser.add_argument("--fail-on", type=int, default=None, help="Exit with code 1 if duplicates exceed this number")
    parser.add_argument("--report", choices=["text", "yaml", "json"], default="text", help="Report output format")
    parser.add_argument("--project-root", type=str, default=".", help="Root directory to scan")
    parser.add_argument("--similarity", type=float, default=0.8, help="Similarity threshold (0.0 to 1.0)")
    parser.add_argument("--output", type=str, help="Output file path for the report")

    args = parser.parse_args()
    scanner = Scanner(args.project_root)
    scanner.similarity_threshold = args.similarity
    results = scanner.scan_project()

    # Save report to file if specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            if args.report == "json":
                json.dump(results.summary(), f, indent=2)
            elif args.report == "yaml":
                yaml.dump(results.summary(), f, sort_keys=False)
            else:
                f.write(results.format_summary() if args.summary_only else results.format_full_report())

    # Print to console
    if args.report == "json":
        print(json.dumps(results.summary(), indent=2))
    elif args.report == "yaml":
        print(yaml.dump(results.summary(), sort_keys=False))
    else:
        print(results.format_summary() if args.summary_only else results.format_full_report())

    if args.fail_on is not None and results.count_duplicates() > args.fail_on:
        exit(1)

if __name__ == "__main__":
    main()

__all__ = ["Scanner", "ScanResults"]

