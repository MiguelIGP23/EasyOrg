from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from easyorg.core.models import SimulationSummary


@dataclass(frozen=True)
class MessageEvent:
    text: str


@dataclass(frozen=True)
class ProgressEvent:
    current: int
    total: int


@dataclass(frozen=True)
class SummaryEvent:
    summary: SimulationSummary


class EventEmitter:
    def __init__(
        self,
        on_message: Callable[[MessageEvent], None] | None = None,
        on_progress: Callable[[ProgressEvent], None] | None = None,
        on_summary: Callable[[SummaryEvent], None] | None = None,
    ) -> None:
        self._on_message = on_message
        self._on_progress = on_progress
        self._on_summary = on_summary

    def emit_message(self, text: str) -> None:
        if self._on_message is not None:
            self._on_message(MessageEvent(text=text))

    def emit_progress(self, current: int, total: int) -> None:
        if self._on_progress is not None:
            self._on_progress(ProgressEvent(current=current, total=total))

    def emit_summary(self, summary: SimulationSummary) -> None:
        if self._on_summary is not None:
            self._on_summary(SummaryEvent(summary=summary))
