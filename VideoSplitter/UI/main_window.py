"""Main desktop window for configuring and running video split jobs."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk
from tkinterdnd2 import DND_FILES

from VideoSplitter.Models.split_request import SplitRequest
from VideoSplitter.Services.config_service import ConfigService
from VideoSplitter.Services.ffmpeg_runner import FfmpegRunner
from VideoSplitter.Services.ffmpeg_validator import FfmpegValidator
from VideoSplitter.UI.setup_dialog import SetupDialog
from VideoSplitter.UI.validation_helpers import validate_input_file, validate_output_directory, validate_split_time
from VideoSplitter.Utils.path_helpers import build_default_output_paths


class MainWindow:
    """Own the application UI, validation flow, and background job wiring."""

    def __init__(self, root: tk.Tk, config_service: ConfigService, validator: FfmpegValidator, ffmpeg_path: Path) -> None:
        self._root = root
        self._style = ttk.Style()
        self._config_service = config_service
        self._validator = validator
        self._runner = FfmpegRunner()
        self._config = self._config_service.load()
        self._ffmpeg_path = ffmpeg_path

        self._root.title("Simple Video Splitter")
        self._root.minsize(1040, 820)

        self._input_var = tk.StringVar()
        self._split_time_var = tk.StringVar(value="00:11:11")
        self._use_custom_output_var = tk.BooleanVar(value=False)
        self._output_directory_var = tk.StringVar()
        self._status_var = tk.StringVar(value="Ready.")
        self._progress_var = tk.DoubleVar(value=0.0)
        self._progress_text_var = tk.StringVar(value="0%")
        self._preview_output_1_var = tk.StringVar(value="Part 1 will be generated automatically")
        self._preview_output_2_var = tk.StringVar(value="Part 2 will be generated automatically")

        self._input_var.trace_add("write", self._handle_paths_changed)
        self._output_directory_var.trace_add("write", self._handle_paths_changed)

        self._configure_styles()
        self._configure_root()
        self._build_layout()
        self._enable_drag_and_drop()
        self._fit_initial_window_size()
        self._persist_ffmpeg_path(ffmpeg_path)
        self._refresh_output_preview()

    def _configure_styles(self) -> None:
        """Register the custom dark theme styles used by the window."""

        self._style.configure("App.TFrame", background="#1b1f24")
        self._style.configure("Header.TFrame", background="#1b1f24")
        self._style.configure("Card.TFrame", background="#252b33")
        self._style.configure("InnerCard.TFrame", background="#2d343d")
        self._style.configure("HeroTitleLabel.TLabel", background="#1b1f24", foreground="#f3f4f6", font=("Segoe UI Semibold", 28))
        self._style.configure("HeroSubtitleLabel.TLabel", background="#1b1f24", foreground="#98a2ad", font=("Segoe UI", 11))
        self._style.configure("CardTitleLabel.TLabel", background="#252b33", foreground="#f3f4f6", font=("Segoe UI Semibold", 14))
        self._style.configure("CardBodyLabel.TLabel", background="#252b33", foreground="#c8d0d8", font=("Segoe UI", 10))
        self._style.configure("FieldNameLabel.TLabel", background="#252b33", foreground="#e4e7eb", font=("Segoe UI Semibold", 10))
        self._style.configure("Hint.TLabel", background="#252b33", foreground="#8f99a4", font=("Segoe UI", 9))
        self._style.configure("PreviewTagLabel.TLabel", background="#2d343d", foreground="#8fb2a3", font=("Segoe UI Semibold", 10))
        self._style.configure("PreviewPathLabel.TLabel", background="#2d343d", foreground="#edf1f4", font=("Consolas", 9))
        self._style.configure("StatusLabel.TLabel", background="#252b33", foreground="#cbd3db", font=("Segoe UI", 10))
        self._style.configure("ProgressLabel.TLabel", background="#252b33", foreground="#f3f4f6", font=("Segoe UI Semibold", 10))

    def _configure_root(self) -> None:
        """Apply baseline size and background settings to the root window."""

        self._root.geometry("1120x860")
        self._root.minsize(1040, 820)
        self._root.configure(bg="#1b1f24")

    def _fit_initial_window_size(self) -> None:
        """Resize the window so the composed layout fits on first launch."""

        self._root.update_idletasks()

        required_width = max(1180, self._root.winfo_reqwidth() + 40)
        required_height = max(880, self._root.winfo_reqheight() + 40)

        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()

        width = min(required_width, screen_width - 80)
        height = min(required_height, screen_height - 80)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)

        self._root.geometry(f"{width}x{height}+{x}+{y}")
        self._root.minsize(width, height)

    def _enable_drag_and_drop(self) -> None:
        """Enable dropping files anywhere inside the application window."""

        self._register_drop_target(self._root)

    def _register_drop_target(self, widget: tk.Misc) -> None:
        """Recursively register every widget as a drag-and-drop target."""

        try:
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._handle_drop_event)
        except tk.TclError:
            pass

        for child in widget.winfo_children():
            self._register_drop_target(child)

    def _build_layout(self) -> None:
        """Build the full control, preview, log, and progress layout."""

        shell = ttk.Frame(self._root, padding=28, style="App.TFrame")
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(2, weight=1)

        header = ttk.Frame(shell, style="Header.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Simple Video Splitter", style="HeroTitleLabel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Split one source video into two encoded outputs with a clean FFmpeg workflow.",
            style="HeroSubtitleLabel.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Button(header, text="Change FFmpeg", command=self._change_ffmpeg, bootstyle="light-outline").grid(row=0, column=1, rowspan=2, sticky="e")

        content = ttk.Frame(shell, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        controls_card = ttk.Frame(content, padding=22, style="Card.TFrame")
        controls_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        controls_card.columnconfigure(0, weight=1)
        controls_card.columnconfigure(1, weight=1)
        ttk.Label(controls_card, text="Split Settings", style="CardTitleLabel.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(controls_card, text="Choose the source file, set the split timestamp and optionally override the export folder.", style="CardBodyLabel.TLabel", wraplength=360).grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 18))

        ttk.Label(controls_card, text="Input video", style="FieldNameLabel.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Entry(controls_card, textvariable=self._input_var).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 14))
        ttk.Button(controls_card, text="Select file", command=self._select_input, bootstyle="light-outline").grid(row=3, column=2, padx=(12, 0), pady=(8, 14))

        ttk.Label(controls_card, text="Split time", style="FieldNameLabel.TLabel").grid(row=4, column=0, sticky="w")
        ttk.Entry(controls_card, textvariable=self._split_time_var, width=18).grid(row=5, column=0, sticky="w", pady=(8, 8))
        ttk.Label(controls_card, text="Format HH:MM:SS, example: 00:11:11", style="Hint.TLabel").grid(row=6, column=0, columnspan=3, sticky="w")
        ttk.Label(controls_card, text="Enter the exact split point where Part 1 ends and Part 2 begins.", style="Hint.TLabel", wraplength=360).grid(row=7, column=0, columnspan=3, sticky="w", pady=(6, 18))

        options_frame = ttk.Frame(controls_card, style="Card.TFrame")
        options_frame.grid(row=8, column=0, columnspan=3, sticky="ew")
        options_frame.columnconfigure(0, weight=1)
        self._custom_output_check = ttk.Checkbutton(
            options_frame,
            text="Use custom output location",
            variable=self._use_custom_output_var,
            command=self._toggle_output_location,
            bootstyle="success-round-toggle",
        )
        self._custom_output_check.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self._output_location_label = ttk.Label(options_frame, text="Output location", style="FieldNameLabel.TLabel")
        self._output_location_entry = ttk.Entry(options_frame, textvariable=self._output_directory_var)
        self._output_location_button = ttk.Button(options_frame, text="Browse", command=self._select_output_directory, bootstyle="secondary-outline")

        preview_card = ttk.Frame(content, padding=22, style="Card.TFrame")
        preview_card.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        preview_card.columnconfigure(0, weight=1)
        ttk.Label(preview_card, text="Generated Output", style="CardTitleLabel.TLabel").grid(row=0, column=0, sticky="w")

        ttk.Label(
            preview_card,
            text="Output files are generated automatically from the selected source name.",
            style="CardBodyLabel.TLabel",
            wraplength=360,
        ).grid(row=1, column=0, sticky="w", pady=(6, 18))

        self._preview_box_1 = ttk.Frame(preview_card, padding=16, style="InnerCard.TFrame")
        self._preview_box_1.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self._preview_box_1.columnconfigure(0, weight=1)
        ttk.Label(self._preview_box_1, text="Part 1", style="PreviewTagLabel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self._preview_box_1, textvariable=self._preview_output_1_var, style="PreviewPathLabel.TLabel", wraplength=340).grid(row=1, column=0, sticky="w", pady=(8, 0))

        self._preview_box_2 = ttk.Frame(preview_card, padding=16, style="InnerCard.TFrame")
        self._preview_box_2.grid(row=3, column=0, sticky="ew")
        self._preview_box_2.columnconfigure(0, weight=1)
        ttk.Label(self._preview_box_2, text="Part 2", style="PreviewTagLabel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self._preview_box_2, textvariable=self._preview_output_2_var, style="PreviewPathLabel.TLabel", wraplength=340).grid(row=1, column=0, sticky="w", pady=(8, 0))

        log_card = ttk.Frame(shell, padding=22, style="Card.TFrame")
        log_card.grid(row=2, column=0, sticky="nsew", pady=(18, 0))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)
        ttk.Label(log_card, text="Processing Log", style="CardTitleLabel.TLabel").grid(row=0, column=0, sticky="w")

        top_row = ttk.Frame(log_card, style="Card.TFrame")
        top_row.grid(row=1, column=0, sticky="ew", pady=(8, 12))
        top_row.columnconfigure(0, weight=1)
        ttk.Label(top_row, textvariable=self._status_var, style="StatusLabel.TLabel").grid(row=0, column=0, sticky="w")
        self._split_button = ttk.Button(top_row, text="Split Video", command=self._start_split, bootstyle="success")
        self._split_button.grid(row=0, column=1, sticky="e", padx=(20, 0))

        log_surface = ttk.Frame(log_card, style="InnerCard.TFrame", padding=1)
        log_surface.grid(row=2, column=0, sticky="nsew")
        log_surface.columnconfigure(0, weight=1)
        log_surface.rowconfigure(0, weight=1)

        self._log_text = tk.Text(
            log_surface,
            wrap="word",
            height=16,
            state="disabled",
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=14,
            font=("Consolas", 10),
            background="#14181d",
            foreground="#e7edf3",
            insertbackground="#e7edf3",
        )
        self._log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_surface, orient="vertical", command=self._log_text.yview, bootstyle="secondary-round")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._log_text.configure(yscrollcommand=scrollbar.set)

        progress_row = ttk.Frame(log_card, style="Card.TFrame")
        progress_row.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        progress_row.columnconfigure(0, weight=1)
        self._progress_bar = ttk.Progressbar(progress_row, orient="horizontal", mode="determinate", maximum=100, variable=self._progress_var, bootstyle="success-striped")
        self._progress_bar.grid(row=0, column=0, sticky="ew")
        ttk.Label(progress_row, textvariable=self._progress_text_var, style="ProgressLabel.TLabel", width=6).grid(row=0, column=1, padx=(12, 0), sticky="e")

        self._toggle_output_location()

    def _change_ffmpeg(self) -> None:
        """Prompt the user to choose a different FFmpeg executable."""

        dialog = SetupDialog(self._root, self._validator)
        selected = dialog.show()
        if selected is None:
            return

        self._ffmpeg_path = Path(selected)
        self._persist_ffmpeg_path(selected)
        self._status_var.set("FFmpeg path updated.")

    def _select_input(self) -> None:
        """Open a file picker and apply the selected input video."""

        initial_dir = self._config.last_input_directory or str(Path.home())
        selected = filedialog.askopenfilename(parent=self._root, title="Select input video", initialdir=initial_dir)
        if not selected:
            return

        self._apply_selected_input_file(selected, source_label="Input file selected.")

    def _handle_drop_event(self, event: tk.Event) -> str:
        """Handle a drop event emitted by TkinterDnD."""

        paths = list(self._root.tk.splitlist(event.data))
        self._process_dropped_files(paths)
        return "break"

    def _process_dropped_files(self, paths: list[str]) -> None:
        """Validate dropped files and accept exactly one input video."""

        if len(paths) != 1:
            self._status_var.set("Please drop exactly one input file.")
            messagebox.showerror(
                "Too many files",
                "Please drop exactly one video file. Multiple files at once are not supported.",
                parent=self._root,
            )
            return

        selected = paths[0]
        input_error = validate_input_file(selected)
        if input_error:
            self._status_var.set("Dropped file is invalid.")
            messagebox.showerror("Invalid input", input_error, parent=self._root)
            return

        self._apply_selected_input_file(selected, source_label="Input file selected by drag and drop.")

    def _apply_selected_input_file(self, selected: str, source_label: str) -> None:
        """Store the chosen input file and refresh related output defaults."""

        self._input_var.set(selected)
        if not self._use_custom_output_var.get():
            self._output_directory_var.set(str(Path(selected).parent))

        self._config.last_input_directory = str(Path(selected).parent)
        self._config.last_output_directory = str(Path(selected).parent)
        self._config_service.save(self._config)
        self._status_var.set(source_label)

    def _select_output_directory(self) -> None:
        """Open a directory picker for the optional custom output folder."""

        initial_dir = self._config.last_output_directory or str(Path.home())
        selected = filedialog.askdirectory(
            parent=self._root,
            title="Select output location",
            initialdir=initial_dir,
        )
        if not selected:
            return

        self._output_directory_var.set(selected)
        self._config.last_output_directory = selected
        self._config_service.save(self._config)

    def _toggle_output_location(self) -> None:
        """Show or hide custom output controls based on the user's choice."""

        if self._use_custom_output_var.get():
            default_directory = self._output_directory_var.get().strip() or self._config.last_output_directory
            if not default_directory and self._input_var.get().strip():
                default_directory = str(Path(self._input_var.get().strip()).parent)

            self._output_directory_var.set(default_directory)
            self._output_location_label.grid(row=1, column=0, sticky="w", pady=(14, 0))
            self._output_location_entry.grid(row=2, column=0, sticky="ew", pady=(8, 0))
            self._output_location_button.grid(row=2, column=1, padx=(12, 0), pady=(8, 0))
            self._refresh_output_preview()
            return

        self._output_location_label.grid_remove()
        self._output_location_entry.grid_remove()
        self._output_location_button.grid_remove()

        if self._input_var.get().strip():
            self._output_directory_var.set(str(Path(self._input_var.get().strip()).parent))

        self._refresh_output_preview()

    def _start_split(self) -> None:
        """Validate inputs, build the request object, and launch the worker thread."""

        input_error = validate_input_file(self._input_var.get())
        if input_error:
            messagebox.showerror("Invalid input", input_error, parent=self._root)
            return

        split_seconds, time_error = validate_split_time(self._split_time_var.get())
        if time_error:
            messagebox.showerror("Invalid split time", time_error, parent=self._root)
            return

        output_directory = str(Path(self._input_var.get().strip()).parent)
        if self._use_custom_output_var.get():
            output_directory = self._output_directory_var.get().strip()
            output_directory_error = validate_output_directory(output_directory)
            if output_directory_error:
                messagebox.showerror("Invalid output", output_directory_error, parent=self._root)
                return

        output_path_1, output_path_2 = build_default_output_paths(self._input_var.get().strip(), output_directory)

        existing_outputs = [
            path
            for path in (output_path_1, output_path_2)
            if Path(path).exists()
        ]
        if existing_outputs:
            confirmed = messagebox.askyesno(
                "Overwrite existing files",
                "One or more output files already exist and will be overwritten. Do you want to continue?",
                parent=self._root,
            )
            if not confirmed:
                self._status_var.set("Split cancelled.")
                return

        request = SplitRequest(
            ffmpeg_path=str(self._ffmpeg_path),
            input_path=self._input_var.get().strip(),
            split_time_text=self._split_time_var.get().strip(),
            split_seconds=split_seconds or 0,
            output_path_1=output_path_1,
            output_path_2=output_path_2,
        )

        self._split_button.configure(state="disabled")
        self._update_progress(0.0)
        self._status_var.set("Running FFmpeg...")
        self._append_log("Starting split job...")
        self._append_log(f"Output file 1: {output_path_1}")
        self._append_log(f"Output file 2: {output_path_2}")

        worker = threading.Thread(target=self._run_split_job, args=(request,), daemon=True)
        worker.start()

    def _run_split_job(self, request: SplitRequest) -> None:
        """Execute the split in a background thread and marshal updates to Tk."""

        result = self._runner.run(
            request,
            log_callback=lambda message: self._root.after(0, self._append_log, message),
            progress_callback=lambda value: self._root.after(0, self._update_progress, value),
        )
        self._root.after(0, self._handle_split_result, result)

    def _handle_split_result(self, result) -> None:
        """Update the UI after the background FFmpeg job has finished."""

        self._split_button.configure(state="normal")
        if result.success:
            self._update_progress(100.0)
            self._status_var.set("Video was successfully split into two files.")
            self._append_log("Split finished successfully.")
            messagebox.showinfo("Success", "Video was successfully split into two files.", parent=self._root)
            return

        self._status_var.set(result.error_message or "Splitting failed. Check the log for details.")
        self._append_log(result.error_message or "Splitting failed.")
        messagebox.showerror("Split failed", result.error_message or "Splitting failed. Check the log for details.", parent=self._root)

    def _handle_paths_changed(self, *_args: object) -> None:
        """Refresh preview paths whenever input or output-related variables change."""

        self._refresh_output_preview()

    def _refresh_output_preview(self) -> None:
        """Display the output file names that will be generated for the current input."""

        input_path = self._input_var.get().strip()
        if not input_path:
            self._preview_output_1_var.set("Part 1 will be generated automatically")
            self._preview_output_2_var.set("Part 2 will be generated automatically")
            return

        output_directory = ""
        if self._use_custom_output_var.get():
            output_directory = self._output_directory_var.get().strip()

        output_1, output_2 = build_default_output_paths(input_path, output_directory or None)
        self._preview_output_1_var.set(output_1)
        self._preview_output_2_var.set(output_2)

    def _update_progress(self, value: float) -> None:
        """Clamp and display the current job progress percentage."""

        clamped = max(0.0, min(100.0, value))
        self._progress_var.set(clamped)
        self._progress_text_var.set(f"{clamped:.0f}%")

    def _append_log(self, message: str) -> None:
        """Append one line to the read-only log view."""

        self._log_text.configure(state="normal")
        self._log_text.insert("end", f"{message}\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _persist_ffmpeg_path(self, ffmpeg_path: Path) -> None:
        """Save the active FFmpeg path back into persistent configuration."""

        self._config.ffmpeg_path = str(ffmpeg_path)
        self._config_service.save(self._config)
