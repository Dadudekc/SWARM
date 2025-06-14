import pytest
import os
from pathlib import Path
import types, sys  # noqa: WPS433
import logging

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["DREAMOS_TEST_MODE"] = "1"
    os.environ["DREAMOS_LOG_LEVEL"] = "DEBUG"
    
    # Create test directories
    test_dirs = [
        "runtime/agent_memory/test_agent",
        "runtime/cache",
        "logs"
    ]
    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # EDIT START: Provide lightweight stub for optional third-party libs absent in CI.
    if "tqdm" not in sys.modules:
        tqdm_stub = types.ModuleType("tqdm")
        def _noop(*args, **kwargs):
            return args[0] if args else None
        tqdm_stub.tqdm = _noop  # type: ignore[attr-defined]
        sys.modules["tqdm"] = tqdm_stub
    # EDIT END
    
    # EDIT START: Provide compatibility shim for legacy TestEnvironment missing `cleanup`.
    try:
        from tests.utils.test_environment import TestEnvironment as _TE  # noqa: WPS433
        if not hasattr(_TE, "cleanup") and hasattr(_TE, "teardown"):
            _TE.cleanup = _TE.teardown  # type: ignore[attr-defined]
    except Exception:
        # Safe to ignore if tests package layout changes.
        pass
    # EDIT END
    
    yield
    
    # Cleanup
    logging.shutdown()

    for dir_path in test_dirs:
        if Path(dir_path).exists():
            for file in Path(dir_path).glob("*"):
                if file.is_file():
                    try:
                        file.unlink()
                    except PermissionError:
                        # Skip files still locked on Windows (e.g., by antivirus)
                        pass 