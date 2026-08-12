from __future__ import annotations

from datetime import date
from io import StringIO
from pathlib import Path

from easyorg.cli.app import run_cli
from easyorg.core.dependencies import ExifToolResolution
from easyorg.core.metadata import MetadataRecord
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


def test_cli_handles_unicode_and_uppercase_extensions(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    nested = source / ".hidden"
    nested.mkdir(parents=True)
    destination.mkdir()

    photo = nested / "Álbum_20240322_194355.JPG"
    photo.write_bytes(b"photo")
    service = _build_service(
        tmp_path,
        {
            photo: MetadataRecord(
                source_path=photo,
                fields={},
                error="missing",
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
        ],
        stdout=StringIO(),
        stderr=StringIO(),
        run_date=date(2026, 8, 12),
        project_root=tmp_path,
        service=service,
    )

    assert exit_code == 0
    assert (
        destination / "easyOrg_2026-08-12" / "2024" / "03 - Marzo" / "Álbum_20240322_194355.JPG"
    ).exists()
