"""Discovery logic for finding a valid FFmpeg executable on Windows."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from VideoSplitter.Services.config_service import ConfigService
from VideoSplitter.Services.ffmpeg_validator import FfmpegValidator


class FfmpegLocator:
    """Search persisted, PATH-based, and common install locations for FFmpeg."""

    def __init__(self, config_service: ConfigService, validator: FfmpegValidator) -> None:
        self._config_service = config_service
        self._validator = validator

    def find_first_valid_path(self) -> Path | None:
        """Return the first valid FFmpeg path discovered on the machine."""

        candidates = []

        config = self._config_service.load()
        if config.ffmpeg_path:
            candidates.append(Path(config.ffmpeg_path))

        path_candidate = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if path_candidate:
            candidates.append(Path(path_candidate))

        candidates.extend(self._common_install_locations())

        seen: set[str] = set()
        for candidate in candidates:
            normalized = os.path.normcase(str(candidate))
            if normalized in seen:
                continue
            seen.add(normalized)

            result = self._validator.validate(candidate)
            if result.is_valid:
                return Path(candidate)

        return None

    def _common_install_locations(self) -> list[Path]:
        """Return known Windows install locations used as fallback candidates."""

        return [
            Path("C:/ffmpeg/bin/ffmpeg.exe"),
            Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
            Path("C:/Program Files (x86)/ffmpeg/bin/ffmpeg.exe"),
            Path("C:/ProgramData/chocolatey/bin/ffmpeg.exe"),
        ]
