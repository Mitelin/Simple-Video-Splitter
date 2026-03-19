"""Tests for FFmpeg command line construction."""

from __future__ import annotations

import unittest

from VideoSplitter.Models.split_request import SplitRequest
from VideoSplitter.Services.ffmpeg_command_builder import FfmpegCommandBuilder


class FfmpegCommandBuilderTests(unittest.TestCase):
    """Verify the legacy multi-output FFmpeg command structure."""

    def test_builds_expected_filter_graph_and_maps(self) -> None:
        request = SplitRequest(
            ffmpeg_path="C:/ffmpeg/bin/ffmpeg.exe",
            input_path="C:/input.avi",
            split_time_text="00:11:11",
            split_seconds=671,
            output_path_1="C:/out1.mkv",
            output_path_2="C:/out2.mkv",
        )

        arguments = FfmpegCommandBuilder().build_arguments(request)
        filter_complex_index = arguments.index("-filter_complex") + 1
        filter_complex = arguments[filter_complex_index]

        self.assertIn("-filter_complex", arguments)
        self.assertIn("[v1o]", arguments)
        self.assertIn("[a1o]", arguments)
        self.assertIn("[v2o]", arguments)
        self.assertIn("[a2o]", arguments)
        self.assertIn("trim=start=0:end=671", filter_complex)
        self.assertIn("atrim=start=671", filter_complex)


if __name__ == "__main__":
    unittest.main()
