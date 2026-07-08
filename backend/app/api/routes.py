from fastapi import APIRouter

from app.schemas.intent import SearchFilesIntent
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
