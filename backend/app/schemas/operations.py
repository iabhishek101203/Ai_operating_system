from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


OperationName = Literal["search_files", "rename_file", "undo_rename_file"]
OperationRisk = Literal["read_only", "reversible", "destructive", "external"]
OperationStatus = Literal["preview", "success", "failed"]


class OperationPreview(BaseModel):
    operation: OperationName
    risk: OperationRisk
    summary: str
    requires_confirmation: bool
    details: dict[str, Any] = Field(default_factory=dict)
    confirmation_token: str | None = Field(
        default=None,
        description="One-time token required for a mutating operation after the user approves its preview.",
    )


class OperationResult(BaseModel):
    operation_id: UUID
    operation: OperationName
    status: OperationStatus
    summary: str
    started_at: datetime
    finished_at: datetime
    data: dict[str, Any] = Field(default_factory=dict)
    undo_supported: bool
    undo_metadata: dict[str, Any] = Field(default_factory=dict)
