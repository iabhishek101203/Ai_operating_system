"""
AI Operating System - Planner Interface

Defines the interface for converting a ParsedIntent into an
ExecutionPlan.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.intent_engine.models import ParsedIntent
from app.planner.models import ExecutionPlan


class Planner(ABC):
    """
    Base planner interface.

    Every planner (Rule-based, Gemini, Hybrid) must implement
    this interface.
    """

    @abstractmethod
    def create_plan(
        self,
        intent: ParsedIntent,
    ) -> ExecutionPlan:
        """
        Convert a resolved ParsedIntent into an ExecutionPlan.
        """
        raise NotImplementedError