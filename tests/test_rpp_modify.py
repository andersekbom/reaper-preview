"""Tests for reaper_preview.rpp_modify module."""

from pathlib import Path

from reaper_preview.rpp_modify import prepare_rpp_for_preview

MINIMAL_RPP = """\
<REAPER_PROJECT 0.1 "6.0"
  RENDER_FILE ""
  RENDER_PATTERN ""
  RENDER_FMT 0 2 0
  RENDER_RANGE 1 0 0 18 1000
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
        assert f'RENDER_FILE "{output_dir}"' in content

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
        assert f'RENDER_FILE "{output_dir}"' in content
        assert 'RENDER_PATTERN "bare-preview"' in content
        assert "RENDER_RANGE 0 0.0 30.0" in content

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
        )
        content = _read_output(result)
        assert f'RENDER_FILE "{output_dir}"' in content
        assert 'RENDER_PATTERN "example-preview"' in content
        assert "RENDER_RANGE 0 0.0 30.0" in content
