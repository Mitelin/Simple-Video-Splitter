"""Tests for automatic output file path generation."""

from __future__ import annotations

import unittest
from pathlib import Path

from VideoSplitter.Utils.path_helpers import build_default_output_paths


class PathHelpersTests(unittest.TestCase):
    """Verify generated output names and target directories."""

    def test_builds_outputs_in_input_directory_by_default(self) -> None:
        output_1, output_2 = build_default_output_paths("C:/videos/MyVideo.avi")
        self.assertEqual(Path(output_1), Path("C:/videos/MyVideo - Part 1.mkv"))
        self.assertEqual(Path(output_2), Path("C:/videos/MyVideo - Part 2.mkv"))

    def test_builds_outputs_in_custom_directory(self) -> None:
        output_1, output_2 = build_default_output_paths("C:/videos/MyVideo.avi", "D:/exports")
        self.assertEqual(Path(output_1), Path("D:/exports/MyVideo - Part 1.mkv"))
        self.assertEqual(Path(output_2), Path("D:/exports/MyVideo - Part 2.mkv"))


if __name__ == "__main__":
    unittest.main()