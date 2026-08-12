import shutil
from datetime import datetime
from pathlib import Path

from easyorg.core.cancel import CancellationToken
from easyorg.core.models import DateSource, MediaType, OperationMode, PlannedOperation
from easyorg.core.organizer import CopyEngine, MoveEngine


def _operation(source_path: Path, destination_path: Path, mode: OperationMode) -> PlannedOperation:
    return PlannedOperation(
        source_path=source_path,
        destination_path=destination_path,
        mode=mode,
        media_type=MediaType.IMAGE,
        size_bytes=source_path.stat().st_size,
        capture_date=datetime(2024, 3, 18, 12, 0, 0),
        date_source=DateSource.METADATA_PRIMARY,
    )


def test_copy_engine_stops_before_starting_next_file_when_cancelled(tmp_path: Path) -> None:
    first_source = tmp_path / "first.jpg"
    second_source = tmp_path / "second.jpg"
    first_source.write_bytes(b"first")
    second_source.write_bytes(b"second")

    token = CancellationToken()

    def cancelling_copy(source_path: Path, destination_path: Path) -> None:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        token.cancel()

    results = CopyEngine(copy_function=cancelling_copy).copy_operations(
        [
            _operation(first_source, tmp_path / "out" / "first.jpg", OperationMode.COPY),
            _operation(second_source, tmp_path / "out" / "second.jpg", OperationMode.COPY),
        ],
        cancellation_token=token,
    )

    assert len(results) == 1
    assert results[0].success is True
    assert (tmp_path / "out" / "first.jpg").exists() is True
    assert (tmp_path / "out" / "second.jpg").exists() is False
    assert second_source.exists() is True


def test_move_engine_preserves_pending_files_when_cancelled(tmp_path: Path) -> None:
    first_source = tmp_path / "first.jpg"
    second_source = tmp_path / "second.jpg"
    first_source.write_bytes(b"first")
    second_source.write_bytes(b"second")

    token = CancellationToken()

    def cancelling_copy(source_path: Path, destination_path: Path) -> None:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        token.cancel()

    results = MoveEngine(copy_engine=CopyEngine(copy_function=cancelling_copy)).move_operations(
        [
            _operation(first_source, tmp_path / "out" / "first.jpg", OperationMode.MOVE),
            _operation(second_source, tmp_path / "out" / "second.jpg", OperationMode.MOVE),
        ],
        cancellation_token=token,
    )

    assert len(results) == 1
    assert results[0].success is True
    assert first_source.exists() is False
    assert second_source.exists() is True
    assert (tmp_path / "out" / "second.jpg").exists() is False
