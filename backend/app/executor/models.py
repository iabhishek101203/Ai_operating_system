"""
Execution Result Models
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """
    Result returned after executing an ExecutionPlan.
    """

    success: bool

    message: str

    action: str

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )