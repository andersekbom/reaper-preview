"""Tests for reaper_preview.discover module."""

import pytest
from pathlib import Path

from reaper_preview.discover import ProjectInfo, discover_projects


class TestProjectInfo:
    def test_has_expected_fields(self):
        info = ProjectInfo(name="MySong", rpp_path=Path("/a/MySong.rpp"), project_dir=Path("/a"))
        assert info.name == "MySong"
        assert info.rpp_path == Path("/a/MySong.rpp")
        assert info.project_dir == Path("/a")


class TestDiscoverProjects:
    def test_empty_directory(self, tmp_path):
        result = discover_projects(tmp_path)
        assert result == []

    def test_finds_rpp_files(self, tmp_path):
        (tmp_path / "song.rpp").touch()
        result = discover_projects(tmp_path)
        assert len(result) == 1
        assert result[0].name == "song"
        assert result[0].rpp_path == tmp_path / "song.rpp"
        assert result[0].project_dir == tmp_path

    def test_finds_rpp_in_subdirectories(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "deep.rpp").touch()
        result = discover_projects(tmp_path)
        assert len(result) == 1
        assert result[0].name == "deep"
        assert result[0].rpp_path == sub / "deep.rpp"
        assert result[0].project_dir == sub

    def test_skips_rpp_bak_files(self, tmp_path):
        (tmp_path / "song.rpp").touch()
        (tmp_path / "song.rpp-bak").touch()
        result = discover_projects(tmp_path)
        assert len(result) == 1
        assert result[0].name == "song"

    def test_skips_rpp_undo_files(self, tmp_path):
        (tmp_path / "song.rpp").touch()
        (tmp_path / "song.rpp-undo").touch()
        result = discover_projects(tmp_path)
        assert len(result) == 1
        assert result[0].name == "song"

    def test_skips_non_rpp_files(self, tmp_path):
        (tmp_path / "readme.txt").touch()
        (tmp_path / "notes.md").touch()
        (tmp_path / "song.rpp").touch()
        result = discover_projects(tmp_path)
        assert len(result) == 1

    def test_multiple_projects_in_different_dirs(self, tmp_path):
        dir_a = tmp_path / "project_a"
        dir_b = tmp_path / "project_b"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "track_a.rpp").touch()
        (dir_b / "track_b.rpp").touch()
        result = discover_projects(tmp_path)
        names = {p.name for p in result}
        assert names == {"track_a", "track_b"}
        assert len(result) == 2

    def test_results_sorted_by_name(self, tmp_path):
        (tmp_path / "zebra.rpp").touch()
        (tmp_path / "alpha.rpp").touch()
        result = discover_projects(tmp_path)
        assert result[0].name == "alpha"
        assert result[1].name == "zebra"
