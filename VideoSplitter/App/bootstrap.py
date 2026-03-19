"""Application startup and themed root window configuration."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

import ttkbootstrap as ttk
from tkinterdnd2 import TkinterDnD
from tkinterdnd2.TkinterDnD import _require

from VideoSplitter.Services.config_service import ConfigService
from VideoSplitter.Services.ffmpeg_locator import FfmpegLocator
from VideoSplitter.Services.ffmpeg_validator import FfmpegValidator
from VideoSplitter.UI.main_window import MainWindow
from VideoSplitter.UI.setup_dialog import SetupDialog


class DnDWindow(TkinterDnD.DnDWrapper, ttk.Window):
    """ttkbootstrap window with TkinterDnD support attached."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.TkdndVersion = _require(self)


def run_app() -> int:
    """Start the desktop application and return the process exit code."""

    root = DnDWindow(themename="darkly")
    root.withdraw()

    config_service = ConfigService()
    validator = FfmpegValidator()
    locator = FfmpegLocator(config_service, validator)

    ffmpeg_path = locator.find_first_valid_path()
    if ffmpeg_path is None:
        dialog = SetupDialog(root, validator)
        ffmpeg_path = dialog.show()
        if ffmpeg_path is None:
            root.destroy()
            return 1
        config = config_service.load()
        config.ffmpeg_path = str(ffmpeg_path)
        config_service.save(config)

    root.deiconify()
    root.title("Simple Video Splitter")
    MainWindow(root, config_service=config_service, validator=validator, ffmpeg_path=Path(ffmpeg_path))
    root.mainloop()
    return 0
