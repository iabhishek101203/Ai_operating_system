from pathlib import Path

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.main import app
from app.schemas.intent import RenameFileIntent
from app.services.operation_service import OperationService
from app.storage.operation_log import SQLiteOperationLog


def make_service(tmp_path: Path) -> OperationService:
    settings = Settings(
        allowed_roots=[tmp_path],
        operation_db_path=tmp_path / "operations.sqlite3",
        preview_token_ttl_seconds=600,
    )
    return OperationService(settings=settings, operation_log=SQLiteOperationLog(settings.operation_db_path))


def test_rename_requires_matching_one_time_preview_confirmation(tmp_path: Path) -> None:
    source = tmp_path / "draft.txt"
    source.write_text("first draft", encoding="utf-8")
    service = make_service(tmp_path)
    intent = RenameFileIntent(source_path=source, new_name="final.txt")

    preview = service.preview_rename_file(intent)
    assert preview.requires_confirmation is True
    assert preview.details["effects"][0]["before"] == str(source)

    result = service.execute_rename_file(intent, preview.confirmation_token or "")
    assert result.undo_supported is True
    assert not source.exists()
    assert (tmp_path / "final.txt").read_text(encoding="utf-8") == "first draft"

    with pytest.raises(HTTPException) as exc:
        service.execute_rename_file(intent, preview.confirmation_token or "")
    assert exc.value.status_code == 400


def test_undo_restores_a_rename_and_rejects_modified_file(tmp_path: Path) -> None:
    source = tmp_path / "draft.txt"
    source.write_text("first draft", encoding="utf-8")
    service = make_service(tmp_path)
    intent = RenameFileIntent(source_path=source, new_name="final.txt")

    preview = service.preview_rename_file(intent)
    renamed = service.execute_rename_file(intent, preview.confirmation_token or "")
    undo_preview = service.preview_undo_rename_file(renamed.operation_id)
    undo = service.execute_undo_rename_file(renamed.operation_id, undo_preview.confirmation_token or "")
    assert undo.operation == "undo_rename_file"
    assert source.exists()

    preview = service.preview_rename_file(intent)
    renamed = service.execute_rename_file(intent, preview.confirmation_token or "")
    (tmp_path / "final.txt").write_text("changed", encoding="utf-8")
    with pytest.raises(HTTPException) as exc:
        service.undo_rename_file(renamed.operation_id)
    assert exc.value.status_code == 409


def test_rename_rejects_a_new_name_containing_a_path() -> None:
    with pytest.raises(ValueError):
        RenameFileIntent(source_path="C:/example.txt", new_name="folder/other.txt")


def test_browser_interface_and_api_routes_are_packaged() -> None:
    frontend = Path(__file__).parents[1] / "frontend" / "index.html"
    assert frontend.exists()
    assert "AI Operating System Assistant" in frontend.read_text(encoding="utf-8")

    route_paths = {route.path for route in app.routes if hasattr(route, "path")}
    assert "/api/operations/history" in route_paths
    assert "/api/operations/rename/{operation_id}/undo/preview" in route_paths
