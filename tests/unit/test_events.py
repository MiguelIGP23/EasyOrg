from easyorg.core.events import EventEmitter, MessageEvent, ProgressEvent, SummaryEvent
from easyorg.core.models import SimulationSummary


def test_event_emitter_dispatches_all_event_types() -> None:
    received_messages: list[MessageEvent] = []
    received_progress: list[ProgressEvent] = []
    received_summaries: list[SummaryEvent] = []

    emitter = EventEmitter(
        on_message=received_messages.append,
        on_progress=received_progress.append,
        on_summary=received_summaries.append,
    )

    summary = SimulationSummary(
        total_files=3,
        image_files=2,
        video_files=1,
        metadata_files=1,
        filename_files=1,
        filesystem_files=1,
        undated_files=0,
        collision_files=0,
        total_bytes=1024,
        available_bytes=4096,
        has_enough_space=True,
    )

    emitter.emit_message("[easyOrg] Iniciando...")
    emitter.emit_progress(1, 3)
    emitter.emit_summary(summary)

    assert received_messages == [MessageEvent(text="[easyOrg] Iniciando...")]
    assert received_progress == [ProgressEvent(current=1, total=3)]
    assert received_summaries == [SummaryEvent(summary=summary)]


def test_event_emitter_allows_missing_callbacks() -> None:
    emitter = EventEmitter()

    summary = SimulationSummary(
        total_files=0,
        image_files=0,
        video_files=0,
        metadata_files=0,
        filename_files=0,
        filesystem_files=0,
        undated_files=0,
        collision_files=0,
        total_bytes=0,
        available_bytes=0,
        has_enough_space=True,
    )

    emitter.emit_message("message")
    emitter.emit_progress(0, 0)
    emitter.emit_summary(summary)
