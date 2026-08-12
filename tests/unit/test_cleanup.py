from pathlib import Path

from easyorg.core.models import OperationResult
from easyorg.core.service import EasyOrgService


def test_cleanup_sources_after_copy_deletes_only_successful_files_when_all_succeeded(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    source_a = tmp_path / "a.jpg"
    source_b = tmp_path / "b.jpg"
    source_a.write_bytes(b"a")
    source_b.write_bytes(b"b")

    service = EasyOrgService(project_root=project_root)

    deleted = service.cleanup_sources_after_copy(
        (
            OperationResult(source_path=source_a, destination_path=tmp_path / "out" / "a.jpg", success=True, message=""),
            OperationResult(source_path=source_b, destination_path=tmp_path / "out" / "b.jpg", success=True, message=""),
        )
    )

    assert deleted == 2
    assert source_a.exists() is False
    assert source_b.exists() is False


def test_cleanup_sources_after_copy_is_conservative_when_any_result_failed(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    source_a = tmp_path / "a.jpg"
    source_b = tmp_path / "b.jpg"
    source_a.write_bytes(b"a")
    source_b.write_bytes(b"b")

    service = EasyOrgService(project_root=project_root)

    deleted = service.cleanup_sources_after_copy(
        (
            OperationResult(source_path=source_a, destination_path=tmp_path / "out" / "a.jpg", success=True, message=""),
            OperationResult(source_path=source_b, destination_path=tmp_path / "out" / "b.jpg", success=False, message="failed"),
        )
    )

    assert deleted == 0
    assert source_a.exists() is True
    assert source_b.exists() is True
