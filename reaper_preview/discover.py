"""Discover Reaper project files in a directory tree."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectInfo:
    """Information about a discovered Reaper project."""

    name: str
    rpp_path: Path
    project_dir: Path


def discover_projects(root_dir: Path) -> list[ProjectInfo]:
    """Recursively find .rpp files under root_dir, skipping backups.

    Skips .rpp-bak and .rpp-undo files. Returns results sorted by name.
    """
    projects = []
    for rpp_path in root_dir.rglob("*.rpp"):
        if rpp_path.suffix != ".rpp":
            # rglob("*.rpp") also matches .rpp-bak, .rpp-undo etc.
            continue
        projects.append(
            ProjectInfo(
                name=rpp_path.stem,
                rpp_path=rpp_path,
                project_dir=rpp_path.parent,
            )
        )
    projects.sort(key=lambda p: p.name)
    return projects
