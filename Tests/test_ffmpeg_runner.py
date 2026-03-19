"""Tests for FFmpeg output parsing and progress calculations."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from VideoSplitter.Services.ffmpeg_runner import FfmpegRunner, VideoProbeInfo
from VideoSplitter.Models.split_request import SplitRequest
from VideoSplitter.Services.ffmpeg_command_builder import FfmpegCommandBuilder


class FfmpegRunnerTests(unittest.TestCase):
    """Verify duration probing and progress extraction logic."""

    def setUp(self) -> None:
        self.runner = FfmpegRunner()

    def test_extracts_duration_seconds_from_ffmpeg_output(self) -> None:
        text = "Duration: 00:11:11.50, start: 0.000000, bitrate: 1200 kb/s"
        self.assertEqual(self.runner._extract_duration_seconds(text), 671.5)

    def test_extracts_processed_seconds_from_progress_line(self) -> None:
        text = "frame=  120 fps=30 q=24.0 size=    1024kB time=00:05:35.25 bitrate=  25.0kbits/s speed=1.0x"
        self.assertEqual(self.runner._extract_processed_seconds(text), 335.25)

    def test_extracts_progress_seconds_from_ffmpeg_progress_line(self) -> None:
        text = "out_time=00:05:35.25"
        self.assertEqual(self.runner._extract_progress_seconds(text), 335.25)

    def test_identifies_ffmpeg_progress_key_lines(self) -> None:
        self.assertTrue(self.runner._is_progress_line("out_time=00:00:12.00"))
        self.assertTrue(self.runner._is_progress_line("progress=continue"))
        self.assertFalse(self.runner._is_progress_line("Input #0, avi, from 'video.avi':"))

    def test_extracts_fps_from_ffmpeg_stream_metadata(self) -> None:
        text = "Stream #0:0: Video: h264, yuv420p, 1280x720, 25 fps, 25 tbr, 25 tbn"
        self.assertEqual(self.runner._extract_fps(text), 25.0)

    def test_uses_frame_count_for_progress_from_start(self) -> None:
        probe_info = VideoProbeInfo(duration_seconds=100.0, fps=25.0)
        progress = self.runner._calculate_progress("frame=1250", probe_info)
        self.assertEqual(progress, 50.0)

    def test_prefers_out_time_progress_when_available(self) -> None:
        probe_info = VideoProbeInfo(duration_seconds=100.0, fps=25.0)
        progress = self.runner._calculate_progress("out_time=00:00:20.00", probe_info)
        self.assertEqual(progress, 20.0)

    def test_calculates_phase_progress_with_out_time(self) -> None:
        progress = self.runner._calculate_phase_progress(
            text="out_time=00:00:10.00",
            phase_duration_seconds=20.0,
            phase_progress_start=0.0,
            phase_progress_span=40.0,
        )
        self.assertEqual(progress, 20.0)

    def test_phase_progress_can_finish_first_half(self) -> None:
        progress = self.runner._calculate_phase_progress(
            text="progress=end",
            phase_duration_seconds=20.0,
            phase_progress_start=0.0,
            phase_progress_span=50.0,
        )
        self.assertEqual(progress, 50.0)

    def test_falls_back_to_time_based_progress_when_fps_missing(self) -> None:
        probe_info = VideoProbeInfo(duration_seconds=200.0, fps=None)
        progress = self.runner._calculate_progress("time=00:00:50.00 bitrate=1000kbits/s", probe_info)
        self.assertEqual(progress, 25.0)

    @patch("VideoSplitter.Services.ffmpeg_runner.subprocess.run")
    def test_probe_duration_uses_ffmpeg_metadata(self, mock_run) -> None:
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = (
            "Duration: 00:01:30.00, start: 0.000000, bitrate: 1200 kb/s\n"
            "Stream #0:0: Video: h264, yuv420p, 1280x720, 25 fps, 25 tbr, 25 tbn"
        )

        duration = self.runner.probe_duration_seconds("C:/ffmpeg/bin/ffmpeg.exe", "C:/input.avi")
        probe_info = self.runner.probe_video_info("C:/ffmpeg/bin/ffmpeg.exe", "C:/input.avi")

        self.assertEqual(duration, 90.0)
        self.assertEqual(probe_info.fps, 25.0)


class FfmpegCommandBuilderOutputTests(unittest.TestCase):
    """Verify argument generation for each sequential output phase."""

    def test_builds_part_1_arguments(self) -> None:
        request = SplitRequest(
            ffmpeg_path="C:/ffmpeg/bin/ffmpeg.exe",
            input_path="C:/input.avi",
            split_time_text="00:11:11",
            split_seconds=671,
            output_path_1="C:/out1.mkv",
            output_path_2="C:/out2.mkv",
        )

        arguments = FfmpegCommandBuilder().build_output_arguments(request, 1)

        self.assertIn("-t", arguments)
        self.assertIn("00:11:11", arguments)
        self.assertIn("0:v:0", arguments)
        self.assertIn("0:a:0", arguments)
        self.assertEqual(arguments[-1], "C:/out1.mkv")

    def test_builds_part_2_arguments(self) -> None:
        request = SplitRequest(
            ffmpeg_path="C:/ffmpeg/bin/ffmpeg.exe",
            input_path="C:/input.avi",
            split_time_text="00:11:11",
            split_seconds=671,
            output_path_1="C:/out1.mkv",
            output_path_2="C:/out2.mkv",
        )

        arguments = FfmpegCommandBuilder().build_output_arguments(request, 2)

        self.assertIn("-ss", arguments)
        self.assertIn("00:11:11", arguments)
        self.assertIn("0:v:0", arguments)
        self.assertIn("0:a:0", arguments)
        self.assertEqual(arguments[-1], "C:/out2.mkv")


if __name__ == "__main__":
    unittest.main()