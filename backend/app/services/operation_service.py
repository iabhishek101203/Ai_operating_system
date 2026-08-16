from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.intent import (
    RenameFileIntent,
    SearchFilesIntent,
    MoveFileIntent,
    DeleteFileIntent,
    OrganizeFolderIntent,
    FindDuplicatesIntent,
    CreateProjectIntent,
    InitializeGitIntent,
    InstallDependenciesIntent,
    CreateReadmeIntent,
    ToolCall,
)
from app.schemas.operations import OperationPreview, OperationResult
from app.storage.operation_log import SQLiteOperationLog
from app.storage.preview_store import PreviewAuthorizationError, PreviewStore
from app.tools.rename_file import RenameFileTool
from app.tools.search_files import SearchFilesTool
from app.tools.move_file import MoveFileTool
from app.tools.delete_file import DeleteFileTool
from app.tools.organize_folder import OrganizeFolderTool
from app.tools.find_duplicates import FindDuplicatesTool
from app.tools.project_templates import ProjectTemplatesTool
from app.validators.path_validator import PathValidationError, PathValidator


class OperationService:
    def __init__(self, settings=None, operation_log=None) -> None:
        self._settings = settings or get_settings()
        self._path_validator = PathValidator(self._settings)
        self._search_tool = SearchFilesTool()
        self._rename_tool = RenameFileTool()
        self._move_tool = MoveFileTool()
        self._delete_tool = DeleteFileTool()
        self._organize_tool = OrganizeFolderTool()
        self._find_duplicates_tool = FindDuplicatesTool()
        self._project_tool = ProjectTemplatesTool()
        self._operation_log = operation_log or SQLiteOperationLog(self._settings.operation_db_path)
        self._preview_store = PreviewStore(self._settings.preview_token_ttl_seconds)

    def preview_search_files(self, intent: SearchFilesIntent) -> OperationPreview:
        return self.preview_tool_call("search_files", intent.model_dump())

    def execute_search_files(self, intent: SearchFilesIntent) -> OperationResult:
        return self.execute_tool_call("search_files", intent.model_dump())

    def preview_rename_file(self, intent: RenameFileIntent) -> OperationPreview:
        return self.preview_tool_call("rename_file", intent.model_dump())

    def execute_rename_file(self, intent: RenameFileIntent, confirmation_token: str) -> OperationResult:
        try:
            self._preview_store.consume(confirmation_token, intent.model_dump(mode="json"))
        except PreviewAuthorizationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return self.execute_tool_call("rename_file", intent.model_dump())

    def preview_undo_rename_file(self, operation_id: UUID) -> OperationPreview:
        return self.preview_undo_operation(operation_id)

    def execute_undo_rename_file(self, operation_id: UUID, confirmation_token: str) -> OperationResult:
        return self.execute_undo_operation(operation_id, confirmation_token)

    def undo_rename_file(self, operation_id: UUID) -> OperationResult:
        return self.undo_operation(operation_id)

    def preview_tool_call(self, tool: str, parameters: dict[str, Any]) -> OperationPreview:
        try:
            if tool == "search_files":
                intent = SearchFilesIntent(**parameters)
                root_path = self._validate_path(intent.root_path, exists=True, is_dir=True)
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
            elif tool == "rename_file":
                intent = RenameFileIntent(**parameters)
                source_path = self._validate_path(intent.source_path, exists=True, is_dir=False)
                target_path = source_path.with_name(intent.new_name)
                if target_path.exists() or target_path.is_symlink():
                    raise HTTPException(status_code=409, detail=f"Destination already exists: {target_path}")
                token = self._preview_store.issue(intent.model_dump(mode="json"))
                return OperationPreview(
                    operation="rename_file",
                    risk="reversible",
                    summary=f"Rename '{source_path.name}' to '{intent.new_name}'.",
                    requires_confirmation=True,
                    confirmation_token=token,
                    details={"effects": [{"kind": "rename", "before": str(source_path), "after": str(target_path)}]},
                )
            elif tool == "move_file":
                intent = MoveFileIntent(**parameters)
                source_path = self._validate_path(intent.source_path, exists=True, is_dir=False)
                target_dir = self._validate_path(intent.target_dir, exists=True, is_dir=True)
                target_path = target_dir / source_path.name
                if target_path.exists() or target_path.is_symlink():
                    raise HTTPException(status_code=409, detail=f"Destination already exists: {target_path}")
                token = self._preview_store.issue(intent.model_dump(mode="json"))
                return OperationPreview(
                    operation="move_file",
                    risk="reversible",
                    summary=f"Move '{source_path.name}' to '{target_dir.name}/'.",
                    requires_confirmation=True,
                    confirmation_token=token,
                    details={"effects": [{"kind": "move", "before": str(source_path), "after": str(target_path)}]},
                )
            elif tool == "delete_file":
                intent = DeleteFileIntent(**parameters)
                path = intent.path
                if path.is_dir():
                    path = self._validate_path(path, exists=True, is_dir=True)
                else:
                    path = self._validate_path(path, exists=True, is_dir=False)
                token = self._preview_store.issue(intent.model_dump(mode="json"))
                return OperationPreview(
                    operation="delete_file",
                    risk="reversible",
                    summary=f"Send '{path.name}' to system trash.",
                    requires_confirmation=True,
                    confirmation_token=token,
                    details={"effects": [{"kind": "delete", "path": str(path)}]},
                )
            elif tool == "organize_folder":
                intent = OrganizeFolderIntent(**parameters)
                folder_path = self._validate_path(intent.folder_path, exists=True, is_dir=True)
                token = self._preview_store.issue(intent.model_dump(mode="json"))
                return OperationPreview(
                    operation="organize_folder",
                    risk="reversible",
                    summary=f"Organize files in '{folder_path.name}' into categorized folders.",
                    requires_confirmation=True,
                    confirmation_token=token,
                    details={"effects": [{"kind": "organize", "path": str(folder_path)}]},
                )
            elif tool == "find_duplicates":
                intent = FindDuplicatesIntent(**parameters)
                folder_path = self._validate_path(intent.folder_path, exists=True, is_dir=True)
                return OperationPreview(
                    operation="find_duplicates",
                    risk="read_only",
                    summary=f"Scan for duplicate files under '{folder_path.name}'.",
                    requires_confirmation=False,
                    details={"folder_path": str(folder_path)},
                )
            elif tool == "create_project":
                intent = CreateProjectIntent(**parameters)
                self._validate_path(intent.location, exists=True, is_dir=True)
                project_dir = intent.location / intent.project_name
                self._validate_path(project_dir, exists=False)
                token = self._preview_store.issue(intent.model_dump(mode="json"))
                return OperationPreview(
                    operation="create_project",
                    risk="external",
                    summary=f"Scaffold new {intent.project_type} project '{intent.project_name}' under '{intent.location.name}/'.",
                    requires_confirmation=True,
                    confirmation_token=token,
                    details={"effects": [{"kind": "create_dir", "path": str(project_dir)}]},
                )
            elif tool == "initialize_git":
                intent = InitializeGitIntent(**parameters)
                if intent.project_path.exists():
                    project_path = self._validate_path(intent.project_path, exists=True, is_dir=True)
                else:
                    project_path = self._validate_path(intent.project_path, exists=False)
                token = self._preview_store.issue(intent.model_dump(mode="json"))
                return OperationPreview(
                    operation="initialize_git",
                    risk="external",
                    summary=f"Initialize git repository in '{project_path.name}'.",
                    requires_confirmation=True,
                    confirmation_token=token,
                    details={"effects": [{"kind": "git_init", "path": str(project_path)}]},
                )
            elif tool == "install_dependencies":
                intent = InstallDependenciesIntent(**parameters)
                if intent.project_path.exists():
                    project_path = self._validate_path(intent.project_path, exists=True, is_dir=True)
                else:
                    project_path = self._validate_path(intent.project_path, exists=False)
                token = self._preview_store.issue(intent.model_dump(mode="json"))
                return OperationPreview(
                    operation="install_dependencies",
                    risk="external",
                    summary=f"Install dependencies using {intent.package_manager} in '{project_path.name}'.",
                    requires_confirmation=True,
                    confirmation_token=token,
                    details={
                        "effects": [
                            {
                                "kind": "install_deps",
                                "path": str(project_path),
                                "manager": intent.package_manager,
                            }
                        ]
                    },
                )
            elif tool == "create_readme":
                intent = CreateReadmeIntent(**parameters)
                if intent.project_path.exists():
                    project_path = self._validate_path(intent.project_path, exists=True, is_dir=True)
                else:
                    project_path = self._validate_path(intent.project_path, exists=False)
                readme_path = project_path / "README.md"
                self._validate_path(readme_path, exists=False)
                token = self._preview_store.issue(intent.model_dump(mode="json"))
                return OperationPreview(
                    operation="create_readme",
                    risk="reversible",
                    summary=f"Create README.md in '{project_path.name}'.",
                    requires_confirmation=True,
                    confirmation_token=token,
                    details={"effects": [{"kind": "create_file", "path": str(readme_path)}]},
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported tool: {tool}")
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=f"Validation failed: {str(exc)}")

    def execute_tool_call(self, tool: str, parameters: dict[str, Any]) -> OperationResult:
        started_at = datetime.now(UTC)
        try:
            if tool == "search_files":
                intent = SearchFilesIntent(**parameters)
                root_path = self._validate_path(intent.root_path, exists=True, is_dir=True)
                max_results = intent.max_results or self._settings.max_search_results
                matches = self._search_tool.search(
                    root_path,
                    intent.query,
                    include_hidden=intent.include_hidden,
                    max_results=max_results,
                )
                result = OperationResult(
                    operation_id=uuid4(),
                    operation="search_files",
                    status="success",
                    summary=f"Found {len(matches)} file(s) matching '{intent.query}'.",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    data={"matches": [str(path) for path in matches]},
                    undo_supported=False,
                )
            elif tool == "rename_file":
                intent = RenameFileIntent(**parameters)
                source_path = self._validate_path(intent.source_path, exists=True, is_dir=False)
                target_path = source_path.with_name(intent.new_name)
                source_fingerprint = self._fingerprint(source_path)
                renamed_path = self._rename_tool.rename(source_path, target_path)
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
            elif tool == "move_file":
                intent = MoveFileIntent(**parameters)
                source_path = self._validate_path(intent.source_path, exists=True, is_dir=False)
                target_dir = self._validate_path(intent.target_dir, exists=True, is_dir=True)
                source_fingerprint = self._fingerprint(source_path)
                moved_path = self._move_tool.move(source_path, target_dir)
                result = OperationResult(
                    operation_id=uuid4(),
                    operation="move_file",
                    status="success",
                    summary=f"Moved '{source_path.name}' to '{target_dir.name}/'.",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    data={"effects": [{"kind": "move", "before": str(source_path), "after": str(moved_path)}]},
                    undo_supported=True,
                    undo_metadata={
                        "source_path": str(source_path),
                        "target_path": str(moved_path),
                        "target_fingerprint": source_fingerprint,
                    },
                )
            elif tool == "delete_file":
                intent = DeleteFileIntent(**parameters)
                path = intent.path
                if path.is_dir():
                    path = self._validate_path(path, exists=True, is_dir=True)
                else:
                    path = self._validate_path(path, exists=True, is_dir=False)
                self._delete_tool.delete(path)
                result = OperationResult(
                    operation_id=uuid4(),
                    operation="delete_file",
                    status="success",
                    summary=f"Sent '{path.name}' to system trash.",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    data={"effects": [{"kind": "delete", "path": str(path)}]},
                    undo_supported=False,
                )
            elif tool == "organize_folder":
                intent = OrganizeFolderIntent(**parameters)
                folder_path = self._validate_path(intent.folder_path, exists=True, is_dir=True)
                moves = self._organize_tool.organize(folder_path)
                result = OperationResult(
                    operation_id=uuid4(),
                    operation="organize_folder",
                    status="success",
                    summary=f"Organized {len(moves)} file(s) in '{folder_path.name}'.",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    data={"moves": moves},
                    undo_supported=True,
                    undo_metadata={"moves": moves},
                )
            elif tool == "find_duplicates":
                intent = FindDuplicatesIntent(**parameters)
                folder_path = self._validate_path(intent.folder_path, exists=True, is_dir=True)
                duplicates = self._find_duplicates_tool.find_duplicates(folder_path)
                result = OperationResult(
                    operation_id=uuid4(),
                    operation="find_duplicates",
                    status="success",
                    summary=f"Found {len(duplicates)} duplicate group(s) in '{folder_path.name}'.",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    data={"duplicates": duplicates},
                    undo_supported=False,
                )
            elif tool == "create_project":
                intent = CreateProjectIntent(**parameters)
                self._validate_path(intent.location, exists=True, is_dir=True)
                project_dir = intent.location / intent.project_name
                self._validate_path(project_dir, exists=False)
                created_dir = self._project_tool.create_project(
                    intent.project_type, intent.project_name, intent.location
                )
                result = OperationResult(
                    operation_id=uuid4(),
                    operation="create_project",
                    status="success",
                    summary=f"Created {intent.project_type} project '{intent.project_name}' under '{intent.location.name}/'.",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    data={"project_dir": str(created_dir)},
                    undo_supported=True,
                    undo_metadata={"project_dir": str(created_dir)},
                )
            elif tool == "initialize_git":
                intent = InitializeGitIntent(**parameters)
                if intent.project_path.exists():
                    project_path = self._validate_path(intent.project_path, exists=True, is_dir=True)
                else:
                    project_path = self._validate_path(intent.project_path, exists=False)
                self._project_tool.initialize_git(project_path)
                result = OperationResult(
                    operation_id=uuid4(),
                    operation="initialize_git",
                    status="success",
                    summary=f"Initialized git repository in '{project_path.name}'.",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    data={"project_path": str(project_path)},
                    undo_supported=False,
                )
            elif tool == "install_dependencies":
                intent = InstallDependenciesIntent(**parameters)
                if intent.project_path.exists():
                    project_path = self._validate_path(intent.project_path, exists=True, is_dir=True)
                else:
                    project_path = self._validate_path(intent.project_path, exists=False)
                self._project_tool.install_dependencies(project_path, intent.package_manager)
                result = OperationResult(
                    operation_id=uuid4(),
                    operation="install_dependencies",
                    status="success",
                    summary=f"Installed dependencies using {intent.package_manager} in '{project_path.name}'.",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    data={"project_path": str(project_path)},
                    undo_supported=False,
                )
            elif tool == "create_readme":
                intent = CreateReadmeIntent(**parameters)
                if intent.project_path.exists():
                    project_path = self._validate_path(intent.project_path, exists=True, is_dir=True)
                else:
                    project_path = self._validate_path(intent.project_path, exists=False)
                readme_path = self._project_tool.create_readme(project_path, intent.content)
                result = OperationResult(
                    operation_id=uuid4(),
                    operation="create_readme",
                    status="success",
                    summary=f"Created README.md file in '{project_path.name}'.",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    data={"readme_path": str(readme_path)},
                    undo_supported=True,
                    undo_metadata={"readme_path": str(readme_path)},
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported tool: {tool}")

            self._operation_log.add(result)
            return result
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=f"Validation failed: {str(exc)}")
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Execution error: {str(exc)}")

    def preview_plan(self, steps: list[ToolCall]) -> list[OperationPreview]:
        previews = []
        for step in steps:
            preview = self.preview_tool_call(step.tool, step.parameters)
            previews.append(preview)

        # Issue single token for the entire set of steps
        token = self._preview_store.issue({"steps": [step.model_dump(mode="json") for step in steps]})
        for preview in previews:
            if preview.requires_confirmation:
                preview.confirmation_token = token

        return previews

    def execute_plan(
        self,
        steps: list[ToolCall],
        confirmation_token: str | None = None,
    ) -> list[OperationResult]:
        """
        Execute a workflow. Read-only workflows (e.g. search_files,
        find_duplicates) do not require a confirmation token.
        """

        needs_confirmation = any(
            step.tool in {
                "rename_file",
                "move_file",
                "delete_file",
                "organize_folder",
                "create_project",
                "initialize_git",
                "install_dependencies",
                "create_readme",
            }
            for step in steps
        )

        if needs_confirmation:
            if not confirmation_token:
                raise HTTPException(
                    status_code=400,
                    detail="Confirmation token required for this workflow.",
                )

            try:
                self._preview_store.consume(
                    confirmation_token,
                    {
                        "steps": [
                            step.model_dump(mode="json")
                            for step in steps
                        ]
                    },
                )
            except PreviewAuthorizationError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=str(exc),
                ) from exc

        results: list[OperationResult] = []

        for step in steps:
            try:
                result = self.execute_tool_call(
                    step.tool,
                    step.parameters,
                )
                results.append(result)
            except Exception as exc:
                succeeded = [r.summary for r in results]
                message = f"Step '{step.tool}' failed: {exc}"
                if succeeded:
                    message += (
                        ". Previous successful steps: "
                        + ", ".join(succeeded)
                    )
                raise HTTPException(
                    status_code=500,
                    detail=message,
                ) from exc

        return results

    def undo_operation(self, operation_id: UUID) -> OperationResult:
        original = self._operation_log.get(operation_id)
        if original is None or not original.undo_supported:
            raise HTTPException(status_code=404, detail="Reversible operation not found or undo not supported.")

        started_at = datetime.now(UTC)
        try:
            if original.operation == "rename_file":
                source_path = Path(original.undo_metadata["source_path"])
                target_path = Path(original.undo_metadata["target_path"])
                self._validate_path(target_path, exists=True, is_dir=False)
                if source_path.exists() or source_path.is_symlink():
                    raise HTTPException(
                        status_code=409, detail=f"Cannot undo because original path is occupied: {source_path}"
                    )
                if self._fingerprint(target_path) != original.undo_metadata["target_fingerprint"]:
                    raise HTTPException(
                        status_code=409, detail="Cannot undo because renamed file changed after operation."
                    )
                self._rename_tool.rename(target_path, source_path)
                summary = f"Restored '{target_path.name}' to original name '{source_path.name}'."
                operation_name = "undo_rename_file"

            elif original.operation == "move_file":
                source_path = Path(original.undo_metadata["source_path"])
                target_path = Path(original.undo_metadata["target_path"])
                self._validate_path(target_path, exists=True, is_dir=False)
                if source_path.exists() or source_path.is_symlink():
                    raise HTTPException(
                        status_code=409, detail=f"Cannot undo because original path is occupied: {source_path}"
                    )
                if self._fingerprint(target_path) != original.undo_metadata["target_fingerprint"]:
                    raise HTTPException(
                        status_code=409, detail="Cannot undo because moved file changed after operation."
                    )
                import shutil

                shutil.move(str(target_path), str(source_path))
                summary = f"Moved '{target_path.name}' back to '{source_path.parent.name}/'."
                operation_name = "undo_move_file"

            elif original.operation == "organize_folder":
                moves = original.undo_metadata["moves"]
                for mv in moves:
                    orig = Path(mv["original"])
                    new = Path(mv["new"])
                    if not new.exists():
                        raise HTTPException(
                            status_code=409,
                            detail=f"Cannot undo because organized file was removed/moved: {new}",
                        )
                    if orig.exists() or orig.is_symlink():
                        raise HTTPException(
                            status_code=409, detail=f"Cannot undo because original path is occupied: {orig}"
                        )

                import shutil

                for mv in moves:
                    orig = Path(mv["original"])
                    new = Path(mv["new"])
                    shutil.move(str(new), str(orig))

                created_dirs = {Path(mv["new"]).parent for mv in moves}
                for d in created_dirs:
                    try:
                        if d.exists() and not any(d.iterdir()):
                            d.rmdir()
                    except Exception:
                        pass

                summary = f"Undid organization: restored {len(moves)} file(s) back."
                operation_name = "undo_organize_folder"

            elif original.operation == "create_project":
                project_dir = Path(original.undo_metadata["project_dir"])
                if project_dir.exists() and project_dir.is_dir():
                    import shutil

                    shutil.rmtree(str(project_dir))
                summary = f"Removed scaffolded project directory '{project_dir.name}'."
                operation_name = "undo_create_project"

            elif original.operation == "create_readme":
                readme_path = Path(original.undo_metadata["readme_path"])
                if readme_path.exists():
                    readme_path.unlink()
                summary = f"Removed README.md in '{readme_path.parent.name}'."
                operation_name = "undo_create_readme"

            else:
                raise HTTPException(status_code=400, detail=f"Undo not supported for operation: {original.operation}")

            result = OperationResult(
                operation_id=uuid4(),
                operation=operation_name,
                status="success",
                summary=summary,
                started_at=started_at,
                finished_at=datetime.now(UTC),
                data={"reverted_operation_id": str(operation_id)},
                undo_supported=False,
            )
            self._operation_log.add(result)
            return result
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Undo failed: {str(exc)}")

    def preview_undo_operation(self, operation_id: UUID) -> OperationPreview:
        original = self._operation_log.get(operation_id)
        if original is None or not original.undo_supported:
            raise HTTPException(status_code=404, detail="Reversible operation not found.")

        token = self._preview_store.issue({"operation_id": str(operation_id), "operation": "undo"})

        if original.operation == "rename_file":
            source_path = Path(original.undo_metadata["source_path"])
            target_path = Path(original.undo_metadata["target_path"])
            summary = f"Restore '{target_path.name}' to its original name '{source_path.name}'."
            effects = [{"kind": "rename", "before": str(target_path), "after": str(source_path)}]
        elif original.operation == "move_file":
            source_path = Path(original.undo_metadata["source_path"])
            target_path = Path(original.undo_metadata["target_path"])
            summary = f"Move '{target_path.name}' back to '{source_path.parent.name}/'."
            effects = [{"kind": "move", "before": str(target_path), "after": str(source_path)}]
        elif original.operation == "organize_folder":
            summary = "Restore files in organized folder back to their original locations."
            effects = [{"kind": "restore_files"}]
        elif original.operation == "create_project":
            project_dir = Path(original.undo_metadata["project_dir"])
            summary = f"Permanently remove project folder '{project_dir.name}' and all its contents."
            effects = [{"kind": "delete_dir", "path": str(project_dir)}]
        elif original.operation == "create_readme":
            readme_path = Path(original.undo_metadata["readme_path"])
            summary = f"Delete README.md in '{readme_path.parent.name}'."
            effects = [{"kind": "delete_file", "path": str(readme_path)}]
        else:
            raise HTTPException(status_code=400, detail=f"Undo not supported for operation: {original.operation}")

        return OperationPreview(
            operation=f"undo_{original.operation}",
            risk="reversible",
            summary=summary,
            requires_confirmation=True,
            confirmation_token=token,
            details={"effects": effects, "reverts_operation_id": str(operation_id)},
        )

    def execute_undo_operation(self, operation_id: UUID, confirmation_token: str) -> OperationResult:
        try:
            self._preview_store.consume(confirmation_token, {"operation_id": str(operation_id), "operation": "undo"})
        except PreviewAuthorizationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return self.undo_operation(operation_id)

    def list_operations(self, limit: int = 50) -> list[OperationResult]:
        return self._operation_log.list(limit=limit)

    def _validate_path(self, path: Path, exists: bool = True, is_dir: bool = False) -> Path:
        try:
            if is_dir:
                return self._path_validator.validate_directory(path)
            elif exists:
                return self._path_validator.validate_regular_file(path)
            else:
                return self._path_validator.validate_new_path(path)
        except PathValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @staticmethod
    def _fingerprint(path: Path) -> dict[str, object]:
        digest = sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        stat = path.stat()
        return {"sha256": digest.hexdigest(), "size": stat.st_size}
