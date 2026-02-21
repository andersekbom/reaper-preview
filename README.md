# reaper-preview

Batch-generate short audio previews (MP3/WAV) from Reaper DAW projects.

Scans a directory tree for `.rpp` project files, temporarily modifies their render settings, and invokes Reaper's command-line render to produce short audio snippets. Useful for quickly browsing a large collection of projects without opening each one.

## Requirements

- Python 3.10+
- [Reaper](https://www.reaper.fm/) installed and accessible from the command line

## Installation

```bash
git clone https://github.com/andersekbom/reaper-preview.git
cd reaper-preview
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Generate 30-second MP3 previews for all projects under a directory
reaper-preview --input-dir ~/Music/Reaper/ --output-dir ~/Music/Reaper/previews/

# 60-second WAV previews starting at the 10-second mark
reaper-preview --input-dir ~/Music/Reaper/ --duration 60 --start 10 --format wav

# Dry run — list discovered projects without rendering
reaper-preview --input-dir ~/Music/Reaper/ --dry-run

# Force re-render even if previews already exist
reaper-preview --input-dir ~/Music/Reaper/ --force

# Specify Reaper binary path (auto-detected by default)
reaper-preview --input-dir ~/Music/Reaper/ --reaper-bin /opt/REAPER/reaper
```

## Options

| Option | Default | Description |
|---|---|---|
| `--input-dir` | `.` | Root directory containing Reaper projects |
| `--output-dir` | `./previews` | Directory for rendered preview files |
| `--format` | `mp3` | Output audio format (`mp3` or `wav`) |
| `--duration` | `30` | Preview duration in seconds |
| `--start` | `0` | Start time in seconds |
| `--reaper-bin` | auto-detect | Path to Reaper executable |
| `--dry-run` | | List projects without rendering |
| `--force` | | Re-render even if preview already exists |

## How it works

1. **Discover** — Recursively finds all `.rpp` files under the input directory, skipping backups (`.rpp-bak`, `.rpp-undo`)
2. **Skip** — If a preview already exists and is newer than the `.rpp` file, it is skipped (use `--force` to override)
3. **Modify** — Creates a temporary copy of each `.rpp` with render settings injected (output format, time bounds, output path)
4. **Render** — Invokes `reaper -renderproject` on the temporary file to produce the audio preview
5. **Report** — Shows progress and a summary of successful/skipped/failed renders

## Limitations

- Reaper opens briefly (with GUI) for each render — there is no true headless mode
- Rendering uses whatever plugins/VSTi are in the project; missing plugins may produce silence
- Rendering is sequential — multiple Reaper instances can conflict

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
