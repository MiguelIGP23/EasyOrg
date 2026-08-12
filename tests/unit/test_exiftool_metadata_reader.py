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


def test_read_batch_splits_large_requests_into_multiple_commands() -> None:
    files = [Path(f"nested\\file_{index:03}.jpg") for index in range(5)]
    commands: list[list[str]] = []

    def fake_run(command, **kwargs) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        payload = [{"SourceFile": path, "DateTimeOriginal": "2024:01:01 10:00:00"} for path in command[7:]]
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    reader = ExifToolMetadataReader(Path("exiftool"), run_command=fake_run)
    reader.MAX_BATCH_SIZE = 2

    records = reader.read_batch(files)

    assert len(commands) == 3
    assert all(file_path in records for file_path in files)


def test_read_batch_falls_back_to_smaller_batches_when_one_batch_fails() -> None:
    files = [Path("a.jpg"), Path("b.jpg"), Path("c.jpg"), Path("d.jpg")]
    commands: list[list[str]] = []

    def fake_run(command, **kwargs) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        requested_paths = [Path(path) for path in command[7:]]
        if len(requested_paths) > 1:
            raise OSError("command line too long")

        payload = [{"SourceFile": str(requested_paths[0]), "DateTimeOriginal": "2024:01:01 10:00:00"}]
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    reader = ExifToolMetadataReader(Path("exiftool"), run_command=fake_run)
    reader.MAX_BATCH_SIZE = 10

    records = reader.read_batch(files)

    assert len(commands) >= 3
    assert all(file_path in records for file_path in files)


def test_read_batch_accepts_non_zero_exit_when_exiftool_returns_json() -> None:
    files = [Path("warning.jpg")]
    payload = [{"SourceFile": "warning.jpg", "Error": "Minor warning"}]

    def fake_run(command, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout=json.dumps(payload),
            stderr="minor warning",
        )

    reader = ExifToolMetadataReader(Path("exiftool"), run_command=fake_run)

    records = reader.read_batch(files)

    assert records[Path("warning.jpg")].error == "Minor warning"


def test_read_batch_raises_clean_error_when_exiftool_fails_without_json() -> None:
    files = [Path("broken.jpg")]

    def fake_run(command, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr="fatal error",
        )

    reader = ExifToolMetadataReader(Path("exiftool"), run_command=fake_run)

    try:
        reader.read_batch(files)
    except RuntimeError as exc:
        assert "fatal error" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")
