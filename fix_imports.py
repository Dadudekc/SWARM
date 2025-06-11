import os
import re

def fix_imports_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all import statements with backslashes
    import_pattern = r'(from|import)\s+dreamos[\\/][^\n]+'
    imports = re.findall(import_pattern, content)
    
    if not imports:
        return False
    
    # Fix each import statement
    for imp in imports:
        # Convert backslashes to dots
        fixed_imp = imp.replace('\\', '.').replace('/', '.')
        # Remove any double dots that might have been created
        fixed_imp = re.sub(r'\.+', '.', fixed_imp)
        # Replace the original import with the fixed one
        content = content.replace(imp, fixed_imp)
    
    # Write the fixed content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    fixed_count = 0
    for root, _, files in os.walk('tests'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    fixed_count += 1
                    print(f"Fixed imports in: {file_path}")
    
    print(f"\nFixed imports in {fixed_count} files")

if __name__ == '__main__':
    main() 