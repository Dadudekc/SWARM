"""Utility helpers for the cursor ChatGPT bridge."""

def sanitize_filename(name: str) -> str:
    """Return a filesystem-safe version of *name*."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)

__all__ = ["sanitize_filename"]

