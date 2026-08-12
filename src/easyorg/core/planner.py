from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

from easyorg.core.models import (
    DateSource,
    MediaFile,
    OperationMode,
    OrganizationMode,
    OrganizationPlan,
    PlannedOperation,
)
from easyorg.core.paths import build_output_directory_name
from easyorg.utils.dates import month_folder_name, week_of_month


def build_organization_plan(
    media_files: list[MediaFile],
    destination_parent_directory: Path,
    operation_mode: OperationMode,
    organization_mode: OrganizationMode,
    run_date: date,
) -> OrganizationPlan:
    base_directory = build_output_directory_name(destination_parent_directory, run_date)
    planned_operations: list[PlannedOperation] = []
    reserved_destinations: set[Path] = set()

    for media_file in media_files:
        target_directory = _target_directory(base_directory, media_file, organization_mode)
        target_path = _resolve_collision(
            target_directory=target_directory,
            original_name=media_file.source_path.name,
            reserved_destinations=reserved_destinations,
        )
        reserved_destinations.add(target_path)
        planned_operations.append(
            PlannedOperation(
                source_path=media_file.source_path,
                destination_path=target_path,
                mode=operation_mode,
                media_type=media_file.media_type,
                size_bytes=media_file.size_bytes,
                capture_date=media_file.capture_date,
                date_source=media_file.date_source,
            )
        )

    return OrganizationPlan(
        base_directory=base_directory,
        mode=operation_mode,
        organization_mode=organization_mode,
        operations=tuple(planned_operations),
    )


def _target_directory(
    base_directory: Path,
    media_file: MediaFile,
    organization_mode: OrganizationMode,
) -> Path:
    if media_file.capture_date is None or media_file.date_source is DateSource.NONE:
        return base_directory / "SIN_FECHA"

    year_directory = base_directory / f"{media_file.capture_date.year:04d}"
    month_directory = year_directory / month_folder_name(media_file.capture_date.month)

    if organization_mode is OrganizationMode.YEAR_MONTH:
        return month_directory

    return month_directory / f"Semana {week_of_month(media_file.capture_date.day)}"


def _resolve_collision(
    target_directory: Path,
    original_name: str,
    reserved_destinations: set[Path],
) -> Path:
    candidate = target_directory / original_name
    if candidate not in reserved_destinations:
        return candidate

    original_path = Path(original_name)
    suffix = 2
    while True:
        candidate = target_directory / f"{original_path.stem}_{suffix}{original_path.suffix}"
        if candidate not in reserved_destinations:
            return candidate
        suffix += 1
