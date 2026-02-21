"""Tests for Reaper binary auto-detection."""

from pathlib import Path
from unittest.mock import patch

from reaper_preview.cli import find_reaper_bin


def _mock_exists(match_path):
    """Return a Path.exists replacement that returns True only for match_path."""
    original_exists = Path.exists

    def exists(self):
        if str(self) == match_path:
            return True
        return False

    return exists


class TestFindReaperBin:
    def test_finds_reaper_via_which(self):
        with patch("shutil.which", return_value="/usr/bin/reaper"):
            result = find_reaper_bin()
        assert result == "/usr/bin/reaper"

    def test_returns_none_when_not_found(self):
        with patch("shutil.which", return_value=None), \
             patch("sys.platform", "linux"), \
             patch.object(Path, "exists", return_value=False):
            result = find_reaper_bin()
        assert result is None

    def test_finds_linux_common_path(self):
        with patch("shutil.which", return_value=None), \
             patch("sys.platform", "linux"), \
             patch.object(Path, "exists", _mock_exists("/opt/REAPER/reaper")):
            result = find_reaper_bin()
        assert result == "/opt/REAPER/reaper"

    def test_finds_macos_app_bundle(self):
        expected = "/Applications/REAPER.app/Contents/MacOS/REAPER"
        with patch("shutil.which", return_value=None), \
             patch("sys.platform", "darwin"), \
             patch.object(Path, "exists", _mock_exists(expected)):
            result = find_reaper_bin()
        assert result == expected

    def test_finds_windows_program_files(self):
        expected = "C:\\Program Files\\REAPER (x64)\\reaper.exe"
        with patch("shutil.which", return_value=None), \
             patch("sys.platform", "win32"), \
             patch.object(Path, "exists", _mock_exists(expected)):
            result = find_reaper_bin()
        assert result == expected

    def test_which_takes_priority_over_common_paths(self):
        with patch("shutil.which", return_value="/usr/local/bin/reaper"), \
             patch("sys.platform", "linux"):
            result = find_reaper_bin()
        assert result == "/usr/local/bin/reaper"
