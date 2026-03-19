"""Helpers for generating default output file locations."""

from __future__ import annotations

from pathlib import Path


def build_default_output_paths(input_path: str, output_directory: str | None = None) -> tuple[str, str]:
    """Build the default Part 1 and Part 2 output paths for an input file."""

    source = Path(input_path)
    base_name = source.stem
    target_directory = Path(output_directory) if output_directory else source.parent
    return (
        str(target_directory / f"{base_name} - Part 1.mkv"),
        str(target_directory / f"{base_name} - Part 2.mkv"),
    )
