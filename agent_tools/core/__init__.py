"""agent_tools.core – legacy subpackage shim."""
from __future__ import annotations

from types import ModuleType
import sys

from .. import mailbox  # noqa: F401

# Re-export utils
from . import file_utils as _file_utils  # noqa: F401

sys.modules[__name__ + '.utils'] = _file_utils

__all__ = ["utils"] 