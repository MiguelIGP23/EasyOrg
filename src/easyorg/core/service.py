from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

from easyorg.core.cancel import CancellationToken
from easyorg.core.date_resolver import resolve_media_date
from easyorg.core.dependencies import ExifToolResolution, ExifToolResolver
from easyorg.core.events import EventEmitter
from easyorg.core.metadata import ExifToolMetadataReader, FilesystemDates, MetadataRecord, get_filesystem_dates
from easyorg.core.models import MediaFile, OperationMode, OperationResult, OrganizationMode, OrganizationPlan, SimulationSummary
from easyorg.core.organizer import CopyEngine, MoveEngine
from easyorg.core.planner import build_organization_plan, summarize_plan
from easyorg.core.scanner import scan_media_files
from easyorg.core.validator import ValidatedPaths, validate_source_and_destination


@dataclass(frozen=True)
class AnalysisResult:
    resolved_dependency: ExifToolResolution
    validated_paths: ValidatedPaths
    media_files: tuple[MediaFile, ...]
    plan: OrganizationPlan
    summary: SimulationSummary


@dataclass(frozen=True)
class ExecutionSummary:
    total_operations: int
    successful_operations: int
    failed_operations: int
    cancelled: bool


@dataclass(frozen=True)
class ExecutionResult:
    results: tuple[OperationResult, ...]
    summary: ExecutionSummary


class EasyOrgService:
    def __init__(
        self,
        project_root: Path,
        exiftool_resolver: ExifToolResolver | None = None,
        metadata_reader_factory: Callable[[Path], ExifToolMetadataReader] | None = None,
        copy_engine: CopyEngine | None = None,
        move_engine_factory: Callable[[], MoveEngine] | None = None,
    ) -> None:
        self._project_root = project_root
        self._exiftool_resolver = exiftool_resolver or ExifToolResolver(project_root)
        self._metadata_reader_factory = metadata_reader_factory or (lambda path: ExifToolMetadataReader(path))
        self._copy_engine = copy_engine or CopyEngine()
        self._move_engine_factory = move_engine_factory or (lambda: MoveEngine(copy_engine=self._copy_engine))

    def analyze(
        self,
        source_directory: Path,
        destination_parent_directory: Path,
        operation_mode: OperationMode,
        organization_mode: OrganizationMode,
        run_date: date,
        event_emitter: EventEmitter | None = None,
    ) -> AnalysisResult:
        self._emit_message(event_emitter, "[easyOrg] Buscando ExifTool...")
        dependency = self._exiftool_resolver.resolve()
        self._emit_message(event_emitter, f"[easyOrg] {dependency.message}")

        self._emit_message(event_emitter, "[easyOrg] Validando rutas...")
        validated_paths = validate_source_and_destination(source_directory, destination_parent_directory)

        self._emit_message(event_emitter, "[easyOrg] Escaneando...")
        scan_result = scan_media_files(validated_paths.source_directory)
        scanned_files = list(scan_result.media_files)

        self._emit_message(event_emitter, "[easyOrg] Leyendo metadatos...")
        metadata_records = self._metadata_reader_factory(dependency.executable_path).read_batch(
            [media_file.source_path for media_file in scanned_files]
        )

        resolved_media_files: list[MediaFile] = []
        for media_file in scanned_files:
            metadata_record = metadata_records.get(
                media_file.source_path,
                MetadataRecord(source_path=media_file.source_path, fields={}, error="No metadata returned by ExifTool."),
            )
            filesystem_dates = get_filesystem_dates(media_file.source_path)
            resolved_date = resolve_media_date(
                file_path=media_file.source_path,
                metadata_record=metadata_record,
                filesystem_dates=filesystem_dates,
            )
            resolved_media_files.append(
                MediaFile(
                    source_path=media_file.source_path,
                    media_type=media_file.media_type,
                    size_bytes=media_file.size_bytes,
                    capture_date=resolved_date.value,
                    date_source=resolved_date.source,
                )
            )

        self._emit_message(event_emitter, "[easyOrg] Preparando simulacion...")
        plan = build_organization_plan(
            media_files=resolved_media_files,
            destination_parent_directory=validated_paths.destination_parent_directory,
            operation_mode=operation_mode,
            organization_mode=organization_mode,
            run_date=run_date,
        )
        summary = summarize_plan(plan)
        self._emit_summary(event_emitter, summary)

        if not summary.has_enough_space:
            raise ValueError("No hay espacio suficiente en el destino para ejecutar la operacion.")

        return AnalysisResult(
            resolved_dependency=dependency,
            validated_paths=validated_paths,
            media_files=tuple(resolved_media_files),
            plan=plan,
            summary=summary,
        )

    def execute(
        self,
        plan: OrganizationPlan,
        cancellation_token: CancellationToken | None = None,
        event_emitter: EventEmitter | None = None,
    ) -> ExecutionResult:
        results: list[OperationResult] = []
        cancelled = False
        engine = self._copy_engine if plan.mode is OperationMode.COPY else self._move_engine_factory()

        self._emit_message(event_emitter, "[easyOrg] Iniciando procesamiento...")
        total = len(plan.operations)
        for index, operation in enumerate(plan.operations, start=1):
            if cancellation_token is not None and cancellation_token.is_cancel_requested:
                cancelled = True
                break

            try:
                if plan.mode is OperationMode.COPY:
                    result = engine.copy_operation(operation)  # type: ignore[attr-defined]
                else:
                    result = engine.move_operation(operation)  # type: ignore[attr-defined]
            except KeyboardInterrupt:
                cancelled = True
                break

            results.append(result)
            self._emit_progress(event_emitter, index, total)

        summary = ExecutionSummary(
            total_operations=total,
            successful_operations=sum(1 for result in results if result.success),
            failed_operations=sum(1 for result in results if not result.success),
            cancelled=cancelled,
        )
        return ExecutionResult(results=tuple(results), summary=summary)

    def cleanup_sources_after_copy(
        self,
        results: tuple[OperationResult, ...],
    ) -> int:
        deleted_count = 0
        for result in results:
            if not result.success:
                continue
            if result.source_path.exists():
                result.source_path.unlink()
                deleted_count += 1
        return deleted_count

    @staticmethod
    def _emit_message(event_emitter: EventEmitter | None, message: str) -> None:
        if event_emitter is not None:
            event_emitter.emit_message(message)

    @staticmethod
    def _emit_progress(event_emitter: EventEmitter | None, current: int, total: int) -> None:
        if event_emitter is not None:
            event_emitter.emit_progress(current, total)

    @staticmethod
    def _emit_summary(event_emitter: EventEmitter | None, summary: SimulationSummary) -> None:
        if event_emitter is not None:
            event_emitter.emit_summary(summary)
