# Reaper Project Preview Generator

## Problem

When you have many Reaper projects in separate folders, it's hard to remember what each project sounds like without opening them individually in Reaper — a slow process. You need a way to quickly generate short audio previews (MP3/WAV snippets) for each project so you can browse through them and decide which ones to revisit.

## Approach: RPP Modification + Command-Line Render

The solution is a Python CLI tool that:

1. **Finds** all `.rpp` project files under a given directory tree
2. **Copies** each `.rpp` to a temporary modified version with render settings injected (output format, time bounds, output path)
3. **Invokes** `reaper -renderproject <modified.rpp>` to render each project to a short audio file
4. **Collects** the rendered previews into a single output directory

### Why this approach

- **No Reaper plugins or ReaScript setup required** — uses Reaper's built-in `-renderproject` command-line flag, which renders and exits
- **No dependency on a running Reaper instance** — unlike `python-reapy` which needs Reaper open with a network control extension
- **RPP files are plain text** — render settings (format, bounds, output path) can be modified programmatically before invoking the render
- **Works on Linux, macOS, and Windows** — just needs Reaper installed

### Limitations

- Reaper still opens briefly (with GUI) for each render, then closes. There is no true headless mode. The `-noactivate` flag can minimize disruption.
- The render uses whatever plugins/VSTi are in the project. If a plugin is missing, the render may produce silence or partial audio on those tracks.
- Rendering many projects is inherently slow (each must be loaded and processed). Parallelization is limited since multiple Reaper instances can conflict.

## Architecture

```
reaper-preview/
├── reaper_preview/
│   ├── __init__.py
│   ├── cli.py            # CLI entry point (argparse or click)
│   ├── discover.py       # Find .rpp files recursively
│   ├── rpp_modify.py     # Parse and modify RPP render settings
│   └── render.py         # Invoke Reaper command-line renders
├── pyproject.toml
└── SPEC.md
```

### Module Responsibilities

#### `discover.py`
- Recursively scan a directory for `.rpp` files
- Skip backup files (`.rpp-bak`, `.rpp-undo`)
- Return a list of `(project_name, rpp_path)` tuples

#### `rpp_modify.py`
- Parse the RPP file using the [`rpp`](https://github.com/Perlence/rpp) Python library (or plain text manipulation as fallback — the format is simple enough)
- Create a modified copy of the RPP with these render settings overridden:
  - `RENDER_FILE` — set to the desired output directory
  - `RENDER_PATTERN` — set to a filename based on the project name
  - `RENDER_FMT` / `RENDER_FORMAT` — set to MP3 (or WAV)
  - `RENDER_BOUNDSFLAG 0` — use custom time bounds
  - `RENDER_STARTPOS` / `RENDER_ENDPOS` — set to the desired time range (e.g., 0 to 30 seconds, or a configurable range)
- Write the modified RPP to a temp file (never modify the original)

#### `render.py`
- Invoke `reaper -renderproject <temp_rpp>` as a subprocess
- Use `-noactivate` and `-nosplash` flags to minimize GUI disruption
- Wait for the process to exit
- Verify the output file was created
- Clean up the temp RPP file
- Provide progress reporting (project N of M)

#### `cli.py`
- Parse command-line arguments:
  - `--input-dir` — root directory containing Reaper projects (default: current directory)
  - `--output-dir` — where to put the preview files (default: `./previews/`)
  - `--format` — `mp3` or `wav` (default: `mp3`)
  - `--duration` — preview duration in seconds (default: `30`)
  - `--start` — start time in seconds (default: `0`)
  - `--reaper-bin` — path to Reaper executable (auto-detected if possible)
  - `--dry-run` — list projects that would be rendered without actually rendering
- Orchestrate the pipeline: discover → modify → render → report

## Key RPP Render Settings

These are the text fields inside the RPP file that control rendering behavior:

| Field | Purpose | Value for previews |
|---|---|---|
| `RENDER_FILE` | Output directory | Absolute path to output dir |
| `RENDER_PATTERN` | Output filename pattern | `"$project-preview"` |
| `RENDER_FMT` | Audio format config (binary/base64) | Format-specific blob for MP3/WAV |
| `RENDER_BOUNDSFLAG` | What time range to render | `0` (custom time bounds) |
| `RENDER_STARTPOS` | Start time in seconds | `0.0` (or user-specified) |
| `RENDER_ENDPOS` | End time in seconds | `30.0` (or user-specified) |

The `RENDER_FMT` value is a base64-encoded binary blob specific to each format. The simplest approach is to:
1. Create a test project in Reaper
2. Set up the desired render settings (e.g., MP3 128kbps)
3. Save the project and extract the `RENDER_FMT` value from the saved `.rpp` file
4. Hardcode that value as a constant for MP3 and WAV presets

## Dependencies

- **Python 3.10+**
- **[rpp](https://pypi.org/project/rpp/)** — Python parser for RPP files (optional; plain text regex manipulation is a viable alternative given the simple structure)
- **Reaper** — installed on the system, accessible via command line

## Usage Example

```bash
# Generate 30-second MP3 previews for all projects under ~/Music/Reaper/
reaper-preview --input-dir ~/Music/Reaper/ --output-dir ~/Music/Reaper/previews/

# Generate 60-second WAV previews starting at the 10-second mark
reaper-preview --input-dir ~/Music/Reaper/ --duration 60 --start 10 --format wav

# Dry run — just list what would be rendered
reaper-preview --input-dir ~/Music/Reaper/ --dry-run
```

## Alternatives Considered

### ReaScript (Lua/Python) running inside Reaper
- Requires Reaper to be open and a script to be loaded
- More control over rendering (can set up time selections, solo/mute tracks)
- More complex setup; less portable as a standalone tool
- Could be a future enhancement for more advanced preview generation

### python-reapy (external Python controlling a running Reaper)
- Requires Reaper running with the `reapy` control extension enabled
- Good for interactive automation but overkill for batch preview generation
- Performance is limited (~30-60 API calls/second over the network bridge)

### Parsing audio files directly from project folders
- Some projects store rendered audio or recorded stems in their folders
- Unreliable — not all projects have useful audio files, and raw stems don't represent the mix
- Could be used as a fast fallback when the full render approach is too slow

## Future Enhancements

- **Smart time selection**: Parse the RPP to find where audio items actually exist and pick a representative section (e.g., the loudest or most dense section) rather than always starting from 0
- **HTML gallery**: Generate an HTML page with embedded audio players for easy browsing
- **Skip already-rendered**: Check if a preview already exists and is newer than the `.rpp` file; skip re-rendering
- **Parallel rendering**: If Reaper supports multiple instances cleanly, render several projects at once
- **Metadata extraction**: Pull project name, track count, last modified date from the RPP and include in the gallery
