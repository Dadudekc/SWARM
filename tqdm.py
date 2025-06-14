"""Lightweight shim of the `tqdm` progress bar for the test environment."""
from __future__ import annotations

from typing import Iterable, Any, Optional

__all__ = ["tqdm"]


def tqdm(iterable: Optional[Iterable[Any]] = None, *args: Any, **kwargs: Any):  # type: ignore[override]
    """Return the iterable unchanged, emulating tqdm wrapper."""
    return iterable if iterable is not None else [] 