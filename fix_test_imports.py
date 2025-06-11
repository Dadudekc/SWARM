import os
import re
from pathlib import Path
from typing import List, Set, Tuple

def fix_backslash_imports(content: str) -> str:
    """Fix backslash imports by replacing them with dots."""
    # Replace backslashes in import statements with dots
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if 'import' in line and '\\' in line:
            # Replace backslashes with dots in import statements
            fixed_line = line.replace('\\', '.')
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def find_missing_imports(file_path: str) -> Set[str]:
    """Find missing imports in a test file."""
    missing_imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract import statements
        import_pattern = r'from\s+([\w\.]+)\s+import\s+([\w\s,]+)'
        matches = re.finditer(import_pattern, content)
        
        for match in matches:
            module_path = match.group(1)
            imports = match.group(2).split(',')
            
            # Try importing each module
            try:
                __import__(module_path)
            except ImportError:
                missing_imports.add(module_path)
                
    except Exception as e:
        print(f"Error analyzing {file_path}: {str(e)}")
        
    return missing_imports

def process_test_files(directory: str) -> Tuple[int, int]:
    """Process all test files in the directory."""
    fixed_files = 0
    files_with_missing_imports = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Read file content
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Fix backslash imports
                    fixed_content = fix_backslash_imports(content)
                    
                    if fixed_content != content:
                        # Write fixed content back
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        fixed_files += 1
                        print(f"Fixed imports in: {file_path}")
                    
                    # Check for missing imports
                    missing_imports = find_missing_imports(file_path)
                    if missing_imports:
                        files_with_missing_imports += 1
                        print(f"\nMissing imports in {file_path}:")
                        for imp in missing_imports:
                            print(f"  - {imp}")
                            
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    
    return fixed_files, files_with_missing_imports

def main():
    """Main function to process test files."""
    test_dir = "tests"
    
    print("Starting test file processing...")
    fixed_files, files_with_missing_imports = process_test_files(test_dir)
    
    print("\nProcessing complete!")
    print(f"Fixed imports in {fixed_files} files")
    print(f"Found missing imports in {files_with_missing_imports} files")

if __name__ == "__main__":
    main() 