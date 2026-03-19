"""Platform-specific subprocess helpers."""

from __future__ import annotations

import subprocess


def windows_creation_flags() -> int:
    """Return flags that keep spawned console windows hidden on Windows."""

    return getattr(subprocess, "CREATE_NO_WINDOW", 0)
