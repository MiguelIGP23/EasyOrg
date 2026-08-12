from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class DateSource(str, Enum):
    METADATA_PRIMARY = "metadata_primary"
    METADATA_SECONDARY = "metadata_secondary"
    FILENAME = "filename"
    FILESYSTEM_MODIFICATION = "filesystem_modification"
    FILESYSTEM_CREATION = "filesystem_creation"
    NONE = "none"


class OperationMode(str, Enum):
    COPY = "copy"
    MOVE = "move"


class OrganizationMode(str, Enum):
    YEAR_MONTH = "year_month"
    YEAR_MONTH_WEEK = "year_month_week"


@dataclass(frozen=True)
class MediaFile:
    source_path: Path
    media_type: MediaType
    size_bytes: int
    capture_date: datetime | None = None
    date_source: DateSource = DateSource.NONE


@dataclass(frozen=True)
class PlannedOperation:
    source_path: Path
    destination_path: Path
    mode: OperationMode
    media_type: MediaType
    size_bytes: int
    capture_date: datetime | None
    date_source: DateSource


@dataclass(frozen=True)
class ScanStats:
    total_files: int = 0
    image_files: int = 0
    video_files: int = 0
    total_bytes: int = 0


@dataclass(frozen=True)
class OperationResult:
    source_path: Path
    destination_path: Path
    success: bool
    message: str = ""


@dataclass(frozen=True)
class OrganizationPlan:
    base_directory: Path
    mode: OperationMode
    organization_mode: OrganizationMode
    operations: tuple[PlannedOperation, ...] = field(default_factory=tuple)

