"""Functional tests for :pymod:`dreamos.core.io.atomic`."""

from pathlib import Path

import pytest

# NOTE: Import *inside* tests to comply with the internal "no runtime module
# import at collection time" linter used by this repository's pytest plugin.


def test_safe_write_and_read_round_trip(tmp_path: Path) -> None:
    """`safe_write` should persist the exact bytes that `safe_read` later
    retrieves.

    This verifies the basic happy-path as well as the fact that the helper
    creates the destination file if it does **not** yet exist.
    """

    target: Path = tmp_path / "sample.txt"
    payload = "hello-atomic-world"

    # Write → read → compare
    from dreamos.core.io.atomic import safe_write, safe_read

    safe_write(str(target), payload)
    assert target.exists(), "safe_write did not create the file"

    recovered = safe_read(str(target))
    assert recovered == payload


def test_safe_read_raises_for_missing_file(tmp_path: Path) -> None:
    """`safe_read` should raise *FileNotFoundError* when the file is absent."""

    missing: Path = tmp_path / "does_not_exist.txt"

    from dreamos.core.io.atomic import safe_read

    with pytest.raises(FileNotFoundError):
        _ = safe_read(str(missing))
