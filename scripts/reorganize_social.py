import os
import shutil
from pathlib import Path

def move_directory(src: str, dst: str):
    """Move a directory and its contents."""
    if os.path.exists(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.move(src, dst)

def update_imports(file_path: str):
    """Update imports in a file from dreamos.social to social."""
    if not os.path.exists(file_path):
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace imports
    content = content.replace('from dreamos.social', 'from social')
    content = content.replace('import dreamos.social', 'import social')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    base_dir = Path('D:/SWARM/Dream.OS')
    
    # Directories to move
    dirs_to_move = [
        ('dreamos/social/strategies', 'social/strategies'),
        ('dreamos/social/utils', 'social/utils'),
        ('dreamos/social/core', 'social/core'),
        ('dreamos/social/driver', 'social/driver'),
    ]
    
    # Move directories
    for src, dst in dirs_to_move:
        move_directory(str(base_dir / src), str(base_dir / dst))
    
    # Update imports in all Python files
    for root, _, files in os.walk(str(base_dir / 'social')):
        for file in files:
            if file.endswith('.py'):
                update_imports(os.path.join(root, file))
    
    # Remove dreamos/social directory
    if os.path.exists(str(base_dir / 'dreamos/social')):
        shutil.rmtree(str(base_dir / 'dreamos/social'))

if __name__ == '__main__':
    main() 