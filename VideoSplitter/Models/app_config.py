"""Configuration models persisted between application launches."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppConfig:
    """User preferences and last-used paths stored in the config file."""

    ffmpeg_path: str = ""
    last_input_directory: str = ""
    last_output_directory: str = ""
