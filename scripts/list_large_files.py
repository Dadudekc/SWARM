from pathlib import Path

THRESHOLD = 300


def find_large_files(root: Path = Path('.'), threshold: int = THRESHOLD):
    """Yield Python files with more than ``threshold`` lines."""
    for path in root.rglob('*.py'):
        # skip files inside virtual environments or caches
        if any(part.startswith('.') for part in path.parts):
            continue
        try:
            lines = sum(1 for _ in open(path, 'r', encoding='utf-8', errors='ignore'))
        except OSError:
            continue
        if lines > threshold:
            yield path, lines


def main():
    for path, lines in sorted(find_large_files(), key=lambda x: -x[1]):
        print(f"{lines:5d} {path}")


if __name__ == '__main__':
    main()
