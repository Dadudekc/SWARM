"""Backup and restore utility for Dream.OS runtime data."""

from __future__ import annotations

import argparse
import io
import json
import tarfile
from datetime import datetime
from pathlib import Path


def add_path(tar: tarfile.TarFile, path: Path, root: Path) -> None:
    """Add a path to the tar archive if it exists.

    Args:
        tar: Open tar file for writing.
        path: Path to file or directory to add.
        root: Root directory to make paths relative.
    """
    if not path.exists():
        return

    tar.add(path, arcname=str(path.relative_to(root)))


def write_metadata(tar: tarfile.TarFile) -> None:
    """Write metadata file to archive."""
    metadata = {"timestamp": datetime.now().isoformat()}
    data = json.dumps(metadata, indent=2).encode("utf-8")
    info = tarfile.TarInfo("metadata.json")
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))


def backup_runtime():
    """Backup runtime directory."""
    runtime = Path("runtime")
    if not runtime.exists():
        return
        
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"runtime_backup_{timestamp}.tar.gz"
    
    with tarfile.open(backup_file, "w:gz") as tar:
        # Backup agent mailboxes
        add_path(tar, Path("agent_tools/mailbox"), runtime)
        
        # Backup other runtime files
        for item in runtime.glob("*"):
            add_path(tar, item, runtime)


def safe_extract(tar: tarfile.TarFile, path: Path) -> None:
    """Safely extract tar archive to path."""
    base = path.resolve()
    for member in tar.getmembers():
        member_path = (path / member.name).resolve()
        if not str(member_path).startswith(str(base)):
            raise RuntimeError("Attempted path traversal in tar file")
    tar.extractall(path)


def restore(runtime: Path, archive: Path) -> None:
    """Restore runtime data from archive."""
    with tarfile.open(archive, "r:gz") as tar:
        safe_extract(tar, runtime)
    print(f"Runtime restored from {archive}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Backup or restore Dream.OS data")
    sub = parser.add_subparsers(dest="command", required=True)

    backup_cmd = sub.add_parser("backup", help="Create backup archive")
    backup_cmd.add_argument("output", type=Path, help="Output tar.gz archive")
    backup_cmd.add_argument("--runtime", type=Path, default=Path("runtime"), help="Runtime directory")

    restore_cmd = sub.add_parser("restore", help="Restore from archive")
    restore_cmd.add_argument("archive", type=Path, help="Backup archive to restore")
    restore_cmd.add_argument("--runtime", type=Path, default=Path("runtime"), help="Runtime directory")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "backup":
        backup_runtime()
    elif args.command == "restore":
        restore(args.runtime, args.archive)


if __name__ == "__main__":
    main()
