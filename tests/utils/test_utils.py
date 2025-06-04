from pathlib import Path
import shutil

TEST_ROOT = Path(__file__).resolve().parents[1]
TEST_DATA_DIR = TEST_ROOT / "data"
TEST_OUTPUT_DIR = TEST_ROOT / "output"
VOICE_QUEUE_DIR = TEST_ROOT / "voice_queue"
TEST_CONFIG_DIR = TEST_ROOT / "config"
TEST_RUNTIME_DIR = TEST_ROOT / "runtime"
TEST_TEMP_DIR = TEST_ROOT / "temp"


def safe_remove(path: Path) -> bool:
    """Remove a file or directory, ignoring errors."""
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def ensure_test_dirs() -> None:
    """Ensure all common test directories exist."""
    for d in [TEST_DATA_DIR, TEST_OUTPUT_DIR, VOICE_QUEUE_DIR, TEST_CONFIG_DIR,
              TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)
