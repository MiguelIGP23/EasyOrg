from __future__ import annotations

from datetime import date
from io import StringIO
from pathlib import Path

from easyorg.cli.app import run_cli
from easyorg.core.dependencies import ExifToolResolution
from easyorg.core.metadata import FilesystemDates, MetadataRecord
from easyorg.core.service import EasyOrgService


class StubResolver:
    def resolve(self) -> ExifToolResolution:
        return ExifToolResolution(
            executable_path=Path("exiftool"),
            source="path",
            requires_confirmation=False,
            install_command=None,
            message="ExifTool encontrado en PATH.",
        )


class StubMetadataReader:
    def __init__(self, records: dict[Path, MetadataRecord]) -> None:
        self._records = records

    def read_batch(self, file_paths: list[Path]) -> dict[Path, MetadataRecord]:
        return {
            path: self._records.get(
                path,
                MetadataRecord(source_path=path, fields={}, error="No metadata returned by ExifTool."),
            )
            for path in file_paths
        }


def _build_service(project_root: Path, records: dict[Path, MetadataRecord]) -> EasyOrgService:
    return EasyOrgService(
        project_root=project_root,
        exiftool_resolver=StubResolver(),
        metadata_reader_factory=lambda _path: StubMetadataReader(records),
    )


def test_cli_copy_year_month_workflow(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()

    photo = source / "photo.jpg"
    photo.write_bytes(b"photo")

    service = _build_service(
        tmp_path,
        {
            photo: MetadataRecord(
                source_path=photo,
                fields={"DateTimeOriginal": "2024:03:18 12:00:00"},
                error=None,
            )
        },
    )

    stdout = StringIO()
    exit_code = run_cli(
        [
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--mode",
            "copy",
            "--organization",
            "year-month",
            "--yes",
        ],
        stdout=stdout,
        stderr=StringIO(),
        run_date=date(2026, 8, 12),
        project_root=tmp_path,
        service=service,
    )

    assert exit_code == 0
    assert (
        destination / "easyOrg_2026-08-12" / "2024" / "03 - Marzo" / "photo.jpg"
    ).read_bytes() == b"photo"
    assert source.joinpath("photo.jpg").exists() is True


def test_cli_copy_year_month_week_workflow(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()

    photo = source / "photo.jpg"
    photo.write_bytes(b"photo")

    service = _build_service(
        tmp_path,
        {
            photo: MetadataRecord(
                source_path=photo,
                fields={"DateTimeOriginal": "2024:03:18 12:00:00"},
                error=None,
            )
        },
    )

    exit_code = run_cli(
        [
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--mode",
            "copy",
            "--organization",
            "year-month-week",
            "--yes",
        ],
        stdout=StringIO(),
        stderr=StringIO(),
        run_date=date(2026, 8, 12),
        project_root=tmp_path,
        service=service,
    )

    assert exit_code == 0
    assert (
        destination / "easyOrg_2026-08-12" / "2024" / "03 - Marzo" / "Semana 3" / "photo.jpg"
    ).exists()


def test_cli_move_workflow_removes_source_after_validated_copy(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()

    photo = source / "photo.jpg"
    photo.write_bytes(b"photo")

    service = _build_service(
        tmp_path,
        {
            photo: MetadataRecord(
                source_path=photo,
                fields={"DateTimeOriginal": "2024:03:18 12:00:00"},
                error=None,
            )
        },
    )

    exit_code = run_cli(
        [
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--mode",
            "move",
            "--organization",
            "year-month",
            "--yes",
        ],
        stdout=StringIO(),
        stderr=StringIO(),
        run_date=date(2026, 8, 12),
        project_root=tmp_path,
        service=service,
    )

    assert exit_code == 0
    assert photo.exists() is False


def test_cli_resolves_collisions_and_sin_fecha(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    nested_a = source / "a"
    nested_b = source / "b"
    nested_a.mkdir(parents=True)
    nested_b.mkdir(parents=True)
    destination.mkdir()

    dated = nested_a / "same.jpg"
    undated = nested_b / "same.jpg"
    dated.write_bytes(b"dated")
    undated.write_bytes(b"undated")

    service = _build_service(
        tmp_path,
        {
            dated: MetadataRecord(
                source_path=dated,
                fields={"DateTimeOriginal": "2024:03:18 12:00:00"},
                error=None,
            ),
            undated: MetadataRecord(source_path=undated, fields={}, error="missing"),
        },
    )
    monkeypatch.setattr(
        "easyorg.core.service.get_filesystem_dates",
        lambda path: FilesystemDates(modification_date=None, creation_date=None),  # type: ignore[arg-type]
    )

    exit_code = run_cli(
        [
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--mode",
            "copy",
            "--organization",
            "year-month",
            "--yes",
        ],
        stdout=StringIO(),
        stderr=StringIO(),
        run_date=date(2026, 8, 12),
        project_root=tmp_path,
        service=service,
    )

    assert exit_code == 0
    assert (destination / "easyOrg_2026-08-12" / "2024" / "03 - Marzo" / "same.jpg").exists()
    assert (destination / "easyOrg_2026-08-12" / "SIN_FECHA" / "same.jpg").exists()


def test_cli_cleanup_after_validated_copy(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()

    photo = source / "photo.jpg"
    photo.write_bytes(b"photo")

    service = _build_service(
        tmp_path,
        {
            photo: MetadataRecord(
                source_path=photo,
                fields={"DateTimeOriginal": "2024:03:18 12:00:00"},
                error=None,
            )
        },
    )

    exit_code = run_cli(
        [
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--mode",
            "copy",
            "--organization",
            "year-month",
            "--yes",
            "--delete-sources-after-copy",
        ],
        stdout=StringIO(),
        stderr=StringIO(),
        run_date=date(2026, 8, 12),
        project_root=tmp_path,
        service=service,
    )

    assert exit_code == 0
    assert photo.exists() is False
