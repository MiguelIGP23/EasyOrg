from pathlib import Path

import pytest

from easyorg.core.models import MediaType
from easyorg.core.scanner import classify_media_file, scan_media_files


def test_classify_media_file_supports_known_types() -> None:
    assert classify_media_file(Path("photo.JPG")) is MediaType.IMAGE
    assert classify_media_file(Path("video.MP4")) is MediaType.VIDEO
    assert classify_media_file(Path("notes.txt")) is None


def test_scan_media_files_recursively_collects_supported_media(tmp_path: Path) -> None:
    source = tmp_path / "source"
    nested = source / "nested"
    nested.mkdir(parents=True)

    image = source / "IMG_0001.JPG"
    video = nested / "clip.MP4"
    ignored = nested / "notes.txt"
    helper = source / "image.xmp"

    image.write_bytes(b"image-data")
    video.write_bytes(b"video-data")
    ignored.write_text("ignore")
    helper.write_text("ignore")

    result = scan_media_files(source)

    assert [item.source_path for item in result.media_files] == [image, video]
    assert [item.media_type for item in result.media_files] == [MediaType.IMAGE, MediaType.VIDEO]
    assert result.stats.total_files == 2
    assert result.stats.image_files == 1
    assert result.stats.video_files == 1
    assert result.stats.total_bytes == len(b"image-data") + len(b"video-data")


def test_scan_media_files_ignores_symbolic_links(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()

    real_file = source / "photo.jpg"
    real_file.write_bytes(b"image")

    linked_dir = source / "linked-dir"
    target_dir = tmp_path / "target-dir"
    target_dir.mkdir()
    (target_dir / "other.jpg").write_bytes(b"other")

    linked_file = source / "linked-file.jpg"

    try:
        linked_dir.symlink_to(target_dir, target_is_directory=True)
        linked_file.symlink_to(real_file)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not supported in this environment")

    result = scan_media_files(source)

    assert [item.source_path for item in result.media_files] == [real_file]


def test_scan_media_files_returns_empty_stats_for_non_media_tree(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "readme.md").write_text("ignore")

    result = scan_media_files(source)

    assert result.media_files == ()
    assert result.stats.total_files == 0
    assert result.stats.total_bytes == 0


def test_scan_media_files_skips_files_that_fail_stat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    ok_file = source / "ok.jpg"
    broken_file = source / "broken.jpg"
    ok_file.write_bytes(b"ok")
    broken_file.write_bytes(b"broken")

    original_stat = Path.stat

    def fake_stat(self: Path, *args, **kwargs):
        if self == broken_file:
            raise OSError("file disappeared")
        return original_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", fake_stat)

    result = scan_media_files(source)

    assert [item.source_path for item in result.media_files] == [ok_file]
