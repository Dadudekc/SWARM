"""
DRY (Don't Repeat Yourself) Analysis Scanner for Dream.OS

This script analyzes the codebase for:
1. Duplicate functions and classes
2. Redundant test code
3. Repeated imports and structures
4. Opportunities for code consolidation
"""

import ast
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
import yaml
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class CodeLocation:
    """Represents a location of code in the codebase."""
    file_path: Path
    name: str
    line_number: int
    source: str

@dataclass
class DuplicateGroup:
    """Represents a group of duplicate code elements."""
    locations: List[CodeLocation]
    hash_sig: str
    element_type: str  # 'function', 'class', 'test', etc.

class CodeHasher:
    """Handles code normalization and hashing for duplicate detection."""
    
    def __init__(self):
        self.normalizer = CodeNormalizer()
    
    def hash_code(self, code: str) -> str:
        """Hash normalized code to identify duplicates."""
        normalized = self.normalizer.normalize(code)
        return hashlib.md5(normalized.encode()).hexdigest()

class CodeNormalizer:
    """Normalizes code for comparison by removing whitespace and comments."""
    
    def normalize(self, code: str) -> str:
        """Normalize code by removing whitespace and comments."""
        # Remove comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        
        # Remove docstrings
        code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
        
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        code = code.strip()
        
        return code

class ASTAnalyzer:
    """Analyzes Python AST for code patterns and duplicates."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.hasher = CodeHasher()
        self.duplicates: Dict[str, DuplicateGroup] = {}
    
    def analyze_file(self, file_path: Path) -> List[Tuple[str, CodeLocation]]:
        """Analyze a single file for code elements."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            results = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    # Get the source code for this node
                    node_source = ast.unparse(node)
                    hash_sig = self.hasher.hash_code(node_source)
                    
                    location = CodeLocation(
                        file_path=file_path,
                        name=node.name,
                        line_number=node.lineno,
                        source=node_source
                    )
                    
                    results.append((hash_sig, location))
            
            return results
        
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {str(e)}")
            return []
    
    def collect_definitions(self) -> Dict[str, DuplicateGroup]:
        """Collect all code definitions across the codebase."""
        all_results: Dict[str, List[CodeLocation]] = {}
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor() as executor:
            futures = []
            for file_path in self.root_dir.rglob("*.py"):
                futures.append(executor.submit(self.analyze_file, file_path))
            
            for future in futures:
                for hash_sig, location in future.result():
                    all_results.setdefault(hash_sig, []).append(location)
        
        # Convert to DuplicateGroup objects
        for hash_sig, locations in all_results.items():
            if len(locations) > 1:  # Only keep duplicates
                self.duplicates[hash_sig] = DuplicateGroup(
                    locations=locations,
                    hash_sig=hash_sig,
                    element_type='function' if 'def ' in locations[0].source else 'class'
                )
        
        return self.duplicates

class TestAnalyzer:
    """Analyzes test files for patterns and duplicates."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.hasher = CodeHasher()
        self.test_duplicates: Dict[str, DuplicateGroup] = {}
    
    def analyze_test_file(self, file_path: Path) -> List[Tuple[str, CodeLocation]]:
        """Analyze a single test file for patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            results = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    # Get the source code for this test
                    node_source = ast.unparse(node)
                    hash_sig = self.hasher.hash_code(node_source)
                    
                    location = CodeLocation(
                        file_path=file_path,
                        name=node.name,
                        line_number=node.lineno,
                        source=node_source
                    )
                    
                    results.append((hash_sig, location))
            
            return results
        
        except Exception as e:
            logger.warning(f"Error analyzing test file {file_path}: {str(e)}")
            return []
    
    def collect_test_patterns(self) -> Dict[str, DuplicateGroup]:
        """Collect all test patterns across the codebase."""
        all_results: Dict[str, List[CodeLocation]] = {}
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor() as executor:
            futures = []
            for file_path in self.root_dir.rglob("test_*.py"):
                futures.append(executor.submit(self.analyze_test_file, file_path))
            
            for future in futures:
                for hash_sig, location in future.result():
                    all_results.setdefault(hash_sig, []).append(location)
        
        # Convert to DuplicateGroup objects
        for hash_sig, locations in all_results.items():
            if len(locations) > 1:  # Only keep duplicates
                self.test_duplicates[hash_sig] = DuplicateGroup(
                    locations=locations,
                    hash_sig=hash_sig,
                    element_type='test'
                )
        
        return self.test_duplicates

def generate_report(duplicates: Dict[str, DuplicateGroup], 
                   test_duplicates: Dict[str, DuplicateGroup]) -> dict:
    """Generate a YAML report of findings."""
    report = {
        'dry_analysis': {
            'duplicate_functions': [],
            'duplicate_classes': [],
            'duplicate_tests': [],
            'suggestions': []
        }
    }
    
    # Process regular code duplicates
    for group in duplicates.values():
        if group.element_type == 'function':
            report['dry_analysis']['duplicate_functions'].append({
                'name': group.locations[0].name,
                'count': len(group.locations),
                'files': [str(loc.file_path) for loc in group.locations],
                'suggestion': f"Consider extracting to a shared utility module"
            })
        elif group.element_type == 'class':
            report['dry_analysis']['duplicate_classes'].append({
                'name': group.locations[0].name,
                'count': len(group.locations),
                'files': [str(loc.file_path) for loc in group.locations],
                'suggestion': f"Consider creating a base class in a shared module"
            })
    
    # Process test duplicates
    for group in test_duplicates.values():
        report['dry_analysis']['duplicate_tests'].append({
            'name': group.locations[0].name,
            'count': len(group.locations),
            'files': [str(loc.file_path) for loc in group.locations],
            'suggestion': "Consider using @pytest.mark.parametrize or shared test fixtures"
        })
    
    # Generate suggestions
    if report['dry_analysis']['duplicate_functions']:
        report['dry_analysis']['suggestions'].append(
            "Create utility modules for common functions"
        )
    if report['dry_analysis']['duplicate_classes']:
        report['dry_analysis']['suggestions'].append(
            "Create base classes for common patterns"
        )
    if report['dry_analysis']['duplicate_tests']:
        report['dry_analysis']['suggestions'].append(
            "Create shared test fixtures and utilities"
        )
    
    return report

def main():
    """Main entry point for the DRY scanner."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Analyze regular code
    logger.info("Analyzing regular code...")
    analyzer = ASTAnalyzer(project_root)
    duplicates = analyzer.collect_definitions()
    
    # Analyze test code
    logger.info("Analyzing test code...")
    test_analyzer = TestAnalyzer(project_root)
    test_duplicates = test_analyzer.collect_test_patterns()
    
    # Generate report
    logger.info("Generating report...")
    report = generate_report(duplicates, test_duplicates)
    
    # Save report
    output_file = project_root / 'dry_analysis_report.yaml'
    with open(output_file, 'w') as f:
        yaml.dump(report, f, default_flow_style=False)
    
    logger.info(f"Report saved to {output_file}")
    
    # Print summary
    print("\nDRY Analysis Summary:")
    print(f"Found {len(duplicates)} duplicate code elements")
    print(f"Found {len(test_duplicates)} duplicate test patterns")
    print(f"\nSee {output_file} for detailed report")

if __name__ == '__main__':
    main() 
