from datetime import datetime, date
from pathlib import Path

from easyorg.core.models import DateSource, MediaFile, MediaType, OperationMode, OrganizationMode
from easyorg.core.planner import build_organization_plan


def test_build_organization_plan_places_files_by_year_and_month(tmp_path: Path) -> None:
    media_files = [
        MediaFile(
            source_path=Path("C:/media/photo.jpg"),
            media_type=MediaType.IMAGE,
            size_bytes=10,
            capture_date=datetime(2024, 3, 18, 12, 0, 0),
            date_source=DateSource.METADATA_PRIMARY,
        )
    ]

    plan = build_organization_plan(
        media_files=media_files,
        destination_parent_directory=tmp_path,
        operation_mode=OperationMode.COPY,
        organization_mode=OrganizationMode.YEAR_MONTH,
        run_date=date(2026, 8, 12),
    )

    assert plan.base_directory == tmp_path / "easyOrg_2026-08-12"
    assert plan.operations[0].destination_path == tmp_path / "easyOrg_2026-08-12" / "2024" / "03 - Marzo" / "photo.jpg"


def test_build_organization_plan_places_files_by_year_month_and_week(tmp_path: Path) -> None:
    media_files = [
        MediaFile(
            source_path=Path("C:/media/photo.jpg"),
            media_type=MediaType.IMAGE,
            size_bytes=10,
            capture_date=datetime(2024, 3, 18, 12, 0, 0),
            date_source=DateSource.METADATA_PRIMARY,
        )
    ]

    plan = build_organization_plan(
        media_files=media_files,
        destination_parent_directory=tmp_path,
        operation_mode=OperationMode.COPY,
        organization_mode=OrganizationMode.YEAR_MONTH_WEEK,
        run_date=date(2026, 8, 12),
    )

    assert plan.operations[0].destination_path == tmp_path / "easyOrg_2026-08-12" / "2024" / "03 - Marzo" / "Semana 3" / "photo.jpg"


def test_build_organization_plan_places_missing_dates_in_sin_fecha(tmp_path: Path) -> None:
    media_files = [
        MediaFile(
            source_path=Path("C:/media/unknown.jpg"),
            media_type=MediaType.IMAGE,
            size_bytes=10,
            capture_date=None,
            date_source=DateSource.NONE,
        )
    ]

    plan = build_organization_plan(
        media_files=media_files,
        destination_parent_directory=tmp_path,
        operation_mode=OperationMode.COPY,
        organization_mode=OrganizationMode.YEAR_MONTH,
        run_date=date(2026, 8, 12),
    )

    assert plan.operations[0].destination_path == tmp_path / "easyOrg_2026-08-12" / "SIN_FECHA" / "unknown.jpg"


def test_build_organization_plan_resolves_name_collisions_deterministically(tmp_path: Path) -> None:
    media_files = [
        MediaFile(
            source_path=Path("C:/media/a/photo.jpg"),
            media_type=MediaType.IMAGE,
            size_bytes=10,
            capture_date=datetime(2024, 3, 18, 12, 0, 0),
            date_source=DateSource.METADATA_PRIMARY,
        ),
        MediaFile(
            source_path=Path("C:/media/b/photo.jpg"),
            media_type=MediaType.IMAGE,
            size_bytes=10,
            capture_date=datetime(2024, 3, 18, 12, 5, 0),
            date_source=DateSource.METADATA_PRIMARY,
        ),
        MediaFile(
            source_path=Path("C:/media/c/photo.jpg"),
            media_type=MediaType.IMAGE,
            size_bytes=10,
            capture_date=datetime(2024, 3, 18, 12, 10, 0),
            date_source=DateSource.METADATA_PRIMARY,
        ),
    ]

    plan = build_organization_plan(
        media_files=media_files,
        destination_parent_directory=tmp_path,
        operation_mode=OperationMode.COPY,
        organization_mode=OrganizationMode.YEAR_MONTH,
        run_date=date(2026, 8, 12),
    )

    destination_names = [operation.destination_path.name for operation in plan.operations]

    assert destination_names == ["photo.jpg", "photo_2.jpg", "photo_3.jpg"]
