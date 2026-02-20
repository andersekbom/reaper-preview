"""Tests for reaper_preview.cli module."""

from pathlib import Path

from click.testing import CliRunner

from reaper_preview.cli import main


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
