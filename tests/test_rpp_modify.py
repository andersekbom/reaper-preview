"""Tests for reaper_preview.rpp_modify module."""

from pathlib import Path

from reaper_preview.rpp_modify import (
    RENDER_CFG_MP3,
    RENDER_CFG_WAV,
    _resolve_relative_file_paths,
    prepare_rpp_for_preview,
)

MINIMAL_RPP = """\
<REAPER_PROJECT 0.1 "6.0"
  RENDER_FILE ""
  RENDER_PATTERN ""
  RENDER_FMT 0 2 0
  RENDER_RANGE 1 0 0 18 1000
  <RENDER_CFG
    ZXZhdxgAAQ==
  >
>
"""

BARE_RPP = """\
<REAPER_PROJECT 0.1 "6.0"
>
"""


def _read_output(path: Path) -> str:
    return path.read_text()


class TestPrepareRppForPreview:
    def test_returns_path_to_temp_file(self, tmp_path):
        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text(MINIMAL_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
        )
        assert result.exists()
        assert result != rpp_file

    def test_original_file_unmodified(self, tmp_path):
        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text(MINIMAL_RPP)
        original_content = rpp_file.read_text()
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
        )
        assert rpp_file.read_text() == original_content

    def test_sets_render_file(self, tmp_path):
        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text(MINIMAL_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
        )
        content = _read_output(result)
        output_dir_str = str(output_dir).replace("\\", "/")
        assert f'RENDER_FILE "{output_dir_str}"' in content

    def test_sets_render_pattern(self, tmp_path):
        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text(MINIMAL_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
        )
        content = _read_output(result)
        assert 'RENDER_PATTERN "song-preview"' in content

    def test_sets_custom_time_bounds(self, tmp_path):
        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text(MINIMAL_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=5.0,
            end=45.0,
        )
        content = _read_output(result)
        # RENDER_RANGE first arg is boundsflag: 0 = custom time bounds
        assert "RENDER_RANGE 0 5.0 45.0" in content

    def test_handles_missing_render_settings(self, tmp_path):
        """RPP without existing render settings should get them added."""
        rpp_file = tmp_path / "bare.rpp"
        rpp_file.write_text(BARE_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="bare-preview",
            start=0.0,
            end=30.0,
        )
        content = _read_output(result)
        output_dir_str = str(output_dir).replace("\\", "/")
        assert f'RENDER_FILE "{output_dir_str}"' in content
        assert 'RENDER_PATTERN "bare-preview"' in content
        assert "RENDER_RANGE 0 0.0 30.0" in content

    def test_sets_mp3_render_cfg(self, tmp_path):
        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text(MINIMAL_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
            audio_format="mp3",
        )
        content = _read_output(result)
        assert f"    {RENDER_CFG_MP3}" in content
        assert "<RENDER_CFG" in content

    def test_sets_wav_render_cfg(self, tmp_path):
        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text(MINIMAL_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
            audio_format="wav",
        )
        content = _read_output(result)
        assert f"    {RENDER_CFG_WAV}" in content

    def test_default_format_is_mp3(self, tmp_path):
        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text(MINIMAL_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
        )
        content = _read_output(result)
        assert f"    {RENDER_CFG_MP3}" in content

    def test_render_cfg_constants_are_nonempty(self):
        assert len(RENDER_CFG_WAV) > 0
        assert len(RENDER_CFG_MP3) > 0

    def test_adds_render_cfg_to_bare_rpp(self, tmp_path):
        rpp_file = tmp_path / "bare.rpp"
        rpp_file.write_text(BARE_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="bare-preview",
            start=0.0,
            end=30.0,
            audio_format="wav",
        )
        content = _read_output(result)
        assert "<RENDER_CFG" in content
        assert f"    {RENDER_CFG_WAV}" in content

    def test_render_file_uses_forward_slashes(self, tmp_path):
        """RENDER_FILE path must use forward slashes even on Windows."""
        rpp_file = tmp_path / "song.rpp"
        rpp_file.write_text(MINIMAL_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        # Wrap output_dir so str() returns backslashes, simulating Windows
        class FakeWindowsPath:
            def __init__(self, real_path):
                self._real = real_path

            def __str__(self):
                return str(self._real).replace("/", "\\")

            def __fspath__(self):
                return str(self)

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=FakeWindowsPath(output_dir),
            filename="song-preview",
            start=0.0,
            end=30.0,
        )
        content = _read_output(result)
        for line in content.splitlines():
            if "RENDER_FILE" in line:
                assert "\\" not in line, f"RENDER_FILE contains backslashes: {line}"
                break

    def test_relative_file_paths_resolved_to_absolute(self, tmp_path):
        """Relative FILE paths should be rewritten to absolute paths."""
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        rpp_file = project_dir / "song.rpp"
        rpp_content = (
            '<REAPER_PROJECT 0.1 "6.0"\n'
            '  RENDER_FILE ""\n'
            '  <ITEM\n'
            '    <SOURCE WAVE\n'
            '      FILE "audio/kick.wav"\n'
            '    >\n'
            '  >\n'
            '>\n'
        )
        rpp_file.write_text(rpp_content)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
        )
        content = _read_output(result)
        expected_abs = str(project_dir / "audio" / "kick.wav").replace("\\", "/")
        assert f'FILE "{expected_abs}"' in content
        assert 'FILE "audio/kick.wav"' not in content

    def test_absolute_file_paths_unchanged(self, tmp_path):
        """Already-absolute FILE paths should not be modified."""
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        rpp_file = project_dir / "song.rpp"
        abs_path = str(tmp_path / "shared" / "sample.wav").replace("\\", "/")
        rpp_content = (
            '<REAPER_PROJECT 0.1 "6.0"\n'
            '  RENDER_FILE ""\n'
            '  <ITEM\n'
            '    <SOURCE WAVE\n'
            f'      FILE "{abs_path}"\n'
            '    >\n'
            '  >\n'
            '>\n'
        )
        rpp_file.write_text(rpp_content)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
        )
        content = _read_output(result)
        assert f'FILE "{abs_path}"' in content

    def test_render_file_not_affected_by_path_resolution(self, tmp_path):
        """RENDER_FILE must not be treated as a FILE source reference."""
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        rpp_file = project_dir / "song.rpp"
        rpp_file.write_text(MINIMAL_RPP)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
        )
        content = _read_output(result)
        output_dir_str = str(output_dir).replace("\\", "/")
        assert f'RENDER_FILE "{output_dir_str}"' in content

    def test_multiple_relative_file_paths_all_resolved(self, tmp_path):
        """All relative FILE entries in a project are resolved."""
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        rpp_file = project_dir / "song.rpp"
        rpp_content = (
            '<REAPER_PROJECT 0.1 "6.0"\n'
            '  RENDER_FILE ""\n'
            '  <ITEM\n'
            '    <SOURCE WAVE\n'
            '      FILE "audio/kick.wav"\n'
            '    >\n'
            '  >\n'
            '  <ITEM\n'
            '    <SOURCE WAVE\n'
            '      FILE "audio/snare.wav"\n'
            '    >\n'
            '  >\n'
            '>\n'
        )
        rpp_file.write_text(rpp_content)
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=rpp_file,
            output_dir=output_dir,
            filename="song-preview",
            start=0.0,
            end=30.0,
        )
        content = _read_output(result)
        kick_abs = str(project_dir / "audio" / "kick.wav").replace("\\", "/")
        snare_abs = str(project_dir / "audio" / "snare.wav").replace("\\", "/")
        assert f'FILE "{kick_abs}"' in content
        assert f'FILE "{snare_abs}"' in content


class TestResolveRelativeFilePaths:
    def test_relative_path_resolved(self, tmp_path):
        rpp_dir = tmp_path / "project"
        rpp_dir.mkdir()
        text = 'FILE "audio/kick.wav"'
        result = _resolve_relative_file_paths(text, rpp_dir)
        expected = str(rpp_dir / "audio" / "kick.wav").replace("\\", "/")
        assert result == f'FILE "{expected}"'

    def test_absolute_path_unchanged(self, tmp_path):
        rpp_dir = tmp_path / "project"
        rpp_dir.mkdir()
        abs_path = str(tmp_path / "shared" / "sample.wav").replace("\\", "/")
        text = f'FILE "{abs_path}"'
        result = _resolve_relative_file_paths(text, rpp_dir)
        assert result == text

    def test_render_file_not_matched(self, tmp_path):
        rpp_dir = tmp_path / "project"
        rpp_dir.mkdir()
        text = 'RENDER_FILE "relative/output"'
        result = _resolve_relative_file_paths(text, rpp_dir)
        assert result == text

    def test_empty_file_path_unchanged(self, tmp_path):
        rpp_dir = tmp_path / "project"
        rpp_dir.mkdir()
        text = 'FILE ""'
        result = _resolve_relative_file_paths(text, rpp_dir)
        assert result == text


    def test_with_real_rpp_file(self, tmp_path):
        """Test with the example.rpp if it exists."""
        example = Path(__file__).parent.parent / "example.rpp"
        if not example.exists():
            return
        output_dir = tmp_path / "previews"
        output_dir.mkdir()

        result = prepare_rpp_for_preview(
            rpp_path=example,
            output_dir=output_dir,
            filename="example-preview",
            start=0.0,
            end=30.0,
            audio_format="mp3",
        )
        content = _read_output(result)
        assert f'RENDER_FILE "{output_dir}"' in content
        assert 'RENDER_PATTERN "example-preview"' in content
        assert "RENDER_RANGE 0 0.0 30.0" in content
        assert f"    {RENDER_CFG_MP3}" in content
