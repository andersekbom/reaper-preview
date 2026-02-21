"""Parse and modify RPP render settings for preview generation.

Uses plain text manipulation rather than the rpp library, which can't
reliably parse all real-world RPP files.
"""

import re
import tempfile
from pathlib import Path

# Base64-encoded RENDER_CFG blobs. The first 4 bytes are a reversed FourCC:
#   evaw = WAV, l3pm = MP3 (LAME).
# Using the simple 4-byte FourCC gives Reaper's default settings for that format.
RENDER_CFG_WAV = "ZXZhdw=="  # b'evaw'
RENDER_CFG_MP3 = "bDNwbQ=="  # b'l3pm'

_RENDER_CFG_BY_FORMAT = {
    "wav": RENDER_CFG_WAV,
    "mp3": RENDER_CFG_MP3,
}


def _replace_or_insert(text: str, key: str, new_line: str) -> str:
    """Replace an existing top-level RPP setting or insert it if missing.

    Matches lines like '  RENDER_FILE "something"' at the top level (two-space indent).
    """
    pattern = rf"^(  ){re.escape(key)}\b.*$"
    replaced, count = re.subn(pattern, new_line, text, count=1, flags=re.MULTILINE)
    if count > 0:
        return replaced
    # Insert before the closing '>' of the root element
    return replaced.replace("\n>", f"\n{new_line}\n>", 1)


def _replace_or_insert_block(text: str, tag: str, block: str) -> str:
    """Replace an existing RPP block (e.g. <RENDER_CFG ...>) or insert it."""
    pattern = rf"^  <{re.escape(tag)}\n.*?\n  >$"
    replaced, count = re.subn(pattern, block, text, count=1, flags=re.MULTILINE | re.DOTALL)
    if count > 0:
        return replaced
    return replaced.replace("\n>", f"\n{block}\n>", 1)


def prepare_rpp_for_preview(
    rpp_path: Path,
    output_dir: Path,
    filename: str,
    start: float,
    end: float,
    audio_format: str = "mp3",
) -> Path:
    """Create a modified copy of an RPP file with render settings for preview.

    Sets the output directory, filename pattern, time bounds, and audio format.
    The original file is never modified.

    Returns the path to the temporary modified RPP file.
    """
    text = rpp_path.read_text()

    # RPP files use forward slashes for paths, even on Windows
    output_dir_str = str(output_dir).replace("\\", "/")
    text = _replace_or_insert(text, "RENDER_FILE", f'  RENDER_FILE "{output_dir_str}"')
    text = _replace_or_insert(text, "RENDER_PATTERN", f'  RENDER_PATTERN "{filename}"')
    text = _replace_or_insert(text, "RENDER_RANGE", f"  RENDER_RANGE 0 {start} {end} 18 1000")

    cfg_blob = _RENDER_CFG_BY_FORMAT[audio_format]
    cfg_block = f"  <RENDER_CFG\n    {cfg_blob}\n  >"
    text = _replace_or_insert_block(text, "RENDER_CFG", cfg_block)

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".rpp", delete=False, prefix="reaper_preview_"
    )
    tmp.write(text)
    tmp.close()
    return Path(tmp.name)
