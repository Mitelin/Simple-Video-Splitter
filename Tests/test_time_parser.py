"""Tests for parsing the user-entered split timestamp."""

from __future__ import annotations

import unittest

from VideoSplitter.Utils.time_parser import parse_time_to_seconds


class TimeParserTests(unittest.TestCase):
    """Verify accepted and rejected HH:MM:SS values."""

    def test_valid_time_is_parsed(self) -> None:
        self.assertEqual(parse_time_to_seconds("01:05:32"), 3932)

    def test_rejects_invalid_format(self) -> None:
        with self.assertRaisesRegex(ValueError, "HH:MM:SS"):
            parse_time_to_seconds("1:05:32")

    def test_rejects_invalid_minutes(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 00 and 59"):
            parse_time_to_seconds("00:99:00")

    def test_rejects_zero(self) -> None:
        with self.assertRaisesRegex(ValueError, "greater than"):
            parse_time_to_seconds("00:00:00")


if __name__ == "__main__":
    unittest.main()
