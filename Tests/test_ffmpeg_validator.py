"""Tests for validating user-selected FFmpeg binaries."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from VideoSplitter.Services.ffmpeg_validator import FfmpegValidator


class FfmpegValidatorTests(unittest.TestCase):
    """Cover common acceptance and rejection cases for FFmpeg paths."""

    def setUp(self) -> None:
        self.validator = FfmpegValidator()

    def test_rejects_wrong_filename(self) -> None:
        result = self.validator.validate("C:/tools/not-ffmpeg.exe")
        self.assertFalse(result.is_valid)

    @patch("VideoSplitter.Services.ffmpeg_validator.subprocess.run")
    def test_accepts_working_binary(self, mock_run) -> None:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "ffmpeg version n7"
        mock_run.return_value.stderr = ""

        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "ffmpeg.exe"
            candidate.write_text("placeholder", encoding="utf-8")
            result = self.validator.validate(candidate)

        self.assertTrue(result.is_valid)


if __name__ == "__main__":
    unittest.main()
