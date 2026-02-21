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
                    "--input-dir", str(tmp_path),
                    "--output-dir", str(output_dir),
                    "--format", "mp3",
                    "--reaper-bin", "reaper",
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
                main,
                [
                    "--input-dir", str(tmp_path),
                    "--output-dir", str(output_dir),
                    "--reaper-bin", "reaper",
                ],
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
                main,
                [
                    "--input-dir", str(tmp_path),
                    "--output-dir", str(output_dir),
                    "--reaper-bin", "reaper",
                ],
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
                main,
                [
                    "--input-dir", str(tmp_path),
                    "--output-dir", str(output_dir),
                    "--reaper-bin", "reaper",
                ],
            )

        assert result.exit_code == 0
        # Check for progress indicators
        assert "1/3" in result.output or "1 of 3" in result.output
        assert "2/3" in result.output or "2 of 3" in result.output
        assert "3/3" in result.output or "3 of 3" in result.output

    def test_skips_existing_preview_newer_than_rpp(self, tmp_path):
        """If preview exists and is newer than .rpp, skip rendering."""
        import os
        import time

        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text("<REAPER_PROJECT>")

        output_dir = tmp_path / "previews"
        output_dir.mkdir()
        preview = output_dir / "song.mp3"
        preview.write_text("existing preview")

        # Make preview newer than RPP
        old_time = time.time() - 100
        os.utime(rpp_file, (old_time, old_time))

        runner = CliRunner()
        with patch("reaper_preview.cli.render_project") as mock_render:
            result = runner.invoke(
                main,
                [
                    "--input-dir", str(tmp_path),
                    "--output-dir", str(output_dir),
                    "--reaper-bin", "reaper",
                ],
            )

        # render_project should NOT have been called
        mock_render.assert_not_called()
        assert "Skipping" in result.output or "skipping" in result.output

    def test_force_rerenders_existing_preview(self, tmp_path):
        """With --force, re-render even if preview exists."""
        import os
        import time

        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text("<REAPER_PROJECT>")

        output_dir = tmp_path / "previews"
        output_dir.mkdir()
        preview = output_dir / "song.mp3"
        preview.write_text("existing preview")

        # Make preview newer than RPP
        old_time = time.time() - 100
        os.utime(rpp_file, (old_time, old_time))

        runner = CliRunner()
        with patch("reaper_preview.cli.render_project") as mock_render:
            mock_render.return_value = preview
            result = runner.invoke(
                main,
                [
                    "--input-dir", str(tmp_path),
                    "--output-dir", str(output_dir),
                    "--reaper-bin", "reaper",
                    "--force",
                ],
            )

        # render_project SHOULD have been called
        mock_render.assert_called_once()

    def test_cleans_up_temp_rpp_after_render(self, tmp_path):
        """Temp RPP file should be cleaned up after rendering."""
        (tmp_path / "song.rpp").write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "previews"

        temp_files_created = []

        runner = CliRunner()
        with patch("reaper_preview.cli.render_project") as mock_render, \
             patch("reaper_preview.cli.prepare_rpp_for_preview") as mock_prepare:
            # Track temp file creation
            real_temp = tmp_path / "temp_song.rpp"
            real_temp.write_text("temp")
            mock_prepare.return_value = real_temp
            temp_files_created.append(real_temp)

            mock_render.return_value = output_dir / "song.mp3"

            result = runner.invoke(
                main,
                [
                    "--input-dir", str(tmp_path),
                    "--output-dir", str(output_dir),
                    "--reaper-bin", "reaper",
                ],
            )

        assert result.exit_code == 0
        # Temp file should have been cleaned up
        assert not real_temp.exists()

    def test_cleans_up_temp_rpp_on_unexpected_error(self, tmp_path):
        """Temp RPP file should be cleaned up on unexpected exceptions."""
        (tmp_path / "song.rpp").write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "previews"

        runner = CliRunner()
        with patch("reaper_preview.cli.render_project") as mock_render, \
             patch("reaper_preview.cli.prepare_rpp_for_preview") as mock_prepare:
            real_temp = tmp_path / "temp_song.rpp"
            real_temp.write_text("temp")
            mock_prepare.return_value = real_temp

            mock_render.side_effect = RuntimeError("Unexpected failure")

            result = runner.invoke(
                main,
                [
                    "--input-dir", str(tmp_path),
                    "--output-dir", str(output_dir),
                    "--reaper-bin", "reaper",
                ],
            )

        assert result.exit_code == 0
        # Temp file should have been cleaned up despite unexpected error
        assert not real_temp.exists()

    def test_cleans_up_temp_rpp_on_render_error(self, tmp_path):
        """Temp RPP file should be cleaned up even when rendering fails."""
        (tmp_path / "song.rpp").write_text("<REAPER_PROJECT>")
        output_dir = tmp_path / "previews"

        runner = CliRunner()
        with patch("reaper_preview.cli.render_project") as mock_render, \
             patch("reaper_preview.cli.prepare_rpp_for_preview") as mock_prepare:
            real_temp = tmp_path / "temp_song.rpp"
            real_temp.write_text("temp")
            mock_prepare.return_value = real_temp

            mock_render.side_effect = RenderError("Simulated failure")

            result = runner.invoke(
                main,
                [
                    "--input-dir", str(tmp_path),
                    "--output-dir", str(output_dir),
                    "--reaper-bin", "reaper",
                ],
            )

        assert result.exit_code == 0
        # Temp file should have been cleaned up despite the error
        assert not real_temp.exists()

    def test_renders_when_rpp_is_newer_than_preview(self, tmp_path):
        """If .rpp is newer than preview, re-render."""
        import os
        import time

        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text("<REAPER_PROJECT>")

        output_dir = tmp_path / "previews"
        output_dir.mkdir()
        preview = output_dir / "song.mp3"
        preview.write_text("old preview")

        # Make preview older than RPP
        old_time = time.time() - 100
        os.utime(preview, (old_time, old_time))

        runner = CliRunner()
        with patch("reaper_preview.cli.render_project") as mock_render:
            mock_render.return_value = preview
            result = runner.invoke(
                main,
                [
                    "--input-dir", str(tmp_path),
                    "--output-dir", str(output_dir),
                    "--reaper-bin", "reaper",
                ],
            )

        mock_render.assert_called_once()
