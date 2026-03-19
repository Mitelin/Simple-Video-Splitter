"""Execute FFmpeg, collect logs, and translate process output into UI progress."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable

from VideoSplitter.Models.split_request import SplitRequest
from VideoSplitter.Models.split_result import SplitResult
from VideoSplitter.Services.ffmpeg_command_builder import FfmpegCommandBuilder
from VideoSplitter.Utils.process_helpers import windows_creation_flags


DURATION_PATTERN = re.compile(r"Duration:\s*(\d{2}:\d{2}:\d{2}(?:\.\d+)?)")
TIME_PATTERN = re.compile(r"time=(\d{2}:\d{2}:\d{2}(?:\.\d+)?)")
FPS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s+fps")
FRAME_PATTERN = re.compile(r"frame=\s*(\d+)")
OUT_TIME_PATTERN = re.compile(r"out_time=(\d{2}:\d{2}:\d{2}(?:\.\d+)?)")

PROGRESS_KEYS = {
    "bitrate",
    "drop_frames",
    "dup_frames",
    "fps",
    "frame",
    "out_time",
    "out_time_ms",
    "out_time_us",
    "progress",
    "speed",
    "stream_0_0_q",
    "stream_0_1_q",
    "total_size",
}


class VideoProbeInfo:
    """Small container for metadata extracted from an FFmpeg probe call."""

    def __init__(self, duration_seconds: float | None, fps: float | None) -> None:
        self.duration_seconds = duration_seconds
        self.fps = fps


class FfmpegRunner:
    """Run the split job and report progress/log output back to the UI."""

    def __init__(self, command_builder: FfmpegCommandBuilder | None = None) -> None:
        self._command_builder = command_builder or FfmpegCommandBuilder()

    def run(
        self,
        request: SplitRequest,
        log_callback: Callable[[str], None] | None = None,
        progress_callback: Callable[[float], None] | None = None,
    ) -> SplitResult:
        """Split the input video into two outputs using two FFmpeg phases."""

        output_lines: list[str] = []
        probe_info = self.probe_video_info(request.ffmpeg_path, request.input_path)
        total_duration = probe_info.duration_seconds

        if total_duration and total_duration > 0:
            first_part_duration = min(float(request.split_seconds), total_duration)
            second_part_duration = max(total_duration - first_part_duration, 0.0)
        else:
            first_part_duration = None
            second_part_duration = None

        if progress_callback is not None:
            progress_callback(0.0)

        # Each part is rendered separately so progress can be mapped across the
        # whole job instead of jumping when FFmpeg finishes the first output.
        phase_1_result = self._run_phase(
            request=request,
            output_index=1,
            phase_duration_seconds=first_part_duration,
            phase_progress_start=0.0,
            phase_progress_span=50.0 if total_duration is None else ((first_part_duration / total_duration) * 100.0 if total_duration > 0 else 50.0),
            log_callback=log_callback,
            progress_callback=progress_callback,
        )
        output_lines.extend(phase_1_result[1])
        if phase_1_result[0] != 0:
            combined_output = "\n".join(output_lines)
            return SplitResult(
                success=False,
                exit_code=phase_1_result[0],
                output_path_1=request.output_path_1,
                output_path_2=request.output_path_2,
                std_output=combined_output,
                std_error=combined_output,
                error_message=self._build_error_message(combined_output),
            )

        second_phase_start = 50.0 if total_duration is None else (phase_1_result[2] if phase_1_result[2] is not None else (first_part_duration / total_duration) * 100.0)
        second_phase_span = 50.0 if total_duration is None else max(0.0, 100.0 - second_phase_start)
        phase_2_result = self._run_phase(
            request=request,
            output_index=2,
            phase_duration_seconds=second_part_duration,
            phase_progress_start=second_phase_start,
            phase_progress_span=second_phase_span,
            log_callback=log_callback,
            progress_callback=progress_callback,
        )
        output_lines.extend(phase_2_result[1])
        combined_output = "\n".join(output_lines)
        if phase_2_result[0] != 0:
            return SplitResult(
                success=False,
                exit_code=phase_2_result[0],
                output_path_1=request.output_path_1,
                output_path_2=request.output_path_2,
                std_output=combined_output,
                std_error=combined_output,
                error_message=self._build_error_message(combined_output),
            )

        if not Path(request.output_path_1).exists() or not Path(request.output_path_2).exists():
            return SplitResult(
                success=False,
                exit_code=phase_2_result[0],
                output_path_1=request.output_path_1,
                output_path_2=request.output_path_2,
                std_output=combined_output,
                std_error=combined_output,
                error_message="FFmpeg finished but one or more output files were not created.",
            )

        if progress_callback is not None:
            progress_callback(100.0)

        return SplitResult(
            success=True,
            exit_code=0,
            output_path_1=request.output_path_1,
            output_path_2=request.output_path_2,
            std_output=combined_output,
            std_error="",
            error_message="",
        )

    def _run_phase(
        self,
        request: SplitRequest,
        output_index: int,
        phase_duration_seconds: float | None,
        phase_progress_start: float,
        phase_progress_span: float,
        log_callback: Callable[[str], None] | None,
        progress_callback: Callable[[float], None] | None,
    ) -> tuple[int, list[str], float | None]:
        """Execute one FFmpeg phase and map its local progress into global progress."""

        arguments = self._command_builder.build_output_arguments(request, output_index)
        output_lines: list[str] = []
        phase_label = f"Starting Part {output_index}..."
        output_lines.append(phase_label)
        if log_callback is not None:
            log_callback(phase_label)

        try:
            process = subprocess.Popen(
                [request.ffmpeg_path, *arguments],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=windows_creation_flags(),
            )
        except OSError as exc:
            message = f"Failed to start FFmpeg: {exc}"
            output_lines.append(message)
            if log_callback is not None:
                log_callback(message)
            return -1, output_lines, None

        # Progress lines are emitted on stdout via -progress pipe:1 and should
        # update the bar without polluting the visible processing log.
        last_phase_progress = phase_progress_start
        assert process.stdout is not None
        for line in process.stdout:
            cleaned = line.rstrip()
            if self._is_progress_line(cleaned):
                if progress_callback is not None:
                    progress_value = self._calculate_phase_progress(
                        text=cleaned,
                        phase_duration_seconds=phase_duration_seconds,
                        phase_progress_start=phase_progress_start,
                        phase_progress_span=phase_progress_span,
                    )
                    if progress_value is not None:
                        last_phase_progress = max(last_phase_progress, progress_value)
                        progress_callback(last_phase_progress)
                continue

            output_lines.append(cleaned)
            if log_callback is not None and cleaned:
                log_callback(cleaned)

        exit_code = process.wait()
        return exit_code, output_lines, last_phase_progress

    def _build_error_message(self, combined_output: str) -> str:
        """Translate FFmpeg output into a short user-facing failure message."""

        normalized = combined_output.lower()
        if "stream specifier ':a'" in normalized or "matches no streams" in normalized:
            return "The selected video does not appear to contain an audio stream. This version requires both video and audio."

        return "Splitting failed. Check the log for details."

    def probe_video_info(self, ffmpeg_path: str, input_path: str) -> VideoProbeInfo:
        """Probe duration and FPS information used for better progress estimates."""

        try:
            completed = subprocess.run(
                [ffmpeg_path, "-i", input_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                creationflags=windows_creation_flags(),
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return VideoProbeInfo(duration_seconds=None, fps=None)

        combined_output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
        return VideoProbeInfo(
            duration_seconds=self._extract_duration_seconds(combined_output),
            fps=self._extract_fps(combined_output),
        )

    def probe_duration_seconds(self, ffmpeg_path: str, input_path: str) -> float | None:
        """Return only the probed source duration in seconds."""

        return self.probe_video_info(ffmpeg_path, input_path).duration_seconds

    def _calculate_progress(self, text: str, probe_info: VideoProbeInfo) -> float | None:
        """Estimate progress from a legacy single-process FFmpeg output stream."""

        if probe_info.duration_seconds:
            progress_seconds = self._extract_progress_seconds(text)
            if progress_seconds is not None:
                return min(100.0, (progress_seconds / probe_info.duration_seconds) * 100.0)

        if probe_info.duration_seconds and probe_info.fps:
            frame_count = self._extract_frame_count(text)
            if frame_count is not None:
                total_frames = probe_info.duration_seconds * probe_info.fps
                if total_frames > 0:
                    return min(100.0, (frame_count / total_frames) * 100.0)

        if probe_info.duration_seconds:
            processed_seconds = self._extract_processed_seconds(text)
            if processed_seconds is not None:
                return min(100.0, (processed_seconds / probe_info.duration_seconds) * 100.0)

        return None

    def _calculate_phase_progress(
        self,
        text: str,
        phase_duration_seconds: float | None,
        phase_progress_start: float,
        phase_progress_span: float,
    ) -> float | None:
        """Map one phase's FFmpeg progress line into the overall 0-100 range."""

        if phase_duration_seconds is not None and phase_duration_seconds > 0:
            progress_seconds = self._extract_progress_seconds(text)
            if progress_seconds is not None:
                phase_ratio = min(1.0, progress_seconds / phase_duration_seconds)
                return phase_progress_start + phase_progress_span * phase_ratio

            frame_count = self._extract_frame_count(text)
            fps_value = self._extract_phase_fps(text)
            if frame_count is not None and fps_value and fps_value > 0:
                estimated_seconds = frame_count / fps_value
                phase_ratio = min(1.0, estimated_seconds / phase_duration_seconds)
                return phase_progress_start + phase_progress_span * phase_ratio

        if text == "progress=end":
            return phase_progress_start + phase_progress_span

        return None

    def _extract_duration_seconds(self, text: str) -> float | None:
        """Extract media duration from FFmpeg probe output."""

        match = DURATION_PATTERN.search(text)
        if match is None:
            return None

        return self._timestamp_to_seconds(match.group(1))

    def _extract_processed_seconds(self, text: str) -> float | None:
        """Extract processed playback time from regular FFmpeg log output."""

        match = TIME_PATTERN.search(text)
        if match is None:
            return None

        return self._timestamp_to_seconds(match.group(1))

    def _extract_progress_seconds(self, text: str) -> float | None:
        """Extract processed time from -progress output lines."""

        match = OUT_TIME_PATTERN.search(text)
        if match is not None:
            return self._timestamp_to_seconds(match.group(1))

        if text.startswith("out_time_us="):
            raw_value = text.partition("=")[2].strip()
            if raw_value.isdigit():
                return int(raw_value) / 1_000_000

        if text.startswith("out_time_ms="):
            raw_value = text.partition("=")[2].strip()
            if raw_value.isdigit():
                return int(raw_value) / 1_000_000

        return None

    def _extract_fps(self, text: str) -> float | None:
        """Extract FPS metadata from FFmpeg probe output."""

        match = FPS_PATTERN.search(text)
        if match is None:
            return None

        return float(match.group(1))

    def _extract_frame_count(self, text: str) -> int | None:
        """Extract the currently processed frame count from FFmpeg output."""

        match = FRAME_PATTERN.search(text)
        if match is None:
            return None

        return int(match.group(1))

    def _extract_phase_fps(self, text: str) -> float | None:
        """Extract instantaneous FPS from progress lines emitted during one phase."""

        if not text.startswith("fps="):
            return None

        raw_value = text.partition("=")[2].strip()
        try:
            return float(raw_value)
        except ValueError:
            return None

    def _is_progress_line(self, text: str) -> bool:
        """Return whether the line belongs to FFmpeg's machine-readable progress output."""

        if "=" not in text:
            return False

        key = text.partition("=")[0].strip()
        return key in PROGRESS_KEYS

    def _timestamp_to_seconds(self, value: str) -> float:
        """Convert an FFmpeg timestamp string into seconds."""

        hours_text, minutes_text, seconds_text = value.split(":")
        return int(hours_text) * 3600 + int(minutes_text) * 60 + float(seconds_text)
