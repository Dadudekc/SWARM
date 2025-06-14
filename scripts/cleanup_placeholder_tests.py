#!/usr/bin/env python3
"""Remove placeholder tests that only contain global skips or pending markers."""
from __future__ import annotations

import pathlib
import re
from typing import List

# Directories / files we *keep* (active test suites)
KEEP_PATHS = {
    pathlib.Path("tests/core/messaging").resolve(),
    pathlib.Path("tests/core/verification").resolve(),
    pathlib.Path("tests/core/resumer_v2").resolve(),
    pathlib.Path("tests/core/ai/chatgpt_bridge_test.py").resolve(),
    pathlib.Path("tests/core/io/atomic_test.py").resolve(),
}

SKIP_RE = re.compile(r"pytest\.skip\(\"Skipping due to missing core import")
PENDING_TOKEN = "Pending implementation"


def should_delete(file_path: pathlib.Path) -> bool:
    """Return True if *file_path* is a placeholder test file."""

    # Keep if inside one of the preserved directories or is an exact keep-file
    if any(str(file_path).startswith(str(k)) for k in KEEP_PATHS):
        return False

    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False  # If we cannot read it, better not delete it.

    # Heuristic: delete if the file contains the global skip *or* has only
    # pending-implementation markers.
    if SKIP_RE.search(text):
        return True

    if PENDING_TOKEN in text and "@pytest.mark.skip(" in text:
        return True

    return False


def collect_placeholder_tests(base_dir: str = "tests") -> List[pathlib.Path]:
    base = pathlib.Path(base_dir).resolve()
    return [p for p in base.rglob("*.py") if should_delete(p)]


def main() -> None:
    placeholders = collect_placeholder_tests()
    for path in placeholders:
        try:
            path.unlink()
            print(f"Deleted {path}")
        except Exception as exc:
            print(f"ERROR deleting {path}: {exc}")

    print(f"Total deleted: {len(placeholders)} placeholder test files")


if __name__ == "__main__":
    main() 