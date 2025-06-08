"""
Agent-5 shim layer for legacy Social-utils tests
------------------------------------------------
Maps old `LogConfig` keyword arguments (log_level, max_bytes, backup_count)
to the new signature (level, max_size_mb, max_files).  Automatically injected
via `pytest_configure` so no individual test files need changes.
"""

import inspect
from pathlib import Path

import pytest

import dreamos.social.utils.log_config as lc


def _kwarg_alias(**mapping):  # generic decorator for alias-renaming
    def decorator(func):
        def wrapper(*args, **kwargs):
            for old, new in mapping.items():
                if old in kwargs:
                    kwargs[new] = kwargs.pop(old)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def pytest_configure(config):  # noqa: D401
    """
    At collection-time, monkey-patch `LogConfig.__init__` to accept legacy names.
    The patch is no-op in production runtime; it only affects the test session.
    """

    original_init = lc.LogConfig.__init__

    # If already patched (idempotent), skip
    if getattr(lc.LogConfig.__init__, "__patched_by_agent5__", False):
        return

    @pytest.fixture(scope="session", autouse=True)
    def _ensure_tmp_log_dir(tmp_path_factory):
        """
        Provide a guaranteed log directory for all social-utils tests.
        """

        tmp_dir: Path = tmp_path_factory.mktemp("social_logs")
        lc.DEFAULT_LOG_DIR = tmp_dir  # override module-level default
        yield tmp_dir

    # Build dynamic alias map from legacy → new param names
    alias_map = {
        "log_level": "level",
        "max_bytes": "max_size_mb",
        "backup_count": "max_files",
    }

    # Create wrapper that accepts legacy names
    wrapped_init = _kwarg_alias(**alias_map)(original_init)
    wrapped_init.__patched_by_agent5__ = True

    # Replace
    lc.LogConfig.__init__ = wrapped_init  # type: ignore[assignment]


# ---------- Utility fixtures used across multiple social tests ----------

@pytest.fixture()
def sample_log_entry():
    from dreamos.social.utils.log_entry import LogEntry

    return LogEntry(
        timestamp="2025-06-08T12:00:00Z",
        level="INFO",
        message="Agent-5 synthetic entry",
        metadata={"agent": "agent-xyz"},
    ) 