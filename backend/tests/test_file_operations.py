from pathlib import Path
import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.services.operation_service import OperationService
from app.storage.operation_log import SQLiteOperationLog


def make_service(tmp_path: Path) -> OperationService:
    settings = Settings(
        allowed_roots=[tmp_path],
        operation_db_path=tmp_path / "operations.sqlite3",
        preview_token_ttl_seconds=600,
    )
    return OperationService(settings=settings, operation_log=SQLiteOperationLog(settings.operation_db_path))


def test_move_file_workflow_and_undo(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    
    # Create file
    src = tmp_path / "note.txt"
    src.write_text("my notes", encoding="utf-8")
    
    # Target directory
    target_dir = tmp_path / "archive"
    target_dir.mkdir()
    
    # Move
    params = {"source_path": str(src), "target_dir": str(target_dir)}
    preview = service.preview_tool_call("move_file", params)
    assert preview.requires_confirmation is True
    
    result = service.execute_tool_call("move_file", params)
    assert result.status == "success"
    assert not src.exists()
    assert (target_dir / "note.txt").exists()
    assert (target_dir / "note.txt").read_text(encoding="utf-8") == "my notes"
    
    # Undo
    undo_result = service.undo_operation(result.operation_id)
    assert undo_result.status == "success"
    assert src.exists()
    assert not (target_dir / "note.txt").exists()


def test_delete_file_safely(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    file_to_del = tmp_path / "temp.txt"
    file_to_del.write_text("trash me", encoding="utf-8")
    
    params = {"path": str(file_to_del)}
    preview = service.preview_tool_call("delete_file", params)
    assert preview.requires_confirmation is True
    
    result = service.execute_tool_call("delete_file", params)
    assert result.status == "success"
    assert not file_to_del.exists()


def test_organize_folder_and_undo(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    
    # Create different files
    (tmp_path / "report.pdf").write_text("pdf content", encoding="utf-8")
    (tmp_path / "script.py").write_text("print(1)", encoding="utf-8")
    (tmp_path / "photo.png").write_text("image bytes", encoding="utf-8")
    
    params = {"folder_path": str(tmp_path)}
    preview = service.preview_tool_call("organize_folder", params)
    assert preview.requires_confirmation is True
    
    result = service.execute_tool_call("organize_folder", params)
    assert result.status == "success"
    
    # Should have categorized
    assert (tmp_path / "Documents" / "report.pdf").exists()
    assert (tmp_path / "Code" / "script.py").exists()
    assert (tmp_path / "Images" / "photo.png").exists()
    
    # Undo
    undo_result = service.undo_operation(result.operation_id)
    assert undo_result.status == "success"
    
    # Reverted
    assert (tmp_path / "report.pdf").exists()
    assert (tmp_path / "script.py").exists()
    assert (tmp_path / "photo.png").exists()
    assert not (tmp_path / "Documents").exists()


def test_find_duplicates(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    
    # Create duplicate files
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f3 = tmp_path / "c.txt"
    
    f1.write_text("same content", encoding="utf-8")
    f2.write_text("same content", encoding="utf-8")
    f3.write_text("different content", encoding="utf-8")
    
    params = {"folder_path": str(tmp_path)}
    preview = service.preview_tool_call("find_duplicates", params)
    assert preview.requires_confirmation is False
    
    result = service.execute_tool_call("find_duplicates", params)
    assert result.status == "success"
    
    # Should find duplicates of f1 and f2
    dup_groups = result.data["duplicates"]
    assert len(dup_groups) == 1
    # Key is SHA256, list contains paths
    list_paths = list(dup_groups.values())[0]
    assert len(list_paths) == 2
    assert str(f1) in list_paths
    assert str(f2) in list_paths
