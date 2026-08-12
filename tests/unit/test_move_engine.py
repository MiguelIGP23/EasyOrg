import shutil
from datetime import datetime
from pathlib import Path

from easyorg.core.models import DateSource, MediaType, OperationMode, OperationResult, PlannedOperation
from easyorg.core.organizer import CopyEngine, MoveEngine


def _operation(source_path: Path, destination_path: Path) -> PlannedOperation:
    return PlannedOperation(
        source_path=source_path,
        destination_path=destination_path,
        mode=OperationMode.MOVE,
        media_type=MediaType.IMAGE,
        size_bytes=source_path.stat().st_size,
        capture_date=datetime(2024, 3, 18, 12, 0, 0),
        date_source=DateSource.METADATA_PRIMARY,
    )


def test_move_engine_deletes_source_after_validated_copy(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "out" / "source.jpg"
    source.write_bytes(b"image-bytes")

    result = MoveEngine(copy_engine=CopyEngine()).move_operation(_operation(source, destination))

    assert result == OperationResult(source, destination, True, "")
    assert source.exists() is False
    assert destination.read_bytes() == b"image-bytes"


def test_move_engine_keeps_source_when_copy_validation_fails(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "out" / "source.jpg"
    source.write_bytes(b"image-bytes")

    def short_copy(source_path: Path, destination_path: Path) -> None:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_bytes(b"short")

    result = MoveEngine(copy_engine=CopyEngine(copy_function=short_copy)).move_operation(
        _operation(source, destination)
    )

    assert result.success is False
    assert result.message == "destination file size does not match source"
    assert source.exists() is True


def test_move_engine_keeps_source_when_delete_fails(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "out" / "source.jpg"
    source.write_bytes(b"image-bytes")

    def failing_delete(path: Path) -> None:
        raise PermissionError("delete denied")

    result = MoveEngine(
        copy_engine=CopyEngine(copy_function=shutil.copy2),
        delete_function=failing_delete,
    ).move_operation(_operation(source, destination))

    assert result.success is False
    assert "delete denied" in result.message
    assert source.exists() is True
    assert destination.exists() is True
