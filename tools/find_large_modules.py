#!/usr/bin/env python3
"""List repository Python files exceeding a line-count threshold."""

from pathlib import Path
import sys

THRESHOLD = 300


def find_large_modules(start: Path) -> None:
    for path in start.rglob('*.py'):
        try:
            line_count = len(path.read_text().splitlines())
        except Exception:
            continue
        if line_count > THRESHOLD:
            print(f"{path.relative_to(start)} {line_count}")


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    find_large_modules(root)


if __name__ == '__main__':
    main()
