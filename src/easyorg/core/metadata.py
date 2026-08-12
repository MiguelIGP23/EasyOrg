from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from os import stat_result


@dataclass(frozen=True)
class FilesystemDates:
    modification_date: datetime
    creation_date: datetime | None


@dataclass(frozen=True)
class MetadataRecord:
    source_path: Path
    fields: dict[str, str]
    error: str | None = None


def get_filesystem_dates(file_path: Path) -> FilesystemDates:
    stat_result = file_path.stat()

    return FilesystemDates(
        modification_date=datetime.fromtimestamp(stat_result.st_mtime),
        creation_date=_extract_creation_date(stat_result),
    )


def _extract_creation_date(stat_result: stat_result) -> datetime | None:
    if sys.platform.startswith("win"):
        return datetime.fromtimestamp(stat_result.st_ctime)

    birthtime = getattr(stat_result, "st_birthtime", None)
    if birthtime is None:
        return None

    return datetime.fromtimestamp(birthtime)


class ExifToolMetadataReader:
    MAX_BATCH_SIZE = 200
    MAX_COMMAND_CHARS = 24000
    PHOTO_FIELDS = (
        "DateTimeOriginal",
        "CreateDate",
    )
    VIDEO_FIELDS = (
        "DateTimeOriginal",
        "MediaCreateDate",
        "TrackCreateDate",
        "CreateDate",
    )

    def __init__(
        self,
        exiftool_path: Path,
        run_command: callable = subprocess.run,
    ) -> None:
        self._exiftool_path = exiftool_path
        self._run_command = run_command

    def read_batch(self, file_paths: list[Path]) -> dict[Path, MetadataRecord]:
        if not file_paths:
            return {}

        records_by_path: dict[Path, MetadataRecord] = {}
        for batch in self._split_batches(file_paths):
            payload = self._read_command_payload_with_fallback(batch)
            records_by_path.update(self._normalize_payload(batch, payload))

        return records_by_path

    def _read_command_payload_with_fallback(self, file_paths: list[Path]) -> list[dict[str, object]]:
        try:
            return self._read_command_payload(file_paths)
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
            if len(file_paths) == 1:
                raise

        midpoint = len(file_paths) // 2
        left_payload = self._read_command_payload_with_fallback(file_paths[:midpoint])
        right_payload = self._read_command_payload_with_fallback(file_paths[midpoint:])
        return [*left_payload, *right_payload]

    def _read_command_payload(self, file_paths: list[Path]) -> list[dict[str, object]]:
        completed = self._run_command(
            self._build_command(file_paths),
            check=False,
            capture_output=True,
            text=True,
            **_subprocess_window_kwargs(),
        )

        if completed.returncode != 0 and not completed.stdout.strip():
            stderr = completed.stderr.strip()
            detail = stderr or f"codigo de salida {completed.returncode}"
            raise RuntimeError(f"ExifTool no pudo leer metadatos: {detail}")

        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            if completed.returncode != 0:
                stderr = completed.stderr.strip()
                detail = stderr or f"codigo de salida {completed.returncode}"
                raise RuntimeError(f"ExifTool devolvio una respuesta invalida: {detail}") from exc
            raise

    def _build_command(self, file_paths: list[Path]) -> list[str]:
        return [
            str(self._exiftool_path),
            "-j",
            "-n",
            "-DateTimeOriginal",
            "-CreateDate",
            "-MediaCreateDate",
            "-TrackCreateDate",
            *[str(path) for path in file_paths],
        ]

    def _normalize_payload(
        self,
        file_paths: list[Path],
        payload: list[dict[str, object]],
    ) -> dict[Path, MetadataRecord]:
        records_by_path: dict[Path, MetadataRecord] = {}
        for item in payload:
            source_path = Path(item.get("SourceFile", ""))
            if not source_path:
                continue

            error = item.get("Error")
            fields = {
                key: value
                for key, value in item.items()
                if key not in {"SourceFile", "Error"} and isinstance(value, str)
            }
            records_by_path[source_path] = MetadataRecord(
                source_path=source_path,
                fields=fields,
                error=error if isinstance(error, str) else None,
            )

        for path in file_paths:
            records_by_path.setdefault(
                path,
                MetadataRecord(
                    source_path=path,
                    fields={},
                    error="No metadata returned by ExifTool.",
                ),
            )

        return records_by_path

    def _split_batches(self, file_paths: list[Path]) -> list[list[Path]]:
        batches: list[list[Path]] = []
        current_batch: list[Path] = []
        current_command_chars = len(" ".join(self._build_command([])))

        for file_path in file_paths:
            file_path_chars = len(str(file_path)) + 1
            would_exceed_batch_size = len(current_batch) >= self.MAX_BATCH_SIZE
            would_exceed_command_chars = current_batch and (
                current_command_chars + file_path_chars > self.MAX_COMMAND_CHARS
            )

            if would_exceed_batch_size or would_exceed_command_chars:
                batches.append(current_batch)
                current_batch = []
                current_command_chars = len(" ".join(self._build_command([])))

            current_batch.append(file_path)
            current_command_chars += file_path_chars

        if current_batch:
            batches.append(current_batch)

        return batches


def _subprocess_window_kwargs() -> dict[str, object]:
    if not sys.platform.startswith("win"):
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }
