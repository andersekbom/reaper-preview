"""Invoke Reaper command-line renders."""

import subprocess
from pathlib import Path


class RenderError(Exception):
    """Base exception for rendering errors."""


class RenderTimeoutError(RenderError):
    """Raised when rendering times out."""


def render_project(
    rpp_path: Path,
    output_dir: Path,
    filename: str,
    audio_format: str,
    reaper_bin: str = "reaper",
    timeout: int = 300,
) -> Path:
    """Render a Reaper project to an audio file.

    Invokes `reaper -renderproject` as a subprocess and waits for completion.

    Args:
        rpp_path: Path to the RPP file to render
        output_dir: Directory where the output file will be created
        filename: Base filename for the output (without extension)
        audio_format: 'mp3' or 'wav'
        reaper_bin: Path to the Reaper executable
        timeout: Maximum time to wait in seconds (default: 300)

    Returns:
        Path to the rendered audio file

    Raises:
        RenderTimeoutError: If rendering takes longer than timeout
        RenderError: If rendering fails (non-zero exit) or output file is not created
    """
    cmd = [
        reaper_bin,
        "-nosplash",
        "-noactivate",
        "-renderproject",
        str(rpp_path),
    ]

    try:
        result = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)
    except subprocess.TimeoutExpired as e:
        raise RenderTimeoutError(f"Rendering timed out after {timeout} seconds") from e

    if result.returncode != 0:
        raise RenderError(
            f"Reaper exited with code {result.returncode}. "
            f"stderr: {result.stderr.strip() if result.stderr else '(none)'}"
        )

    # Verify output file was created
    extension = f".{audio_format}"
    expected_output = output_dir / f"{filename}{extension}"
    if not expected_output.exists():
        raise RenderError(
            f"Render completed but output file was not created: {expected_output}"
        )

    return expected_output
