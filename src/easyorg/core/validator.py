from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class PathValidationError(ValueError):
    """Raised when source and destination paths are not safe to use."""


@dataclass(frozen=True)
class ValidatedPaths:
    source_directory: Path
    destination_parent_directory: Path


def validate_source_and_destination(
    source_directory: Path,
    destination_parent_directory: Path,
) -> ValidatedPaths:
    source = source_directory.resolve()
    destination = destination_parent_directory.resolve()

    if not source.exists():
        raise PathValidationError("source directory does not exist")
    if not source.is_dir():
        raise PathValidationError("source path must be a directory")

    if not destination.exists():
        raise PathValidationError("destination directory does not exist")
    if not destination.is_dir():
        raise PathValidationError("destination path must be a directory")

    if source == destination:
        raise PathValidationError("source and destination cannot be the same directory")
    if _is_relative_to(destination, source):
        raise PathValidationError("destination cannot be inside source")
    if _is_relative_to(source, destination):
        raise PathValidationError("source cannot be inside destination")

    if not os.access(source, os.R_OK):
        raise PathValidationError("source directory is not readable")
    if not os.access(destination, os.W_OK):
        raise PathValidationError("destination directory is not writable")

    return ValidatedPaths(
        source_directory=source,
        destination_parent_directory=destination,
    )


def _is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
    except ValueError:
        return False
    return True
