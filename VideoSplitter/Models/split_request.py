"""Input model describing one split operation requested by the user."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SplitRequest:
    """All FFmpeg inputs and encoding options needed to process one job."""

    ffmpeg_path: str
    input_path: str
    split_time_text: str
    split_seconds: int
    output_path_1: str
    output_path_2: str
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = 16
    preset: str = "slow"
    audio_bitrate: str = "192k"
