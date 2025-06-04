"""Tests for the social module's logging manager."""

import os
import logging
from pathlib import Path

import pytest

from social.utils.log_manager import LogManager, LogConfig


def reset_log_manager():
    LogManager._instance = None


@pytest.fixture(autouse=True)
def cleanup():
    reset_log_manager()
    yield
    logging.shutdown()
    reset_log_manager()


def test_log_rotation(tmp_path):
    config = LogConfig(
        log_dir=str(tmp_path),
        max_bytes=200,
        backup_count=1,
        platforms={"system": "system.log"},
    )
    manager = LogManager(config)

    # Write enough data to ensure file is created
    for _ in range(25):
        manager.info("system", "x" * 10)

    rotated = manager.rotate("system")
    assert rotated is not None
    rotated_path = Path(rotated)
    assert rotated_path.exists()
    assert rotated_path.name != "system.log"
