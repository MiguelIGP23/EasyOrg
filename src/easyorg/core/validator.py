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
        raise PathValidationError("La carpeta de origen no existe.")
    if not source.is_dir():
        raise PathValidationError("La ruta de origen debe ser una carpeta.")

    if not destination.exists():
        raise PathValidationError("La carpeta de destino no existe.")
    if not destination.is_dir():
        raise PathValidationError("La ruta de destino debe ser una carpeta.")

    if source == destination:
        raise PathValidationError("La carpeta de origen y la de destino no pueden ser la misma.")
    if _is_relative_to(destination, source):
        raise PathValidationError("La carpeta de destino no puede estar dentro de la carpeta de origen.")
    if _is_relative_to(source, destination):
        raise PathValidationError("La carpeta de origen no puede estar dentro de la carpeta de destino.")

    if not os.access(source, os.R_OK):
        raise PathValidationError("No se puede leer la carpeta de origen.")
    if not os.access(destination, os.W_OK):
        raise PathValidationError("No se puede escribir en la carpeta de destino.")

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
