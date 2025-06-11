import os
import importlib
import sys
from pathlib import Path

def try_import(module_path):
    try:
        importlib.import_module(module_path)
        return True
    except ImportError:
        return False

def scan_test_files():
    missing_imports = {}
    syntax_errors = []
    
    for root, _, files in os.walk("tests"):
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Check for backslash imports (syntax error)
                if "\\" in content and "from dreamos" in content:
                    syntax_errors.append(f"{file_path}: Contains backslash in import path")
                
                # Extract all dreamos imports
                import_lines = [line.strip() for line in content.split("\n") 
                              if line.strip().startswith("from dreamos") or 
                                 line.strip().startswith("import dreamos")]
                
                for import_line in import_lines:
                    if "\\" in import_line:
                        continue  # Skip backslash imports as they're already caught
                        
                    # Extract module path
                    if import_line.startswith("from dreamos"):
                        module_path = import_line.split(" import ")[0].replace("from ", "")
                    else:
                        module_path = import_line.split(" import ")[0]
                    
                    if not try_import(module_path):
                        if file_path not in missing_imports:
                            missing_imports[file_path] = []
                        missing_imports[file_path].append(import_line)
                        
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
    
    return missing_imports, syntax_errors

def main():
    print("Scanning test files for missing imports...")
    missing_imports, syntax_errors = scan_test_files()
    
    # Write report
    with open("test_import_report.txt", "w") as f:
        f.write("=== Test Import Analysis Report ===\n\n")
        
        if syntax_errors:
            f.write("=== Syntax Errors (Backslash in Imports) ===\n")
            for error in syntax_errors:
                f.write(f"{error}\n")
            f.write("\n")
        
        if missing_imports:
            f.write("=== Missing Imports ===\n")
            for file_path, imports in missing_imports.items():
                f.write(f"\n{file_path}:\n")
                for imp in imports:
                    f.write(f"  {imp}\n")
        else:
            f.write("No missing imports found!\n")
    
    print(f"\nReport written to test_import_report.txt")
    print(f"Found {len(missing_imports)} files with missing imports")
    print(f"Found {len(syntax_errors)} files with syntax errors")

if __name__ == "__main__":
    main() 