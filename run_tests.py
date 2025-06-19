#!/usr/bin/env python3
"""Convenience wrapper for running tests.

This module calls the enhanced test runner located in ``scripts/run_tests.py``.
It exists so developers can simply execute ``python run_tests.py`` from the
repository root, matching the documentation and AGENTS guidelines.
"""

from scripts.run_tests import main

if __name__ == "__main__":
    main()

