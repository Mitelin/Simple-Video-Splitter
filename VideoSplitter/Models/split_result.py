"""Output model describing the result of a split operation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SplitResult:
    """Structured result returned after the FFmpeg job finishes or fails."""

    success: bool
    exit_code: int
    output_path_1: str
    output_path_2: str
    std_output: str = ""
    std_error: str = ""
    error_message: str = ""
