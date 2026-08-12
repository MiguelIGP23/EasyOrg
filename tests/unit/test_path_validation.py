from pathlib import Path

import pytest

from easyorg.core.validator import (
    PathValidationError,
    ValidatedPaths,
    validate_source_and_destination,
)


def test_validate_source_and_destination_returns_resolved_paths(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()

    validated = validate_source_and_destination(source, destination)

    assert validated == ValidatedPaths(
        source_directory=source.resolve(),
        destination_parent_directory=destination.resolve(),
    )


def test_validate_source_and_destination_rejects_same_directory(tmp_path: Path) -> None:
    with pytest.raises(PathValidationError, match="no pueden ser la misma"):
        validate_source_and_destination(tmp_path, tmp_path)


def test_validate_source_and_destination_rejects_destination_inside_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = source / "nested-destination"
    source.mkdir()
    destination.mkdir()

    with pytest.raises(PathValidationError, match="destino no puede estar dentro"):
        validate_source_and_destination(source, destination)


def test_validate_source_and_destination_rejects_source_inside_destination(tmp_path: Path) -> None:
    destination = tmp_path / "destination"
    source = destination / "nested-source"
    destination.mkdir()
    source.mkdir()

    with pytest.raises(PathValidationError, match="origen no puede estar dentro"):
        validate_source_and_destination(source, destination)


def test_validate_source_and_destination_requires_existing_directories(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()

    with pytest.raises(PathValidationError, match="destino no existe"):
        validate_source_and_destination(source, destination)


def test_validate_source_and_destination_requires_source_read_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()

    def fake_access(path: str | Path, mode: int) -> bool:
        candidate = Path(path)
        if candidate == source and mode == __import__("os").R_OK:
            return False
        return True

    monkeypatch.setattr("easyorg.core.validator.os.access", fake_access)

    with pytest.raises(PathValidationError, match="No se puede leer"):
        validate_source_and_destination(source, destination)


def test_validate_source_and_destination_requires_destination_write_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()

    def fake_access(path: str | Path, mode: int) -> bool:
        candidate = Path(path)
        if candidate == destination and mode == __import__("os").W_OK:
            return False
        return True

    monkeypatch.setattr("easyorg.core.validator.os.access", fake_access)

    with pytest.raises(PathValidationError, match="No se puede escribir"):
        validate_source_and_destination(source, destination)
