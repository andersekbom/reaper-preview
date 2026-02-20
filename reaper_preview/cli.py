"""CLI entry point for reaper-preview."""

import os
from pathlib import Path

import click

from reaper_preview.discover import discover_projects
from reaper_preview.render import RenderError, render_project
from reaper_preview.rpp_modify import prepare_rpp_for_preview


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
        reaper_bin = "reaper"  # T9 will implement auto-detection
        click.echo("Using 'reaper' from PATH (auto-detection not yet implemented)")

    # Render each project
    click.echo(f"\nRendering {len(projects)} project{'s' if len(projects) != 1 else ''}...\n")
    successful = 0
    failed = 0

    for idx, project in enumerate(projects, start=1):
        click.echo(f"[{idx}/{len(projects)}] {project.name}...")

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

            # Clean up temp RPP
            temp_rpp.unlink()

            click.echo(f"  ✓ Rendered: {output_file.name}")
            successful += 1

        except RenderError as e:
            click.echo(f"  ✗ Failed: {e}", err=True)
            failed += 1
            # Clean up temp RPP on error
            try:
                if temp_rpp and temp_rpp.exists():
                    temp_rpp.unlink()
            except Exception:
                pass
            continue
        except Exception as e:
            click.echo(f"  ✗ Unexpected error: {e}", err=True)
            failed += 1
            continue

    # Summary
    click.echo(f"\nCompleted: {successful} successful, {failed} failed")


if __name__ == "__main__":
    main()
