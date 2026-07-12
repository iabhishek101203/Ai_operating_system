from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.intent import RenameFileIntent, SearchFilesIntent
from app.schemas.operations import OperationPreview, OperationResult
from app.storage.operation_log import SQLiteOperationLog
from app.storage.preview_store import PreviewAuthorizationError, PreviewStore
from app.tools.rename_file import RenameFileTool
from app.tools.search_files import SearchFilesTool
from app.validators.path_validator import PathValidationError, PathValidator


class OperationService:
    def __init__(self, settings=None, operation_log=None) -> None:
        self._settings = settings or get_settings()
        self._path_validator = PathValidator(self._settings)
        self._search_tool = SearchFilesTool()
        self._rename_tool = RenameFileTool()
        self._operation_log = operation_log or SQLiteOperationLog(self._settings.operation_db_path)
        self._preview_store = PreviewStore(self._settings.preview_token_ttl_seconds)

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

    def preview_rename_file(self, intent: RenameFileIntent) -> OperationPreview:
        source_path, target_path = self._validated_rename_paths(intent)
        token = self._preview_store.issue(self._rename_payload(intent))
        return OperationPreview(
            operation="rename_file",
            risk="reversible",
            summary=f"Rename '{source_path.name}' to '{target_path.name}'.",
            requires_confirmation=True,
            confirmation_token=token,
            details={
                "effects": [
                    {
                        "kind": "rename",
                        "before": str(source_path),
                        "after": str(target_path),
                        "reversible": True,
                    }
                ],
                "undo": "The original name can be restored unless the file is changed or a conflict appears.",
            },
        )

    def execute_rename_file(self, intent: RenameFileIntent, confirmation_token: str) -> OperationResult:
        try:
            self._preview_store.consume(confirmation_token, self._rename_payload(intent))
        except PreviewAuthorizationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        started_at = datetime.now(UTC)
        source_path, target_path = self._validated_rename_paths(intent)
        source_fingerprint = self._fingerprint(source_path)
        try:
            renamed_path = self._rename_tool.rename(source_path, target_path)
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        result = OperationResult(
            operation_id=uuid4(),
            operation="rename_file",
            status="success",
            summary=f"Renamed '{source_path.name}' to '{renamed_path.name}'.",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            data={"effects": [{"kind": "rename", "before": str(source_path), "after": str(renamed_path)}]},
            undo_supported=True,
            undo_metadata={
                "source_path": str(source_path),
                "target_path": str(renamed_path),
                "target_fingerprint": source_fingerprint,
            },
        )
        self._operation_log.add(result)
        return result

    def undo_rename_file(self, operation_id: UUID) -> OperationResult:
        original = self._get_reversible_rename(operation_id)
        source_path, target_path = self._validated_undo_paths(original)

        started_at = datetime.now(UTC)
        restored_path = self._rename_tool.rename(target_path, source_path)
        result = OperationResult(
            operation_id=uuid4(),
            operation="undo_rename_file",
            status="success",
            summary=f"Restored '{target_path.name}' to '{restored_path.name}'.",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            data={"reverted_operation_id": str(operation_id)},
            undo_supported=False,
            undo_metadata={},
        )
        self._operation_log.add(result)
        return result

    def preview_undo_rename_file(self, operation_id: UUID) -> OperationPreview:
        original = self._get_reversible_rename(operation_id)
        source_path, target_path = self._validated_undo_paths(original)
        token = self._preview_store.issue(self._undo_payload(operation_id))
        return OperationPreview(
            operation="undo_rename_file",
            risk="reversible",
            summary=f"Restore '{target_path.name}' to its original name '{source_path.name}'.",
            requires_confirmation=True,
            confirmation_token=token,
            details={
                "effects": [
                    {
                        "kind": "rename",
                        "before": str(target_path),
                        "after": str(source_path),
                        "reversible": False,
                    }
                ],
                "reverts_operation_id": str(operation_id),
            },
        )

    def execute_undo_rename_file(self, operation_id: UUID, confirmation_token: str) -> OperationResult:
        try:
            self._preview_store.consume(confirmation_token, self._undo_payload(operation_id))
        except PreviewAuthorizationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return self.undo_rename_file(operation_id)

    def list_operations(self, limit: int = 50) -> list[OperationResult]:
        return self._operation_log.list(limit=limit)

    def _validate_directory_or_400(self, intent: SearchFilesIntent):
        try:
            return self._path_validator.validate_directory(intent.root_path)
        except PathValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def _validated_rename_paths(self, intent: RenameFileIntent) -> tuple[Path, Path]:
        try:
            source_path = self._path_validator.validate_regular_file(intent.source_path)
        except PathValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        target_path = source_path.with_name(intent.new_name)
        if target_path.exists() or target_path.is_symlink():
            raise HTTPException(status_code=409, detail=f"Destination already exists: {target_path}")
        return source_path, target_path

    def _get_reversible_rename(self, operation_id: UUID) -> OperationResult:
        original = self._operation_log.get(operation_id)
        if original is None or original.operation != "rename_file" or not original.undo_supported:
            raise HTTPException(status_code=404, detail="Reversible rename operation not found.")
        return original

    def _validated_undo_paths(self, original: OperationResult) -> tuple[Path, Path]:
        source_path = Path(original.undo_metadata["source_path"])
        target_path = Path(original.undo_metadata["target_path"])
        try:
            self._path_validator.validate_regular_file(target_path)
        except PathValidationError as exc:
            raise HTTPException(status_code=409, detail=f"Cannot undo because the renamed file is unavailable: {exc}") from exc
        if source_path.exists() or source_path.is_symlink():
            raise HTTPException(status_code=409, detail=f"Cannot undo because the original path is occupied: {source_path}")
        if self._fingerprint(target_path) != original.undo_metadata["target_fingerprint"]:
            raise HTTPException(status_code=409, detail="Cannot undo because the renamed file changed after the operation.")
        return source_path, target_path

    @staticmethod
    def _rename_payload(intent: RenameFileIntent) -> dict[str, object]:
        return intent.model_dump(mode="json")

    @staticmethod
    def _undo_payload(operation_id: UUID) -> dict[str, object]:
        return {"operation_id": str(operation_id), "operation": "undo_rename_file"}

    @staticmethod
    def _fingerprint(path: Path) -> dict[str, object]:
        digest = sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        stat = path.stat()
        return {"sha256": digest.hexdigest(), "size": stat.st_size}
