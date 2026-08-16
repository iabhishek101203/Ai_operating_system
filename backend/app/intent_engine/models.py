"""
AI Operating System - Intent Engine Models

These models define the internal language used by the Intent Engine.
They are intentionally independent of execution logic and LLM providers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.intent_engine.enums import (
    ClarificationReason,
    ConfidenceLevel,
    EntityType,
    IntentStatus,
    IntentType,
)


class IntentEntity(BaseModel):
    """
    A single entity extracted from the user's request.

    Example:
        "demo.txt"
        "Downloads"
        ".pdf"
    """

    type: EntityType
    value: str
    confidence: float = Field(ge=0.0, le=1.0)


class ClarificationRequest(BaseModel):
    """
    Represents information that must be obtained from the user
    before the workflow can continue.
    """

    required: bool = False
    reason: ClarificationReason = ClarificationReason.UNKNOWN
    question: str | None = None


class IntentMetadata(BaseModel):
    """
    Metadata generated during intent understanding.
    """

    llm_provider: str | None = None
    model_name: str | None = None
    processing_time_ms: float | None = None

    extra: dict[str, Any] = Field(default_factory=dict)


class ParsedIntent(BaseModel):
    """
    Final output of the Intent Engine.

    This object is passed to the Planner.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))

    created_at: datetime = Field(
    default_factory=lambda: datetime.now(UTC)
)

    raw_text: str

    normalized_text: str

    intent_type: IntentType = IntentType.UNKNOWN

    status: IntentStatus = IntentStatus.RECEIVED

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW

    entities: list[IntentEntity] = Field(default_factory=list)

    clarification: ClarificationRequest = Field(
        default_factory=ClarificationRequest
    )

    metadata: IntentMetadata = Field(
        default_factory=IntentMetadata
    )


class IntentContext(BaseModel):
    """
    Additional runtime context supplied to the Intent Engine.

    This is intentionally separate from ParsedIntent.
    """

    workspace_root: str | None = None

    current_directory: str | None = None

    recent_files: list[str] = Field(default_factory=list)

    active_project: str | None = None

    environment: dict[str, Any] = Field(default_factory=dict)