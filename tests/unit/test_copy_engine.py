import shutil
from datetime import datetime
from pathlib import Path

from easyorg.core.models import DateSource, MediaType, OperationMode, OperationResult, PlannedOperation
from easyorg.core.organizer import CopyEngine, validate_copied_file


def _operation(source_path: Path, destination_path: Path) -> PlannedOperation:
    return PlannedOperation(
        source_path=source_path,
        destination_path=destination_path,
        mode=OperationMode.COPY,
        media_type=MediaType.IMAGE,
        size_bytes=source_path.stat().st_size,
        capture_date=datetime(2024, 3, 18, 12, 0, 0),
        date_source=DateSource.METADATA_PRIMARY,
    )


def test_copy_engine_copies_and_validates_file(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "out" / "source.jpg"
    source.write_bytes(b"image-bytes")

    result = CopyEngine().copy_operation(_operation(source, destination))

    assert result == OperationResult(source, destination, True, "")
    assert destination.read_bytes() == b"image-bytes"


def test_copy_engine_reports_copy_permission_failure(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "out" / "source.jpg"
    source.write_bytes(b"image-bytes")

    def failing_copy(source_path: Path, destination_path: Path) -> None:
        raise PermissionError("permission denied")

    result = CopyEngine(copy_function=failing_copy).copy_operation(_operation(source, destination))

    assert result.success is False
    assert "permission denied" in result.message
    assert destination.exists() is False


def test_copy_engine_reports_size_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "out" / "source.jpg"
    source.write_bytes(b"image-bytes")

    def short_copy(source_path: Path, destination_path: Path) -> None:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_bytes(b"short")

    result = CopyEngine(copy_function=short_copy).copy_operation(_operation(source, destination))

    assert result.success is False
    assert result.message == "destination file size does not match source"


def test_copy_engine_reports_destination_disappearing_after_copy(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "out" / "source.jpg"
    source.write_bytes(b"image-bytes")

    def remove_destination(source_path: Path, destination_path: Path) -> None:
        destination_path.unlink()

    result = CopyEngine(
        copy_function=shutil.copy2,
        post_copy_hook=remove_destination,
    ).copy_operation(_operation(source, destination))

    assert result.success is False
    assert result.message == "destination file does not exist after copy"


def test_copy_engine_continues_when_one_operation_fails(tmp_path: Path) -> None:
    first_source = tmp_path / "first.jpg"
    second_source = tmp_path / "second.jpg"
    first_source.write_bytes(b"first")
    second_source.write_bytes(b"second")

    first_destination = tmp_path / "out" / "first.jpg"
    second_destination = tmp_path / "out" / "second.jpg"

    def conditional_copy(source_path: Path, destination_path: Path) -> None:
        if source_path.name == "first.jpg":
            raise PermissionError("permission denied")
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)

    engine = CopyEngine(copy_function=conditional_copy)

    results = engine.copy_operations(
        [
            _operation(first_source, first_destination),
            _operation(second_source, second_destination),
        ]
    )

    assert [result.success for result in results] == [False, True]
    assert second_destination.read_bytes() == b"second"


def test_validate_copied_file_detects_success(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "destination.jpg"
    source.write_bytes(b"same-size")
    destination.write_bytes(b"same-size")

    assert validate_copied_file(source, destination) == (True, "")
