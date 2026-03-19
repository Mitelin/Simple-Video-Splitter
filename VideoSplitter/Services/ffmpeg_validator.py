"""Validation helpers for user-selected FFmpeg executables."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from VideoSplitter.Utils.process_helpers import windows_creation_flags


@dataclass(slots=True)
class FfmpegValidationResult:
    """Result object describing whether an FFmpeg path is usable."""

    is_valid: bool
    message: str = ""


class FfmpegValidator:
    """Verify that a selected executable is a working FFmpeg binary."""

    def validate(self, ffmpeg_path: str | Path) -> FfmpegValidationResult:
        """Validate the provided path and return a user-friendly result."""

        candidate = Path(ffmpeg_path)

        if candidate.name.lower() != "ffmpeg.exe":
            return FfmpegValidationResult(False, "Selected file must be named ffmpeg.exe.")

        if not candidate.is_file():
            return FfmpegValidationResult(False, "Selected ffmpeg.exe does not exist.")

        try:
            completed = subprocess.run(
                [str(candidate), "-version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                creationflags=windows_creation_flags(),
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return FfmpegValidationResult(False, f"Failed to execute FFmpeg: {exc}")

        output = f"{completed.stdout}\n{completed.stderr}".lower()
        if completed.returncode != 0 and "ffmpeg version" not in output:
            return FfmpegValidationResult(False, "The selected executable does not appear to be a working FFmpeg binary.")

        return FfmpegValidationResult(True, "")
