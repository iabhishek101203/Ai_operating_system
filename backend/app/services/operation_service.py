from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.intent import SearchFilesIntent
from app.schemas.operations import OperationPreview, OperationResult
from app.storage.operation_log import InMemoryOperationLog
from app.tools.search_files import SearchFilesTool
from app.validators.path_validator import PathValidationError, PathValidator


class OperationService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._path_validator = PathValidator(self._settings)
        self._search_tool = SearchFilesTool()
        self._operation_log = InMemoryOperationLog()

    def preview_search_files(self, intent: SearchFilesIntent) -> OperationPreview:
        root_path = self._validate_directory_or_400(intent)
        max_results = intent.max_results or self._settings.max_search_results

        return OperationPreview(
            operation="search_files",
            risk="read_only",
            summary=f"Search for files matching '{intent.query}' under {root_path}.",
            requires_confirmation=False,
            details={
                "root_path": str(root_path),
                "query": intent.query,
                "include_hidden": intent.include_hidden,
                "max_results": max_results,
            },
        )

    def execute_search_files(self, intent: SearchFilesIntent) -> OperationResult:
        started_at = datetime.now(UTC)
        root_path = self._validate_directory_or_400(intent)
        max_results = intent.max_results or self._settings.max_search_results

        matches = self._search_tool.search(
            root_path,
            intent.query,
            include_hidden=intent.include_hidden,
            max_results=max_results,
        )

        finished_at = datetime.now(UTC)
        result = OperationResult(
            operation_id=uuid4(),
            operation="search_files",
            status="success",
            summary=f"Found {len(matches)} file(s) matching '{intent.query}'.",
            started_at=started_at,
            finished_at=finished_at,
            data={"matches": [str(path) for path in matches]},
            undo_supported=False,
            undo_metadata={},
        )
        self._operation_log.add(result)
        return result

    def _validate_directory_or_400(self, intent: SearchFilesIntent):
        try:
            return self._path_validator.validate_directory(intent.root_path)
        except PathValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
