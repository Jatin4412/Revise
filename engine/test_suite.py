"""Single entry point for the complete Revise engine test suite."""

from __future__ import annotations

import sys
import unittest


def main() -> int:
    """Run every engine test module using package-aware discovery."""
    suite = unittest.defaultTestLoader.discover(
        start_dir="engine",
        pattern="test*.py",
        top_level_dir=".",
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
