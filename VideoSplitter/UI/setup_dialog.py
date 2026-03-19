"""Dialog shown when the application needs the user to locate FFmpeg."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk

from VideoSplitter.Services.ffmpeg_validator import FfmpegValidator


class SetupDialog(tk.Toplevel):
    """Modal dialog for selecting a valid FFmpeg executable."""

    def __init__(self, parent: tk.Misc, validator: FfmpegValidator) -> None:
        super().__init__(parent)
        self._style = ttk.Style()
        self._validator = validator
        self._selected_path: Path | None = None

        self.title("FFmpeg required")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._exit)
        self.geometry("600x300")
        self.configure(bg="#1b1f24")

        self._style.configure("DialogShell.TFrame", background="#1b1f24")
        self._style.configure("DialogCard.TFrame", background="#252b33")
        self._style.configure("DialogInner.TFrame", background="#2d343d")
        self._style.configure("DialogTitle.TLabel", background="#1b1f24", foreground="#f3f4f6", font=("Segoe UI Semibold", 24))
        self._style.configure("DialogText.TLabel", background="#1b1f24", foreground="#9ba4ae", font=("Segoe UI", 10))
        self._style.configure("DialogCardTitle.TLabel", background="#2d343d", foreground="#8fb2a3", font=("Segoe UI Semibold", 10))
        self._style.configure("DialogCardText.TLabel", background="#2d343d", foreground="#e3e9ee", font=("Segoe UI", 10))

        container = ttk.Frame(self, padding=24, style="DialogShell.TFrame")
        container.grid(sticky="nsew")
        container.columnconfigure(0, weight=1)

        ttk.Label(container, text="FFmpeg required", style="DialogTitle.TLabel").grid(row=0, column=0, sticky="w")

        ttk.Label(
            container,
            text=(
                "This application requires FFmpeg to process video files. "
                "FFmpeg is not bundled with this app. Please choose an existing ffmpeg.exe "
                "or open the official FFmpeg website."
            ),
            wraplength=420,
            justify="left",
            style="DialogText.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(10, 18))

        note = ttk.Frame(container, padding=16, style="DialogInner.TFrame")
        note.grid(row=2, column=0, sticky="ew")
        note.columnconfigure(0, weight=1)
        ttk.Label(note, text="What you need", style="DialogCardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(note, text="Select an existing ffmpeg.exe installation or open the official FFmpeg download page.", wraplength=500, style="DialogCardText.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))

        actions = ttk.Frame(container, style="DialogShell.TFrame")
        actions.grid(row=3, column=0, sticky="e", pady=(18, 0))
        ttk.Button(actions, text="Open FFmpeg website", command=self._open_website, bootstyle="secondary-outline").grid(row=0, column=0, padx=(0, 8))
        ttk.Button(actions, text="Browse for ffmpeg.exe", command=self._browse, bootstyle="success").grid(row=0, column=1, padx=(0, 8))
        ttk.Button(actions, text="Exit", command=self._exit, bootstyle="dark-outline").grid(row=0, column=2)

    def show(self) -> Path | None:
        """Display the dialog modally and return the selected FFmpeg path."""

        self.wait_window(self)
        return self._selected_path

    def _open_website(self) -> None:
        """Open the official FFmpeg download page in the default browser."""

        webbrowser.open("https://ffmpeg.org/download.html")

    def _browse(self) -> None:
        """Let the user browse for ffmpeg.exe and validate the selection."""

        selected = filedialog.askopenfilename(
            parent=self,
            title="Select ffmpeg.exe",
            filetypes=[("FFmpeg executable", "ffmpeg.exe"), ("Executable files", "*.exe")],
        )
        if not selected:
            return

        result = self._validator.validate(selected)
        if not result.is_valid:
            messagebox.showerror("Invalid FFmpeg", result.message, parent=self)
            return

        self._selected_path = Path(selected)
        self.destroy()

    def _exit(self) -> None:
        """Close the dialog without selecting FFmpeg."""

        self._selected_path = None
        self.destroy()
