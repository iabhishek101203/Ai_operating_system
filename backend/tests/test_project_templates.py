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


def test_create_react_project_scaffolding_and_undo(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    
    # We will trigger the React fallback structure by calling create_project
    params = {
        "project_type": "react",
        "project_name": "portfolio-site",
        "location": str(tmp_path)
    }
    
    preview = service.preview_tool_call("create_project", params)
    assert preview.requires_confirmation is True
    assert preview.details["effects"][0]["kind"] == "create_dir"
    
    result = service.execute_tool_call("create_project", params)
    assert result.status == "success"
    
    proj_dir = tmp_path / "portfolio-site"
    assert proj_dir.is_dir()
    assert (proj_dir / "package.json").exists()
    assert (proj_dir / "src" / "App.tsx").exists()
    
    # Undo should delete the whole folder
    undo_result = service.undo_operation(result.operation_id)
    assert undo_result.status == "success"
    assert not proj_dir.exists()


def test_create_django_project_scaffolding(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    params = {
        "project_type": "django",
        "project_name": "backend_portal",
        "location": str(tmp_path)
    }
    
    result = service.execute_tool_call("create_project", params)
    assert result.status == "success"
    
    proj_dir = tmp_path / "backend_portal"
    assert proj_dir.is_dir()
    assert (proj_dir / "manage.py").exists()
    assert (proj_dir / "backend_portal" / "settings.py").exists()


def test_create_readme_workflow(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    
    # Pre-create project folder
    proj_dir = tmp_path / "app"
    proj_dir.mkdir()
    
    params = {
        "project_path": str(proj_dir),
        "content": "# Test App\nRun local server."
    }
    
    preview = service.preview_tool_call("create_readme", params)
    assert preview.requires_confirmation is True
    
    result = service.execute_tool_call("create_readme", params)
    assert result.status == "success"
    
    readme = proj_dir / "README.md"
    assert readme.exists()
    assert readme.read_text(encoding="utf-8") == "# Test App\nRun local server."
    
    # Undo
    undo = service.undo_operation(result.operation_id)
    assert undo.status == "success"
    assert not readme.exists()
