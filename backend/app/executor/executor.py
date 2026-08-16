"""
AI Operating System - Executor Interface
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.planner.models import ExecutionPlan


class Executor(ABC):
    """
    Base executor interface.

    Responsible for executing an ExecutionPlan.
    """

    @abstractmethod
    def execute(
        self,
        plan: ExecutionPlan,
    ) -> dict:
        """
        Execute an execution plan.

        Returns a structured execution result.
        """
        raise NotImplementedError