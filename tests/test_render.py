"""Tests for reaper_preview.render module."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from reaper_preview.render import RenderError, RenderTimeoutError, render_project


class TestRenderProject:
    def test_constructs_correct_command(self, tmp_path):
        rpp_file = tmp_path / "test.rpp"
        rpp_file.write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        expected_output = output_dir / "test.mp3"
        expected_output.write_text("fake audio")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            render_project(
                rpp_path=rpp_file,
                output_dir=output_dir,
                filename="test",
                audio_format="mp3",
                reaper_bin="reaper",
            )

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["reaper", "-nosplash", "-noactivate", "-renderproject", str(rpp_file)]

    def test_returns_output_path_on_success(self, tmp_path):
        rpp_file = tmp_path / "test.rpp"
        rpp_file.write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        expected_output = output_dir / "test.mp3"
        expected_output.write_text("fake audio")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = render_project(
                rpp_path=rpp_file,
                output_dir=output_dir,
                filename="test",
                audio_format="mp3",
                reaper_bin="reaper",
            )

        assert result == expected_output

    def test_raises_on_timeout(self, tmp_path):
        rpp_file = tmp_path / "test.rpp"
        rpp_file.write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("reaper", 60)
            with pytest.raises(RenderTimeoutError, match="timed out"):
                render_project(
                    rpp_path=rpp_file,
                    output_dir=output_dir,
                    filename="test",
                    audio_format="mp3",
                    reaper_bin="reaper",
                    timeout=60,
                )

    def test_raises_on_nonzero_exit(self, tmp_path):
        rpp_file = tmp_path / "test.rpp"
        rpp_file.write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr="Error occurred")
            with pytest.raises(RenderError, match=r"exited with code 1"):
                render_project(
                    rpp_path=rpp_file,
                    output_dir=output_dir,
                    filename="test",
                    audio_format="mp3",
                    reaper_bin="reaper",
                )

    def test_raises_on_missing_output_file(self, tmp_path):
        rpp_file = tmp_path / "test.rpp"
        rpp_file.write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        # Don't create the output file

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            with pytest.raises(RenderError, match="not created"):
                render_project(
                    rpp_path=rpp_file,
                    output_dir=output_dir,
                    filename="test",
                    audio_format="mp3",
                    reaper_bin="reaper",
                )

    def test_uses_custom_timeout(self, tmp_path):
        rpp_file = tmp_path / "test.rpp"
        rpp_file.write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        expected_output = output_dir / "test.wav"
        expected_output.write_text("fake audio")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            render_project(
                rpp_path=rpp_file,
                output_dir=output_dir,
                filename="test",
                audio_format="wav",
                reaper_bin="reaper",
                timeout=120,
            )

        assert mock_run.call_args[1]["timeout"] == 120

    def test_constructs_correct_output_path_for_wav(self, tmp_path):
        rpp_file = tmp_path / "test.rpp"
        rpp_file.write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        expected_output = output_dir / "test.wav"
        expected_output.write_text("fake audio")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = render_project(
                rpp_path=rpp_file,
                output_dir=output_dir,
                filename="test",
                audio_format="wav",
                reaper_bin="reaper",
            )

        assert result == expected_output
        assert result.suffix == ".wav"
