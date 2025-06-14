#!/usr/bin/env python3
"""pattern_delete.py

A small CLI utility that recursively deletes files whose *names* match a
provided glob pattern **and** whose *contents* contain a given search string.

Examples
--------
Delete all ``.py`` files underneath the ``./tests`` directory that contain the
string ``pytest.skip``::

    python pattern_delete.py --dir ./tests --include "*.py" --contains "pytest.skip"

Preview which files *would* be deleted (no files are removed)::

    python pattern_delete.py --dir ./tests --include "*.py" --contains "TODO" --dry-run
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
from pathlib import Path
from typing import List, Sequence


def _filename_matches(name: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def _content_matches(content: str, *, literal: str | None, regex: re.Pattern[str] | None) -> bool:
    if regex is not None:
        return bool(regex.search(content))
    if literal is not None:
        return literal in content
    # If neither provided treat as "match everything" (unlikely via CLI).
    return True


def pattern_delete(
    root_dir: str | os.PathLike[str],
    glob_patterns: Sequence[str],
    *,
    contains: str | None = None,
    regex: str | None = None,
    dry_run: bool = False,
) -> None:
    """Recursively traverse *root_dir* deleting files that match criteria.

    Parameters
    ----------
    root_dir
        Directory to search recursively.
    glob_patterns
        One or many Unix shell-style globs matched against *file names*.
    contains
        File must include this *literal* substring to qualify (ignored if *regex* provided).
    regex
        Optional regular expression. If given, its presence in file content triggers deletion.
    dry_run
        If *True*, list the matched files but do **not** delete them.
    """

    if regex and contains:
        raise SystemExit("Use either --contains or --regex (not both)")

    root = Path(root_dir).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"[pattern_delete] Error: directory not found – {root}")

    compiled_re: re.Pattern[str] | None = re.compile(regex, re.MULTILINE | re.DOTALL) if regex else None

    matched_files: List[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if not _filename_matches(path.name, glob_patterns):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue  # unreadable -> skip

        if _content_matches(content, literal=contains, regex=compiled_re):
            matched_files.append(path)

    action = "DRY RUN —" if dry_run else "DELETING"
    print(f"\n[{action}] {len(matched_files)} files matched:")

    for file_path in matched_files:
        if dry_run:
            print(f"  {file_path}")
        else:
            try:
                file_path.unlink()
                print(f"  Deleted {file_path}")
            except Exception as exc:
                print(f"  ⚠️  Failed to delete {file_path}: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete files by filename + content pattern")
    parser.add_argument("--dir", required=True, help="Root directory to search")
    parser.add_argument("--include", action="append", default=["*"], help="Glob pattern for filenames (repeatable)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--contains", help="Only delete files containing this literal text")
    group.add_argument("--regex", help="Delete files whose content matches this REGEX pattern")
    parser.add_argument("--dry-run", action="store_true", help="Preview files without deleting them")
    args = parser.parse_args()

    pattern_delete(
        args.dir,
        args.include,
        contains=args.contains,
        regex=args.regex,
        dry_run=args.dry_run,
    ) 