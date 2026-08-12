from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from easyorg.core.models import OperationResult, PlannedOperation


def validate_copied_file(source_path: Path, destination_path: Path) -> tuple[bool, str]:
    if not destination_path.exists():
        return False, "destination file does not exist after copy"

    if source_path.stat().st_size != destination_path.stat().st_size:
        return False, "destination file size does not match source"

    return True, ""


@dataclass
class CopyEngine:
    copy_function: Callable[[Path, Path], object] = shutil.copy2
    post_copy_hook: Callable[[Path, Path], None] | None = None

    def copy_operation(self, operation: PlannedOperation) -> OperationResult:
        destination_path = operation.destination_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.copy_function(operation.source_path, destination_path)
            if self.post_copy_hook is not None:
                self.post_copy_hook(operation.source_path, destination_path)
        except OSError as exc:
            return OperationResult(
                source_path=operation.source_path,
                destination_path=destination_path,
                success=False,
                message=str(exc),
            )

        is_valid, message = validate_copied_file(operation.source_path, destination_path)
        return OperationResult(
            source_path=operation.source_path,
            destination_path=destination_path,
            success=is_valid,
            message=message,
        )

    def copy_operations(self, operations: list[PlannedOperation]) -> tuple[OperationResult, ...]:
        return tuple(self.copy_operation(operation) for operation in operations)
