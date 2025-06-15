"""Test migration script."""

import os
import shutil
from pathlib import Path

# Test categories and their source directories
TEST_CATEGORIES = {
    "unit": {
        "core": [
            "tests/core/agents",
            "tests/core/auth",
            "tests/core/bridge",
            "tests/core/messaging",
            "tests/core/utils",
        ],
        "features": [
            "tests/autonomy",
            "tests/social",
            "tests/ui",
        ],
        "tools": [
            "tests/tools/scanner",
            "tests/gpt_router",
        ],
    },
    "integration": {
        "core": [
            "tests/core/handlers",
        ],
        "features": [
            "tests/integration",
        ],
        "tools": [
            "tests/tools",
        ],
    },
    "e2e": {
        "workflows": [
            "tests/smoke",
        ],
        "scenarios": [
            "tests/integration",
        ],
        "performance": [
            "tests/performance",
        ],
    },
}

# Fixture and utility directories
FIXTURE_DIRS = {
    "core": ["tests/fixtures"],
    "features": ["tests/features/fixtures"],
    "tools": ["tests/tools/fixtures"],
}

UTILITY_DIRS = {
    "helpers": ["tests/utils"],
    "mocks": ["tests/utils/mock_discord"],
    "environment": ["tests/utils/test_environment.py"],
}

def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def copy_files(src: Path, dst: Path) -> None:
    """Copy files from source to destination."""
    if not src.exists():
        return

    if src.is_file():
        shutil.copy2(src, dst)
    else:
        for item in src.glob("**/*"):
            if item.is_file():
                rel_path = item.relative_to(src)
                dst_path = dst / rel_path
                ensure_dir(dst_path.parent)
                shutil.copy2(item, dst_path)

def migrate_tests() -> None:
    """Migrate tests to new structure."""
    # Create new directory structure
    for category, subcategories in TEST_CATEGORIES.items():
        for subcategory, src_dirs in subcategories.items():
            dst_dir = Path(f"tests/{category}/{subcategory}")
            ensure_dir(dst_dir)
            
            for src_dir in src_dirs:
                src_path = Path(src_dir)
                if src_path.exists():
                    copy_files(src_path, dst_dir)

    # Migrate fixtures
    for category, src_dirs in FIXTURE_DIRS.items():
        dst_dir = Path(f"tests/fixtures/{category}")
        ensure_dir(dst_dir)
        
        for src_dir in src_dirs:
            src_path = Path(src_dir)
            if src_path.exists():
                copy_files(src_path, dst_dir)

    # Migrate utilities
    for category, src_dirs in UTILITY_DIRS.items():
        dst_dir = Path(f"tests/utils/{category}")
        ensure_dir(dst_dir)
        
        for src_dir in src_dirs:
            src_path = Path(src_dir)
            if src_path.exists():
                copy_files(src_path, dst_dir)

def main() -> None:
    """Main entry point."""
    print("Starting test migration...")
    migrate_tests()
    print("Test migration complete!")

if __name__ == "__main__":
    main() 