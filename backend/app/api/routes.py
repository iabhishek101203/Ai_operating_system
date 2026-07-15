from fastapi import APIRouter

from uuid import UUID

from app.schemas.intent import ConfirmedRenameRequest, ConfirmedUndoRequest, RenameFileIntent, SearchFilesIntent
from app.schemas.operations import OperationPreview, OperationResult
from app.services.operation_service import OperationService

router = APIRouter()
operation_service = OperationService()


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
