"""CLI entry point for reaper-preview."""

import shutil
import sys
from pathlib import Path

import click

from reaper_preview.discover import discover_projects
from reaper_preview.render import RenderError, render_project
from reaper_preview.rpp_modify import prepare_rpp_for_preview

# Common install locations per platform
_LINUX_PATHS = [
    "/opt/REAPER/reaper",
    "/usr/local/bin/reaper",
]
_MACOS_PATHS = [
    "/Applications/REAPER.app/Contents/MacOS/REAPER",
]
_WINDOWS_PATHS = [
    "C:\\Program Files\\REAPER (x64)\\reaper.exe",
    "C:\\Program Files\\REAPER\\reaper.exe",
]


def find_reaper_bin() -> str | None:
    """Auto-detect the Reaper executable.

    Checks PATH first via shutil.which, then common install locations.
    Returns the path string or None if not found.
    """
    found = shutil.which("reaper")
    if found:
        return found

    if sys.platform == "darwin":
        candidates = _MACOS_PATHS
    elif sys.platform == "win32":
        candidates = _WINDOWS_PATHS
    else:
        candidates = _LINUX_PATHS

    for path in candidates:
        if Path(path).exists():
            return path

    return None


@click.command()
@click.option("--input-dir", type=click.Path(exists=True), default=".", help="Root directory containing Reaper projects.")
@click.option("--output-dir", type=click.Path(), default="./previews", help="Directory for rendered preview files.")
@click.option("--format", "audio_format", type=click.Choice(["mp3", "wav"]), default="mp3", help="Output audio format.")
@click.option("--duration", type=float, default=30.0, help="Preview duration in seconds.")
@click.option("--start", type=float, default=0.0, help="Start time in seconds.")
@click.option("--reaper-bin", type=click.Path(), default=None, help="Path to Reaper executable.")
@click.option("--dry-run", is_flag=True, help="List projects without rendering.")
@click.option("--force", is_flag=True, help="Re-render even if preview already exists.")
def main(input_dir, output_dir, audio_format, duration, start, reaper_bin, dry_run, force):
    """Generate short audio previews from Reaper DAW projects."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Discover projects
    click.echo(f"Scanning for .rpp files in {input_path}...")
    projects = discover_projects(input_path)

    if not projects:
        click.echo("No projects found.")
        return

    click.echo(f"Found {len(projects)} project{'s' if len(projects) != 1 else ''}:")
    for project in projects:
        click.echo(f"  - {project.name} ({project.project_dir})")

    if dry_run:
        click.echo("\nDry run mode - no rendering performed.")
        return

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    click.echo(f"\nOutput directory: {output_path}")

    # Auto-detect Reaper binary if not specified
    if reaper_bin is None:
        reaper_bin = find_reaper_bin()
        if reaper_bin is None:
            click.echo("Error: Could not find Reaper. Use --reaper-bin to specify the path.", err=True)
            raise SystemExit(1)
        click.echo(f"Using Reaper: {reaper_bin}")

    # Render each project
    click.echo(f"\nRendering {len(projects)} project{'s' if len(projects) != 1 else ''}...\n")
    successful = 0
    failed = 0
    skipped = 0

    for idx, project in enumerate(projects, start=1):
        click.echo(f"[{idx}/{len(projects)}] {project.name}...")

        # Check if preview already exists and is up to date
        preview_path = output_path / f"{project.name}.{audio_format}"
        if not force and preview_path.exists():
            if preview_path.stat().st_mtime > project.rpp_path.stat().st_mtime:
                click.echo(f"  Skipping (preview is up to date)")
                skipped += 1
                continue

        temp_rpp = None
        try:
            # Prepare modified RPP
            end_time = start + duration
            temp_rpp = prepare_rpp_for_preview(
                rpp_path=project.rpp_path,
                output_dir=output_path,
                filename=project.name,
                start=start,
                end=end_time,
                audio_format=audio_format,
            )

            # Render
            output_file = render_project(
                rpp_path=temp_rpp,
                output_dir=output_path,
                filename=project.name,
                audio_format=audio_format,
                reaper_bin=reaper_bin,
            )

            click.echo(f"  ✓ Rendered: {output_file.name}")
            successful += 1

        except RenderError as e:
            click.echo(f"  ✗ Failed: {e}", err=True)
            failed += 1
        except Exception as e:
            click.echo(f"  ✗ Unexpected error: {e}", err=True)
            failed += 1
        finally:
            if temp_rpp is not None:
                try:
                    temp_rpp.unlink(missing_ok=True)
                except OSError:
                    pass

    # Summary
    parts = [f"{successful} successful"]
    if skipped:
        parts.append(f"{skipped} skipped")
    if failed:
        parts.append(f"{failed} failed")
    click.echo(f"\nCompleted: {', '.join(parts)}")


if __name__ == "__main__":
    main()
