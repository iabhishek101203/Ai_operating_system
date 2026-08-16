from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.core.config import get_settings
from app.schemas.intent import (
    ConfirmedPlanExecutionRequest,
    ConfirmedRenameRequest,
    ConfirmedUndoRequest,
    RenameFileIntent,
    SearchFilesIntent,
)
from app.schemas.operations import OperationPreview, OperationResult
from app.services.ai_service import AIService
from app.services.operation_service import OperationService
from app.tools.workspace import WorkspaceExplorerTool
from typing import Literal

router = APIRouter()
settings = get_settings()
operation_service = OperationService(settings=settings)
ai_service = AIService(settings=settings)
workspace_explorer = WorkspaceExplorerTool(path_validator=operation_service._path_validator)


class ChatPlanRequest(BaseModel):
    message: str
    planner: Literal["auto", "gemini", "rule"] = "auto"


class SettingsUpdateRequest(BaseModel):
    allowed_roots: list[str]
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None


class SettingsResponse(BaseModel):
    allowed_roots: list[str]
    gemini_model: str
    has_api_key: bool


@router.post("/operations/search/preview", response_model=OperationPreview)
def preview_search_files(intent: SearchFilesIntent) -> OperationPreview:
    return operation_service.preview_search_files(intent)


@router.post("/operations/search/execute", response_model=OperationResult)
def execute_search_files(intent: SearchFilesIntent) -> OperationResult:
    return operation_service.execute_search_files(intent)


@router.post("/operations/rename/preview", response_model=OperationPreview)
def preview_rename_file(intent: RenameFileIntent) -> OperationPreview:
    return operation_service.preview_rename_file(intent)


@router.post("/operations/rename/execute", response_model=OperationResult)
def execute_rename_file(request: ConfirmedRenameRequest) -> OperationResult:
    return operation_service.execute_rename_file(request.intent, request.confirmation_token)


@router.post("/operations/rename/{operation_id}/undo/preview", response_model=OperationPreview)
def preview_undo_rename_file(operation_id: UUID) -> OperationPreview:
    return operation_service.preview_undo_rename_file(operation_id)


@router.post("/operations/rename/undo/execute", response_model=OperationResult)
def execute_undo_rename_file(request: ConfirmedUndoRequest) -> OperationResult:
    return operation_service.execute_undo_rename_file(request.operation_id, request.confirmation_token)


@router.get("/operations/history", response_model=list[OperationResult])
def list_operations(limit: int = 50) -> list[OperationResult]:
    return operation_service.list_operations(limit=limit)


@router.post("/chat/plan")
def chat_plan(request: ChatPlanRequest, x_gemini_api_key: Optional[str] = Header(None)) -> dict:
    allowed_roots_str = [str(r) for r in settings.allowed_roots]
    # Use header key first, then fall back to .env key
    api_key = x_gemini_api_key or getattr(settings, "gemini_api_key", None)
    plan = ai_service.generate_plan(
    user_query=request.message,
    allowed_roots=allowed_roots_str,
    current_workspace=str(Path.cwd()),
    api_key=api_key,
    planner=request.planner,
)

    previews = operation_service.preview_plan(plan.steps)

    token = None
    for preview in previews:
        if preview.confirmation_token:
            token = preview.confirmation_token
            break

    return {
        "explanation": plan.explanation,
        "steps": plan.steps,
        "previews": previews,
        "confirmation_token": token,
    }


@router.post("/chat/execute", response_model=list[OperationResult])
def chat_execute(request: ConfirmedPlanExecutionRequest) -> list[OperationResult]:
    return operation_service.execute_plan(request.steps, request.confirmation_token)


@router.get("/settings", response_model=SettingsResponse)
def get_current_settings() -> SettingsResponse:
    return SettingsResponse(
        allowed_roots=[str(r) for r in settings.allowed_roots],
        gemini_model=getattr(settings, "gemini_model", "gemini-2.5-flash"),
        has_api_key=bool(getattr(settings, "gemini_api_key", None)),
    )


@router.post("/settings", response_model=SettingsResponse)
def update_settings(req: SettingsUpdateRequest) -> SettingsResponse:
    settings.allowed_roots = [Path(r) for r in req.allowed_roots]
    if req.gemini_api_key is not None:
        settings.gemini_api_key = req.gemini_api_key if req.gemini_api_key.strip() else None
    if req.gemini_model is not None:
        settings.gemini_model = req.gemini_model
    return SettingsResponse(
        allowed_roots=[str(r) for r in settings.allowed_roots],
        gemini_model=getattr(settings, "gemini_model", "gemini-2.5-flash"),
        has_api_key=bool(getattr(settings, "gemini_api_key", None)),
    )


@router.get("/workspace/files")
def get_workspace_files():
    return workspace_explorer.list_workspace(settings.allowed_roots)

