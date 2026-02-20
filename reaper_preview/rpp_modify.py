"""Parse and modify RPP render settings for preview generation.

Uses plain text manipulation rather than the rpp library, which can't
reliably parse all real-world RPP files.
"""

import re
import tempfile
from pathlib import Path


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


def prepare_rpp_for_preview(
    rpp_path: Path,
    output_dir: Path,
    filename: str,
    start: float,
    end: float,
) -> Path:
    """Create a modified copy of an RPP file with render settings for preview.

    Sets the output directory, filename pattern, and time bounds.
    The original file is never modified.

    Returns the path to the temporary modified RPP file.
    """
    text = rpp_path.read_text()

    text = _replace_or_insert(text, "RENDER_FILE", f'  RENDER_FILE "{output_dir}"')
    text = _replace_or_insert(text, "RENDER_PATTERN", f'  RENDER_PATTERN "{filename}"')
    text = _replace_or_insert(text, "RENDER_RANGE", f"  RENDER_RANGE 0 {start} {end} 18 1000")

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".rpp", delete=False, prefix="reaper_preview_"
    )
    tmp.write(text)
    tmp.close()
    return Path(tmp.name)
