import json
import subprocess
from pathlib import Path

from easyorg.core.metadata import ExifToolMetadataReader, MetadataRecord


def test_read_batch_returns_normalized_records() -> None:
    files = [Path("photo.jpg"), Path("video.mp4")]

    payload = [
        {
            "SourceFile": "photo.jpg",
            "DateTimeOriginal": "2023:04:17 15:30:25",
            "CreateDate": "2023:04:17 15:30:25",
        },
        {
            "SourceFile": "video.mp4",
            "MediaCreateDate": "2021:08:21 12:13:00",
            "TrackCreateDate": "2021:08:21 12:13:01",
        },
    ]

    def fake_run(command, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    reader = ExifToolMetadataReader(Path("exiftool"), run_command=fake_run)

    records = reader.read_batch(files)

    assert records[Path("photo.jpg")] == MetadataRecord(
        source_path=Path("photo.jpg"),
        fields={
            "DateTimeOriginal": "2023:04:17 15:30:25",
            "CreateDate": "2023:04:17 15:30:25",
        },
        error=None,
    )
    assert records[Path("video.mp4")] == MetadataRecord(
        source_path=Path("video.mp4"),
        fields={
            "MediaCreateDate": "2021:08:21 12:13:00",
            "TrackCreateDate": "2021:08:21 12:13:01",
        },
        error=None,
    )


def test_read_batch_preserves_per_file_errors_without_aborting_batch() -> None:
    files = [Path("broken.jpg"), Path("good.jpg")]
    payload = [
        {
            "SourceFile": "broken.jpg",
            "Error": "File is empty",
        },
        {
            "SourceFile": "good.jpg",
            "DateTimeOriginal": "2024:01:01 10:00:00",
        },
    ]

    def fake_run(command, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    reader = ExifToolMetadataReader(Path("exiftool"), run_command=fake_run)

    records = reader.read_batch(files)

    assert records[Path("broken.jpg")].error == "File is empty"
    assert records[Path("broken.jpg")].fields == {}
    assert records[Path("good.jpg")].fields["DateTimeOriginal"] == "2024:01:01 10:00:00"


def test_read_batch_marks_missing_records_as_errors() -> None:
    requested = [Path("missing.jpg")]

    def fake_run(command, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="[]",
            stderr="",
        )

    reader = ExifToolMetadataReader(Path("exiftool"), run_command=fake_run)

    records = reader.read_batch(requested)

    assert records[Path("missing.jpg")].error == "No metadata returned by ExifTool."
