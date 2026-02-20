"""Tests for reaper_preview.cli module."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from reaper_preview.cli import main
from reaper_preview.render import RenderError


class TestCLI:
    def test_help_option(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Generate short audio previews" in result.output
        assert "--input-dir" in result.output
        assert "--output-dir" in result.output
        assert "--format" in result.output
        assert "--dry-run" in result.output

    def test_dry_run_lists_projects(self, tmp_path):
        # Create test RPP files
        (tmp_path / "song1.rpp").write_text("<REAPER_PROJECT>")
        (tmp_path / "song2.rpp").write_text("<REAPER_PROJECT>")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "song3.rpp").write_text("<REAPER_PROJECT>")

        runner = CliRunner()
        result = runner.invoke(main, ["--input-dir", str(tmp_path), "--dry-run"])

        assert result.exit_code == 0
        assert "song1" in result.output
        assert "song2" in result.output
        assert "song3" in result.output
        assert "3 project" in result.output  # "3 projects found" or similar

    def test_dry_run_with_empty_directory(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["--input-dir", str(tmp_path), "--dry-run"])

        assert result.exit_code == 0
        assert "0 project" in result.output or "No project" in result.output

    def test_creates_output_directory(self, tmp_path):
        (tmp_path / "song.rpp").write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "previews"

        runner = CliRunner()
        result = runner.invoke(
            main, ["--input-dir", str(tmp_path), "--output-dir", str(output_dir), "--dry-run"]
        )

        assert result.exit_code == 0
        # In dry-run, output dir might not be created, but should not error

    def test_accepts_format_option(self, tmp_path):
        (tmp_path / "song.rpp").write_text("<REAPER_PROJECT>")

        runner = CliRunner()
        result = runner.invoke(
            main, ["--input-dir", str(tmp_path), "--format", "wav", "--dry-run"]
        )

        assert result.exit_code == 0

    def test_accepts_duration_and_start_options(self, tmp_path):
        (tmp_path / "song.rpp").write_text("<REAPER_PROJECT>")

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--input-dir",
                str(tmp_path),
                "--duration",
                "60",
                "--start",
                "10",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0

    def test_rejects_invalid_format(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["--input-dir", str(tmp_path), "--format", "ogg", "--dry-run"]
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output or "is not one of" in result.output


class TestCLIIntegration:
    """Integration tests for the full render pipeline."""

    def test_end_to_end_rendering(self, tmp_path):
        # Create test RPP files
        (tmp_path / "song1.rpp").write_text("<REAPER_PROJECT>")
        (tmp_path / "song2.rpp").write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "previews"

        runner = CliRunner()
        with patch("reaper_preview.cli.render_project") as mock_render:
            # Mock render to return expected output paths
            def fake_render(rpp_path, output_dir, filename, audio_format, reaper_bin, timeout):
                output_file = output_dir / f"{filename}.{audio_format}"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("fake audio")
                return output_file

            mock_render.side_effect = fake_render

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(tmp_path),
                    "--output-dir",
                    str(output_dir),
                    "--format",
                    "mp3",
                ],
            )

        assert result.exit_code == 0
        assert "song1" in result.output
        assert "song2" in result.output
        assert "2/2" in result.output or "2 of 2" in result.output  # Progress indicator
        assert output_dir.exists()

    def test_creates_output_directory_if_missing(self, tmp_path):
        (tmp_path / "song.rpp").write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "new_output"

        runner = CliRunner()
        with patch("reaper_preview.cli.render_project") as mock_render:
            mock_render.return_value = output_dir / "song.mp3"
            result = runner.invoke(
                main, ["--input-dir", str(tmp_path), "--output-dir", str(output_dir)]
            )

        assert result.exit_code == 0
        assert output_dir.exists()

    def test_continues_on_render_error(self, tmp_path):
        # Create multiple RPP files
        (tmp_path / "song1.rpp").write_text("<REAPER_PROJECT>")
        (tmp_path / "song2.rpp").write_text("<REAPER_PROJECT>")
        (tmp_path / "song3.rpp").write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "previews"

        runner = CliRunner()
        with patch("reaper_preview.cli.render_project") as mock_render:

            def fake_render(rpp_path, output_dir, filename, audio_format, reaper_bin, timeout=300):
                # Fail on song2, succeed on others
                if "song2" in filename:
                    raise RenderError("Simulated render failure")
                output_file = output_dir / f"{filename}.{audio_format}"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("fake audio")
                return output_file

            mock_render.side_effect = fake_render

            result = runner.invoke(
                main, ["--input-dir", str(tmp_path), "--output-dir", str(output_dir)]
            )

        # Should not abort on error
        assert result.exit_code == 0
        assert "song1" in result.output
        assert "song2" in result.output
        assert "song3" in result.output
        assert "Error" in result.output or "Failed" in result.output  # Error message

    def test_shows_progress_for_multiple_projects(self, tmp_path):
        # Create multiple projects
        for i in range(1, 4):
            (tmp_path / f"song{i}.rpp").write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "previews"

        runner = CliRunner()
        with patch("reaper_preview.cli.render_project") as mock_render:
            mock_render.return_value = output_dir / "song.mp3"
            result = runner.invoke(
                main, ["--input-dir", str(tmp_path), "--output-dir", str(output_dir)]
            )

        assert result.exit_code == 0
        # Check for progress indicators
        assert "1/3" in result.output or "1 of 3" in result.output
        assert "2/3" in result.output or "2 of 3" in result.output
        assert "3/3" in result.output or "3 of 3" in result.output
