"""Shared validation helpers used by the desktop UI before processing starts."""

from __future__ import annotations

import os
from pathlib import Path

from VideoSplitter.Utils.time_parser import parse_time_to_seconds


def validate_input_file(input_path: str) -> str:
    """Validate that the user selected an existing input file."""

    if not input_path.strip():
        return "Please select an input video file."

    if not Path(input_path).is_file():
        return "The selected input video does not exist."

    return ""


def validate_output_path(output_path: str, label: str) -> str:
    """Validate that an output file path points to an existing parent folder."""

    if not output_path.strip():
        return f"Please choose {label}."

    parent = Path(output_path).parent
    if not parent.exists():
        return f"The folder for {label} does not exist."

    return ""


def validate_output_directory(output_directory: str) -> str:
    """Validate that a custom output directory exists."""

    if not output_directory.strip():
        return "Please choose an output location."

    if not Path(output_directory).is_dir():
        return "The selected output location does not exist."

    return ""


def validate_distinct_paths(input_path: str, output_path_1: str, output_path_2: str) -> str:
    """Ensure that generated outputs do not collide with each other or the input."""

    normalized_input = os.path.normcase(os.path.abspath(input_path))
    normalized_output_1 = os.path.normcase(os.path.abspath(output_path_1))
    normalized_output_2 = os.path.normcase(os.path.abspath(output_path_2))

    if normalized_output_1 == normalized_output_2:
        return "Output file 1 and output file 2 must be different files."

    if normalized_input == normalized_output_1 or normalized_input == normalized_output_2:
        return "Output files must be different from the input video file."

    return ""


def validate_split_time(split_time_text: str) -> tuple[int | None, str]:
    """Validate and parse the split timestamp entered by the user."""

    try:
        return parse_time_to_seconds(split_time_text), ""
    except ValueError as exc:
        return None, str(exc)
