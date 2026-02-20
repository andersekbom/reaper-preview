# reaper-preview

Batch-generate short audio previews (MP3/WAV) from Reaper DAW projects.

Scans a directory tree for `.rpp` project files, temporarily modifies their render settings, and invokes Reaper's command-line render to produce short audio snippets. Useful for quickly browsing a large collection of projects without opening each one.

## Requirements

- Python 3.10+
- [Reaper](https://www.reaper.fm/) installed and accessible from the command line

## Installation

```bash
git clone <repo-url>
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
```

Run `reaper-preview --help` for all options.
