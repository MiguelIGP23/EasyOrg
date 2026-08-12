from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Callable


@dataclass(frozen=True)
class WorkerMessage:
    kind: str
    payload: object | None = None


class WorkerThread:
    def __init__(
        self,
        queue: Queue[WorkerMessage],
        target: Callable[[], object],
    ) -> None:
        self._queue = queue
        self._target = target
        self._thread = Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _run(self) -> None:
        try:
            result = self._target()
        except Exception as exc:
            self._queue.put(WorkerMessage(kind="error", payload=exc))
            return

        self._queue.put(WorkerMessage(kind="result", payload=result))
