from __future__ import annotations

from dataclasses import dataclass


class OperationCancelled(Exception):
    """Raised when a batch operation is cancelled before starting the next file."""


@dataclass
class CancellationToken:
    _cancel_requested: bool = False

    def cancel(self) -> None:
        self._cancel_requested = True

    @property
    def is_cancel_requested(self) -> bool:
        return self._cancel_requested

    def raise_if_cancelled(self) -> None:
        if self._cancel_requested:
            raise OperationCancelled("operation cancelled")
