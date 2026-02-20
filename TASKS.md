# Development Tasks

## Phase 1: Project Setup

- [ ] **T1: Project scaffolding** — Create `pyproject.toml` with project metadata, dependencies (`rpp`, `click`), and a `[project.scripts]` entry point. Create the `reaper_preview/` package directory with `__init__.py`. Verify with `pip install -e .` that the package installs.

- [ ] **T2: Git housekeeping** — Create `.gitignore` (Python defaults, `.rpp` files, `previews/`). Create a minimal `README.md`. Make initial commit.

## Phase 2: Core Modules

- [ ] **T3: Project discovery (`discover.py`)** — Implement `discover_projects(root_dir) -> list[ProjectInfo]` that recursively finds `.rpp` files, skipping `.rpp-bak` and `.rpp-undo`. `ProjectInfo` is a dataclass with `name`, `rpp_path`, and `project_dir`. Write unit tests with a temp directory containing a mix of `.rpp`, `.rpp-bak`, and non-RPP files. Test: all `.rpp` files found, backups excluded, empty dir returns empty list.

- [ ] **T4: RPP render settings modification (`rpp_modify.py`)** — Implement `prepare_rpp_for_preview(rpp_path, output_dir, filename, start, end, format) -> Path` that reads an RPP file, modifies render settings (`RENDER_FILE`, `RENDER_PATTERN`, `RENDER_BOUNDSFLAG`, `RENDER_STARTPOS`, `RENDER_ENDPOS`), and writes to a temp file. Test: create a minimal RPP string, run the function, verify the output file contains the expected settings. Original file must be unmodified.

- [ ] **T5: Extract RENDER_FMT blobs** — Open Reaper, configure render for MP3 (128kbps) and WAV (16-bit 44.1kHz), save test projects, and extract the `RENDER_FMT` base64 values. Store them as constants in `rpp_modify.py`. Test: the constants are non-empty strings; a modified RPP contains the correct blob for the requested format.

- [ ] **T6: Render invocation (`render.py`)** — Implement `render_project(rpp_path, reaper_bin, timeout) -> Path` that calls `reaper -renderproject` as a subprocess, waits for completion, and returns the output audio path. Handle: process timeout, non-zero exit code, missing output file. Write a test that mocks `subprocess.run` and verifies the correct command is constructed. Integration test (manual): render a real project and verify the output file exists and is a valid audio file.

## Phase 3: CLI and Integration

- [ ] **T7: CLI entry point (`cli.py`)** — Implement the CLI using `click` with options: `--input-dir`, `--output-dir`, `--format`, `--duration`, `--start`, `--reaper-bin`, `--dry-run`. Dry-run mode should list discovered projects without rendering. Test: invoke CLI with `--dry-run` on a temp directory with fake `.rpp` files; verify output lists them. Verify `--help` works.

- [ ] **T8: End-to-end pipeline** — Wire everything together: discover → modify → render → report. Add progress output (project N of M). Handle errors per-project (log and continue, don't abort the batch). Test: run with `--dry-run` on a real project directory and verify the output. Manual test: render a real project end-to-end.

## Phase 4: Polish

- [ ] **T9: Reaper binary auto-detection** — Detect the Reaper executable path on Linux (`which reaper`, common install paths), macOS (`/Applications/REAPER.app/...`), and Windows (`Program Files`). Fall back to `--reaper-bin` if auto-detection fails. Test: mock `shutil.which` and platform, verify correct paths returned.

- [ ] **T10: Skip already-rendered previews** — If a preview file exists and is newer than the source `.rpp`, skip rendering. Add a `--force` flag to override. Test: create a fake preview file newer than the RPP, verify it's skipped; with `--force`, verify it's re-rendered.

- [ ] **T11: Documentation and release prep** — Flesh out `README.md` with installation instructions, usage examples, and limitations. Verify `pip install .` from a clean venv works. Tag as v0.1.0.
