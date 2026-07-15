from pathlib import Path
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
