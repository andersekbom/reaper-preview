"""CLI entry point for reaper-preview."""

from pathlib import Path

import click

from reaper_preview.discover import discover_projects


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

    # Actual rendering will be implemented in T8
    click.echo("\nRendering not yet implemented (T8).")


if __name__ == "__main__":
    main()
