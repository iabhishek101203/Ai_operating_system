from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SearchFilesIntent(BaseModel):
    """Structured intent for searching files under an allowed directory."""

    root_path: Path = Field(description="Directory to search within.")
    query: str = Field(min_length=1, max_length=255, description="Case-insensitive filename query.")
    include_hidden: bool = Field(default=False, description="Whether hidden files should be searched.")
    max_results: int | None = Field(default=None, ge=1, le=500)


class RenameFileIntent(BaseModel):
    """Structured, reversible request to rename one regular file."""

    source_path: Path = Field(description="Existing file to rename within an allowed directory.")
    new_name: str = Field(min_length=1, max_length=255, description="New basename only; paths are forbidden.")

    @field_validator("new_name")
    @classmethod
    def validate_new_name(cls, value: str) -> str:
        normalized = value.strip()
        if normalized in {"", ".", ".."}:
            raise ValueError("New name must not be empty, '.' or '..'.")
        if any(separator in normalized for separator in ("/", "\\")):
            raise ValueError("New name must be a basename, not a path.")
        if any(character in normalized for character in '<>:"|?*'):
            raise ValueError("New name contains characters prohibited by the filesystem policy.")
        if any(ord(character) < 32 for character in normalized):
            raise ValueError("New name must not contain control characters.")
        return normalized


class ConfirmedRenameRequest(BaseModel):
    """A rename intent paired with the one-time token issued by its preview."""

    intent: RenameFileIntent
    confirmation_token: str = Field(min_length=16, max_length=512)


class ConfirmedUndoRequest(BaseModel):
    """Confirmation for a previously previewed undo operation."""

    operation_id: UUID
    confirmation_token: str = Field(min_length=16, max_length=512)


class MoveFileIntent(BaseModel):
    """Structured request to move a file to another folder."""

    source_path: Path = Field(description="Existing file to move.")
    target_dir: Path = Field(description="Target directory to place the file in.")


class DeleteFileIntent(BaseModel):
    """Structured request to send a file/folder to trash."""

    path: Path = Field(description="Path to the file or folder to delete safely.")


class OrganizeFolderIntent(BaseModel):
    """Structured request to group files in a directory by extension."""

    folder_path: Path = Field(description="Directory containing files to organize.")


class FindDuplicatesIntent(BaseModel):
    """Structured request to scan a directory for duplicate files by content."""

    folder_path: Path = Field(description="Directory to scan.")


class CreateProjectIntent(BaseModel):
    """Structured request to scaffold a project from a template."""

    project_type: Literal["react", "django", "node"] = Field(description="The template type.")
    project_name: str = Field(min_length=1, max_length=255, description="Name of the project directory.")
    location: Path = Field(description="Parent directory for the project.")

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, value: str) -> str:
        import re
        normalized = value.strip()
        if not re.match(r"^[a-zA-Z0-9_-]+$", normalized):
            raise ValueError("Project name must contain only alphanumeric characters, dashes, and underscores.")
        return normalized


class InitializeGitIntent(BaseModel):
    """Structured request to initialize git in a repository."""

    project_path: Path = Field(description="Directory to run git init in.")


class InstallDependenciesIntent(BaseModel):
    """Structured request to install project dependencies."""

    project_path: Path = Field(description="Directory containing package manager configuration.")
    package_manager: Literal["npm", "pip"] = Field(description="Package manager to run.")


class CreateReadmeIntent(BaseModel):
    """Structured request to write a README.md file."""

    project_path: Path = Field(description="Directory where README.md should be written.")
    content: str = Field(description="Markdown content to write.")


class ToolCall(BaseModel):
    """A single tool invocation in the planning pipeline."""

    tool: Literal[
        "search_files",
        "rename_file",
        "move_file",
        "delete_file",
        "organize_folder",
        "find_duplicates",
        "create_project",
        "initialize_git",
        "install_dependencies",
        "create_readme"
    ] = Field(description="Name of the tool to invoke.")
    parameters: dict[str, Any] = Field(description="Parameters conforming to the target tool's schema.")


class ExecutionPlan(BaseModel):
    """Structured JSON schema used by Gemini to plan workflow actions."""

    explanation: str = Field(description="Brief explanation of the plan's actions.")
    steps: list[ToolCall] = Field(description="Sequential list of actions.")


class ConfirmedPlanExecutionRequest(BaseModel):
    """A confirmed list of tool calls to execute, authenticated by a one-time token."""

    steps: list[ToolCall]
    confirmation_token: str = Field(min_length=16, max_length=512)

