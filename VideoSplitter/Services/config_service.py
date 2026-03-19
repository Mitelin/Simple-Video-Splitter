"""Persistence helpers for the user configuration file."""

from __future__ import annotations

import json
import os
from pathlib import Path

from VideoSplitter.Models.app_config import AppConfig


class ConfigService:
    """Load and save application settings in the user's AppData folder."""

    def __init__(self) -> None:
        app_data_root = Path(os.getenv("APPDATA", Path.home()))
        self._config_path = app_data_root / "SimpleVideoSplitter" / "config.json"

    @property
    def config_path(self) -> Path:
        """Return the resolved path to the JSON configuration file."""

        return self._config_path

    def load(self) -> AppConfig:
        """Read the stored configuration or return defaults if unavailable."""

        if not self._config_path.exists():
            return AppConfig()

        try:
            payload = json.loads(self._config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AppConfig()

        return AppConfig(
            ffmpeg_path=str(payload.get("ffmpeg_path", "")),
            last_input_directory=str(payload.get("last_input_directory", "")),
            last_output_directory=str(payload.get("last_output_directory", "")),
        )

    def save(self, config: AppConfig) -> None:
        """Persist the provided configuration to disk as JSON."""

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ffmpeg_path": config.ffmpeg_path,
            "last_input_directory": config.last_input_directory,
            "last_output_directory": config.last_output_directory,
        }
        self._config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
