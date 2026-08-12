from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from easyorg.core.cancel import CancellationToken, OperationCancelled
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

    def copy_operations(
        self,
        operations: list[PlannedOperation],
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[OperationResult, ...]:
        results: list[OperationResult] = []
        for operation in operations:
            if cancellation_token is not None:
                try:
                    cancellation_token.raise_if_cancelled()
                except OperationCancelled:
                    break
            results.append(self.copy_operation(operation))
        return tuple(results)


@dataclass
class MoveEngine:
    copy_engine: CopyEngine
    delete_function: Callable[[Path], None] = Path.unlink

    def move_operation(self, operation: PlannedOperation) -> OperationResult:
        copy_result = self.copy_engine.copy_operation(operation)
        if not copy_result.success:
            return copy_result

        try:
            self.delete_function(operation.source_path)
        except OSError as exc:
            return OperationResult(
                source_path=operation.source_path,
                destination_path=operation.destination_path,
                success=False,
                message=str(exc),
            )

        return OperationResult(
            source_path=operation.source_path,
            destination_path=operation.destination_path,
            success=True,
            message="",
        )

    def move_operations(
        self,
        operations: list[PlannedOperation],
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[OperationResult, ...]:
        results: list[OperationResult] = []
        for operation in operations:
            if cancellation_token is not None:
                try:
                    cancellation_token.raise_if_cancelled()
                except OperationCancelled:
                    break
            results.append(self.move_operation(operation))
        return tuple(results)
