from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Sequence, TextIO

from easyorg import __version__
from easyorg.core.cancel import CancellationToken
from easyorg.core.events import EventEmitter
from easyorg.core.models import OperationMode, OrganizationMode
from easyorg.core.service import AnalysisResult, EasyOrgService


@dataclass(frozen=True)
class CliConfig:
    source_directory: Path
    destination_parent_directory: Path
    operation_mode: OperationMode
    organization_mode: OrganizationMode
    auto_confirm: bool
    cleanup_after_copy: bool


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="easyorg", description="Organiza fotos y videos por fecha.")
    parser.add_argument("--source", type=Path, help="Directorio origen")
    parser.add_argument("--destination", type=Path, help="Directorio destino padre")
    parser.add_argument("--mode", choices=["copy", "move"], help="Modo de operacion")
    parser.add_argument(
        "--organization",
        choices=["year-month", "year-month-week"],
        help="Estructura de organizacion",
    )
    parser.add_argument("--yes", action="store_true", help="Confirmar ejecucion sin pedir aprobacion")
    parser.add_argument(
        "--delete-sources-after-copy",
        action="store_true",
        help="Eliminar originales tras una copia totalmente validada",
    )
    parser.add_argument("--gui", action="store_true", help="Iniciar la interfaz grafica")
    parser.add_argument("--version", action="version", version=f"easyOrg {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    return run_cli(argv=argv)


def run_cli(
    argv: Sequence[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    run_date: date | None = None,
    project_root: Path | None = None,
    service: EasyOrgService | None = None,
) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    argv = list(argv or sys.argv[1:])

    if not argv and not sys.stdin.isatty():
        print("easyOrg", file=stdout)
        return 0

    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.gui:
        from easyorg.gui.app import run_gui

        run_gui(project_root=project_root or Path(__file__).resolve().parents[3])
        return 0

    cli_config = _build_cli_config(args, input_fn=input_fn, stdout=stdout)
    current_date = run_date or date.today()
    service = service or EasyOrgService(project_root=project_root or Path(__file__).resolve().parents[3])
    event_emitter = EventEmitter(
        on_message=lambda event: print(event.text, file=stdout),
        on_progress=lambda event: print(f"[easyOrg] Progreso: {event.current}/{event.total}", file=stdout),
        on_summary=lambda event: _print_summary(event.summary, file=stdout),
    )

    try:
        dependency = service.resolve_dependency()
        if dependency.requires_confirmation and dependency.executable_path is None:
            confirmation = input_fn("ExifTool no esta disponible. Instalar con apt? [s/N]: ").strip().lower()
            if confirmation in {"s", "si", "y", "yes"}:
                dependency = service.resolve_dependency(allow_install=True)
            else:
                print("[easyOrg] ExifTool es obligatorio para continuar.", file=stderr)
                return 1

        analysis = service.analyze(
            source_directory=cli_config.source_directory,
            destination_parent_directory=cli_config.destination_parent_directory,
            operation_mode=cli_config.operation_mode,
            organization_mode=cli_config.organization_mode,
            run_date=current_date,
            event_emitter=event_emitter,
            dependency_resolution=dependency,
        )
    except Exception as exc:
        print(f"[easyOrg] Error estructural: {exc}", file=stderr)
        return 1

    _print_plan_preview(analysis, file=stdout)
    if not cli_config.auto_confirm:
        confirmation = input_fn("Confirmar ejecucion? [s/N]: ").strip().lower()
        if confirmation not in {"s", "si", "y", "yes"}:
            print("[easyOrg] Operacion cancelada por el usuario.", file=stdout)
            return 0

    cancellation_token = CancellationToken()
    try:
        execution = service.execute(
            analysis.plan,
            cancellation_token=cancellation_token,
            event_emitter=event_emitter,
        )
    except KeyboardInterrupt:
        cancellation_token.cancel()
        print("[easyOrg] Cancelacion solicitada.", file=stdout)
        return 130

    _print_execution_summary(execution.summary, file=stdout)

    if (
        cli_config.operation_mode is OperationMode.COPY
        and cli_config.cleanup_after_copy
        and execution.summary.failed_operations == 0
        and not execution.summary.cancelled
    ):
        deleted_count = service.cleanup_sources_after_copy(execution.results)
        print(f"[easyOrg] Originales eliminados tras copia validada: {deleted_count}", file=stdout)

    if execution.summary.failed_operations > 0:
        return 2
    if execution.summary.cancelled:
        return 130
    return 0


def _build_cli_config(
    args: argparse.Namespace,
    *,
    input_fn: Callable[[str], str],
    stdout: TextIO,
) -> CliConfig:
    source_directory = args.source or Path(input_fn("Origen: ").strip())
    destination_parent_directory = args.destination or Path(input_fn("Destino padre: ").strip())

    if args.mode:
        operation_mode = OperationMode(args.mode)
    else:
        operation_mode = _prompt_operation_mode(input_fn, stdout)

    if args.organization:
        organization_mode = {
            "year-month": OrganizationMode.YEAR_MONTH,
            "year-month-week": OrganizationMode.YEAR_MONTH_WEEK,
        }[args.organization]
    else:
        organization_mode = _prompt_organization_mode(input_fn, stdout)

    return CliConfig(
        source_directory=source_directory,
        destination_parent_directory=destination_parent_directory,
        operation_mode=operation_mode,
        organization_mode=organization_mode,
        auto_confirm=bool(args.yes),
        cleanup_after_copy=bool(args.delete_sources_after_copy),
    )


def _prompt_operation_mode(input_fn: Callable[[str], str], stdout: TextIO) -> OperationMode:
    print("Modo [copy/move]: ", end="", file=stdout)
    value = input_fn("").strip().lower()
    return OperationMode(value)


def _prompt_organization_mode(input_fn: Callable[[str], str], stdout: TextIO) -> OrganizationMode:
    print("Organizacion [year-month/year-month-week]: ", end="", file=stdout)
    value = input_fn("").strip().lower()
    mapping = {
        "year-month": OrganizationMode.YEAR_MONTH,
        "year-month-week": OrganizationMode.YEAR_MONTH_WEEK,
    }
    return mapping[value]


def _print_summary(summary, *, file: TextIO) -> None:
    print("[easyOrg] Resumen de simulacion:", file=file)
    print(f"  archivos: {summary.total_files}", file=file)
    print(f"  imagenes: {summary.image_files}", file=file)
    print(f"  videos: {summary.video_files}", file=file)
    print(f"  metadata: {summary.metadata_files}", file=file)
    print(f"  nombre: {summary.filename_files}", file=file)
    print(f"  filesystem: {summary.filesystem_files}", file=file)
    print(f"  sin fecha: {summary.undated_files}", file=file)
    print(f"  colisiones: {summary.collision_files}", file=file)
    print(f"  bytes totales: {summary.total_bytes}", file=file)
    print(f"  bytes disponibles: {summary.available_bytes}", file=file)


def _print_plan_preview(analysis: AnalysisResult, *, file: TextIO) -> None:
    print(f"[easyOrg] Carpeta de salida: {analysis.plan.base_directory}", file=file)
    print(f"[easyOrg] Operaciones previstas: {len(analysis.plan.operations)}", file=file)


def _print_execution_summary(summary, *, file: TextIO) -> None:
    print("[easyOrg] Resumen final:", file=file)
    print(f"  total: {summary.total_operations}", file=file)
    print(f"  correctas: {summary.successful_operations}", file=file)
    print(f"  fallidas: {summary.failed_operations}", file=file)
    print(f"  cancelada: {'si' if summary.cancelled else 'no'}", file=file)
