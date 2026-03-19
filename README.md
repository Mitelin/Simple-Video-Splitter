# Simple Video Splitter

Windows desktop application for splitting one input video into two `.mkv` outputs at a user-selected timestamp.

The application does not bundle FFmpeg. It validates and uses an existing user-provided `ffmpeg.exe` installation.

## Features

- Detects `ffmpeg.exe` from saved config, `PATH`, and common Windows install locations
- Falls back to a setup dialog when FFmpeg is not available
- Lets the user browse for an input file and enter split time in `HH:MM:SS`
- Lets the user drag and drop a single input file anywhere onto the app window
- Generates two output files automatically as:
	- `<original name> - Part 1.mkv`
	- `<original name> - Part 2.mkv`
- Uses the input folder by default, with optional custom output folder
- Runs FFmpeg as a direct external process without fragile shell wrapping
- Shows live log output and a progress bar during processing
- Stores FFmpeg path and last used folders in user config

## Dependencies

- `ttkbootstrap` for the desktop theme and modernized widget styling
- `tkinterdnd2` for desktop drag-and-drop file handling

## Requirements

- Windows
- Python 3.14+ recommended
- FFmpeg installed somewhere on the machine, or available as a local `ffmpeg.exe`

## FFmpeg Requirement

This project intentionally does not ship FFmpeg.

On startup the application tries to find `ffmpeg.exe` in this order:

1. previously saved app config
2. `PATH`
3. common Windows install locations
4. manual user selection in the setup dialog

When the user selects a binary manually, the app validates that:

- the filename is exactly `ffmpeg.exe`
- the file exists
- `ffmpeg.exe -version` executes successfully enough to identify a working FFmpeg binary

If FFmpeg is missing, the app offers:

- opening the official FFmpeg website
- browsing for a local `ffmpeg.exe`

## Install

```powershell
"d:/PROGRAMOVANI VYVOJ APLIKACI/Simple Video Splitter/.venv/Scripts/python.exe" -m pip install -r requirements.txt
```

If you use the included virtual environment, install into that environment.

## Run

```powershell
"d:/PROGRAMOVANI VYVOJ APLIKACI/Simple Video Splitter/.venv/Scripts/python.exe" main.py
```

## Usage

1. Start the application
2. If FFmpeg is not already known, select a valid `ffmpeg.exe`
3. Choose an input video with `Select file` or drag one file anywhere into the window
4. Enter split time in `HH:MM:SS`
5. Optionally enable custom output location
6. Click `Split Video`
7. Wait for FFmpeg to finish and review the log/progress section

If the user drops more than one file at once, the application shows an error message and keeps the current selection unchanged.

## Output Naming

For an input file like:

```text
MyVideo.avi
```

the application generates:

```text
MyVideo - Part 1.mkv
MyVideo - Part 2.mkv
```

By default those files are created in the same folder as the input video.

## FFmpeg Processing

The application builds FFmpeg arguments programmatically and starts FFmpeg directly as a process.

It uses the following behavior:

- split video into two branches
- split audio into two branches
- trim the first branch from `0` to the split timestamp
- trim the second branch from the split timestamp to the end
- reset timestamps with `setpts` and `asetpts`
- encode video with `libx264`
- encode audio with `aac`
- save both outputs as `.mkv`

Current encoding settings:

- `-c:v libx264`
- `-crf 16`
- `-preset slow`
- `-c:a aac`
- `-b:a 192k`

## Progress Reporting

The progress bar uses FFmpeg output to estimate progress.

- primary source: encoded `frame=` count compared to input FPS and duration
- fallback source: FFmpeg `time=` output if FPS is unavailable

This gives a much more useful progress estimate than a generic indeterminate spinner.

## Configuration

The app stores user configuration in AppData and currently remembers:

- FFmpeg path
- last input directory
- last output directory

## Tests

```powershell
"d:/PROGRAMOVANI VYVOJ APLIKACI/Simple Video Splitter/.venv/Scripts/python.exe" -m unittest discover -s Tests
```

Covered areas include:

- time parsing
- FFmpeg validation
- FFmpeg command generation
- output path generation
- progress parsing logic

## Project Structure

```text
Simple Video Splitter/
├─ main.py
├─ README.md
├─ requirements.txt
├─ VideoSplitter/
│  ├─ App/
│  ├─ Models/
│  ├─ Services/
│  ├─ UI/
│  └─ Utils/
└─ Tests/
```

## Current Limitations

- v1 assumes the source video contains an audio stream
- split time is validated for format and positivity, but not yet against actual media duration before launch
- outputs are always encoded to `.mkv`; codec customization is not exposed in the UI
- no preview player or timeline UI is included

## Notes

- Unicode paths and Windows paths with spaces are supported because FFmpeg is launched with structured arguments
- existing output files trigger overwrite confirmation before running FFmpeg
- the app is intentionally narrow in scope: one input video, one split point, two output files
