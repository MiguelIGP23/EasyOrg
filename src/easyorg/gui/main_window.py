from __future__ import annotations

from datetime import date
from pathlib import Path
from queue import Empty, Queue
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from easyorg.core.cancel import CancellationToken
from easyorg.core.events import EventEmitter
from easyorg.core.models import OperationMode, OrganizationMode
from easyorg.core.service import AnalysisResult, EasyOrgService, ExecutionResult
from easyorg.gui.worker import WorkerMessage, WorkerThread


class EasyOrgMainWindow:
    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._service = EasyOrgService(project_root=project_root)
        self._queue: Queue[WorkerMessage] = Queue()
        self._analysis_result: AnalysisResult | None = None
        self._execution_result: ExecutionResult | None = None
        self._cancellation_token: CancellationToken | None = None
        self._current_worker_kind: str | None = None

        self.root = tk.Tk()
        self.root.title("easyOrg")
        self.root.geometry("860x620")

        self.source_var = tk.StringVar()
        self.destination_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="copy")
        self.organization_var = tk.StringVar(value="year-month")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.status_var = tk.StringVar(value="Listo.")

        self._build_layout()
        self.root.after(100, self._poll_queue)

    def run(self) -> None:
        self.root.mainloop()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(container, text="Origen").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(container, textvariable=self.source_var).grid(row=0, column=1, sticky="ew", pady=(0, 8))
        ttk.Button(container, text="Buscar", command=self._browse_source).grid(row=0, column=2, pady=(0, 8))

        ttk.Label(container, text="Destino").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(container, textvariable=self.destination_var).grid(row=1, column=1, sticky="ew", pady=(0, 8))
        ttk.Button(container, text="Buscar", command=self._browse_destination).grid(row=1, column=2, pady=(0, 8))

        controls = ttk.Frame(container)
        controls.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 12))

        ttk.Label(controls, text="Modo").pack(side=tk.LEFT)
        ttk.Radiobutton(controls, text="Copiar", variable=self.mode_var, value="copy").pack(side=tk.LEFT, padx=(8, 12))
        ttk.Radiobutton(controls, text="Mover", variable=self.mode_var, value="move").pack(side=tk.LEFT)

        ttk.Label(controls, text="Estructura").pack(side=tk.LEFT, padx=(24, 8))
        ttk.Radiobutton(
            controls,
            text="Año-Mes",
            variable=self.organization_var,
            value="year-month",
        ).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Radiobutton(
            controls,
            text="Año-Mes-Semana",
            variable=self.organization_var,
            value="year-month-week",
        ).pack(side=tk.LEFT)

        actions = ttk.Frame(container)
        actions.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        self.analyze_button = ttk.Button(actions, text="Analizar", command=self._start_analysis)
        self.analyze_button.pack(side=tk.LEFT)
        self.execute_button = ttk.Button(actions, text="Ejecutar", command=self._start_execution, state=tk.DISABLED)
        self.execute_button.pack(side=tk.LEFT, padx=(8, 0))
        self.cleanup_button = ttk.Button(
            actions,
            text="Eliminar originales tras copia",
            command=self._cleanup_after_copy,
            state=tk.DISABLED,
        )
        self.cleanup_button.pack(side=tk.LEFT, padx=(8, 0))
        self.cancel_button = ttk.Button(actions, text="Cancelar", command=self._cancel_current, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.RIGHT)

        self.activity = tk.Text(container, height=18, state=tk.DISABLED, wrap="word")
        self.activity.grid(row=4, column=0, columnspan=3, sticky="nsew")

        ttk.Progressbar(container, variable=self.progress_var, maximum=100).grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(12, 6),
        )
        ttk.Label(container, textvariable=self.status_var).grid(row=6, column=0, columnspan=3, sticky="w")

    def _browse_source(self) -> None:
        selected = filedialog.askdirectory(title="Selecciona el directorio origen")
        if selected:
            self.source_var.set(selected)

    def _browse_destination(self) -> None:
        selected = filedialog.askdirectory(title="Selecciona el directorio destino padre")
        if selected:
            self.destination_var.set(selected)

    def _start_analysis(self) -> None:
        self._analysis_result = None
        self._execution_result = None
        self.execute_button.configure(state=tk.DISABLED)
        self.cleanup_button.configure(state=tk.DISABLED)
        self.progress_var.set(0.0)
        self._append_activity("[easyOrg] Iniciando analisis...")
        self._set_busy_state("analysis")

        source = Path(self.source_var.get().strip())
        destination = Path(self.destination_var.get().strip())
        mode = OperationMode(self.mode_var.get())
        organization_mode = {
            "year-month": OrganizationMode.YEAR_MONTH,
            "year-month-week": OrganizationMode.YEAR_MONTH_WEEK,
        }[self.organization_var.get()]
        try:
            dependency = self._service.resolve_dependency()
            if dependency.requires_confirmation and dependency.executable_path is None:
                if not messagebox.askyesno(
                    "ExifTool",
                    "ExifTool no esta disponible. Quieres intentar instalarlo automaticamente?",
                ):
                    self._release_busy_state()
                    self.status_var.set("Operacion cancelada.")
                    return
                dependency = self._service.resolve_dependency(allow_install=True)
        except Exception as exc:
            self._release_busy_state()
            messagebox.showerror("Error", str(exc))
            return

        def work() -> AnalysisResult:
            emitter = EventEmitter(
                on_message=lambda event: self._queue.put(WorkerMessage(kind="message", payload=event.text)),
                on_progress=lambda event: self._queue.put(WorkerMessage(kind="progress", payload=(event.current, event.total))),
                on_summary=lambda event: self._queue.put(WorkerMessage(kind="summary", payload=event.summary)),
            )
            return self._service.analyze(
                source_directory=source,
                destination_parent_directory=destination,
                operation_mode=mode,
                organization_mode=organization_mode,
                run_date=date.today(),
                event_emitter=emitter,
                dependency_resolution=dependency,
            )

        WorkerThread(self._queue, work).start()

    def _start_execution(self) -> None:
        if self._analysis_result is None:
            return

        if not messagebox.askyesno("Confirmar", "Se ejecutara el plan de organizacion actual. Continuar?"):
            return

        self._append_activity("[easyOrg] Iniciando ejecucion...")
        self._progress_reset()
        self._cancellation_token = CancellationToken()
        self._set_busy_state("execution")

        def work() -> ExecutionResult:
            emitter = EventEmitter(
                on_message=lambda event: self._queue.put(WorkerMessage(kind="message", payload=event.text)),
                on_progress=lambda event: self._queue.put(WorkerMessage(kind="progress", payload=(event.current, event.total))),
                on_summary=lambda event: self._queue.put(WorkerMessage(kind="summary", payload=event.summary)),
            )
            return self._service.execute(
                self._analysis_result.plan,
                cancellation_token=self._cancellation_token,
                event_emitter=emitter,
            )

        WorkerThread(self._queue, work).start()

    def _cleanup_after_copy(self) -> None:
        if self._execution_result is None:
            return
        if not messagebox.askyesno(
            "Eliminar originales",
            "Se eliminaran los originales de las copias validadas. Continuar?",
        ):
            return

        deleted_count = self._service.cleanup_sources_after_copy(self._execution_result.results)
        self._append_activity(f"[easyOrg] Originales eliminados tras copia validada: {deleted_count}")
        self.cleanup_button.configure(state=tk.DISABLED)

    def _cancel_current(self) -> None:
        if self._cancellation_token is not None:
            self._cancellation_token.cancel()
            self._append_activity("[easyOrg] Cancelacion solicitada.")
            self.status_var.set("Cancelacion solicitada.")

    def _poll_queue(self) -> None:
        try:
            while True:
                message = self._queue.get_nowait()
                self._handle_worker_message(message)
        except Empty:
            pass

        self.root.after(100, self._poll_queue)

    def _handle_worker_message(self, message: WorkerMessage) -> None:
        if message.kind == "message":
            self._append_activity(str(message.payload))
            self.status_var.set(str(message.payload))
            return

        if message.kind == "progress":
            current, total = message.payload  # type: ignore[misc]
            percent = 0.0 if total == 0 else (current / total) * 100.0
            self.progress_var.set(percent)
            self.status_var.set(f"Progreso: {current}/{total}")
            return

        if message.kind == "summary":
            summary = message.payload
            self._append_activity(
                f"[easyOrg] Simulacion: {summary.total_files} archivos, {summary.total_bytes} bytes, "
                f"espacio disponible {summary.available_bytes}."
            )
            return

        if message.kind == "error":
            self._release_busy_state()
            messagebox.showerror("Error", str(message.payload))
            self.status_var.set("Error.")
            return

        if message.kind == "result":
            self._handle_worker_result(message.payload)

    def _handle_worker_result(self, payload: object | None) -> None:
        if self._current_worker_kind == "analysis":
            self._analysis_result = payload  # type: ignore[assignment]
            self.execute_button.configure(state=tk.NORMAL)
            self._append_activity("[easyOrg] Analisis completado.")
            self.status_var.set("Analisis completado.")
        elif self._current_worker_kind == "execution":
            execution_result = payload  # type: ignore[assignment]
            self._execution_result = execution_result
            self._append_activity(
                f"[easyOrg] Ejecucion completada. Correctas: {execution_result.summary.successful_operations}, "
                f"fallidas: {execution_result.summary.failed_operations}, cancelada: "
                f"{'si' if execution_result.summary.cancelled else 'no'}."
            )
            self.status_var.set("Ejecucion completada.")
            if self.mode_var.get() == "copy" and execution_result.summary.failed_operations == 0:
                self.cleanup_button.configure(state=tk.NORMAL)

        self._release_busy_state()

    def _append_activity(self, text: str) -> None:
        self.activity.configure(state=tk.NORMAL)
        self.activity.insert(tk.END, text + "\n")
        self.activity.see(tk.END)
        self.activity.configure(state=tk.DISABLED)

    def _set_busy_state(self, worker_kind: str) -> None:
        self._current_worker_kind = worker_kind
        self.analyze_button.configure(state=tk.DISABLED)
        self.execute_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL)

    def _release_busy_state(self) -> None:
        self._current_worker_kind = None
        self.analyze_button.configure(state=tk.NORMAL)
        self.cancel_button.configure(state=tk.DISABLED)

    def _progress_reset(self) -> None:
        self.progress_var.set(0.0)
