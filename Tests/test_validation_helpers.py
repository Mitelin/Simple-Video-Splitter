"""Tests for UI-facing validation helper functions."""

from __future__ import annotations

import tempfile
import unittest

from VideoSplitter.UI.validation_helpers import validate_distinct_paths, validate_output_directory


class ValidationHelpersTests(unittest.TestCase):
    """Verify path and directory validation behavior."""

    def test_rejects_same_output_paths(self) -> None:
        message = validate_distinct_paths("C:/input.avi", "C:/same.mkv", "C:/same.mkv")
        self.assertIn("must be different", message)

    def test_rejects_output_matching_input(self) -> None:
        message = validate_distinct_paths("C:/input.avi", "C:/input.avi", "C:/other.mkv")
        self.assertIn("different from the input", message)

    def test_accepts_distinct_paths(self) -> None:
        message = validate_distinct_paths("C:/input.avi", "C:/part1.mkv", "C:/part2.mkv")
        self.assertEqual(message, "")

    def test_rejects_missing_output_directory(self) -> None:
        message = validate_output_directory("C:/does-not-exist")
        self.assertIn("does not exist", message)

    def test_accepts_existing_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message = validate_output_directory(temp_dir)

        self.assertEqual(message, "")


if __name__ == "__main__":
    unittest.main()