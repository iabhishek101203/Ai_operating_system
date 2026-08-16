"""
Rule-Based Planner.

Creates deterministic execution plans from ParsedIntent.
"""

from __future__ import annotations

from app.intent_engine.enums import IntentStatus, IntentType
from app.intent_engine.models import ParsedIntent

from app.planner.models import (
    ExecutionPlan,
    ExecutionStep,
)
from app.planner.planner import Planner


class RuleBasedPlanner(Planner):
    """
    Deterministic execution planner.
    """

    def create_plan(
        self,
        intent: ParsedIntent,
    ) -> ExecutionPlan:

        if intent.status != IntentStatus.RESOLVED:
            return ExecutionPlan(
                intent=intent.intent_type.value,
                safe_to_execute=False,
                reasoning="Intent is not resolved.",
            )

        plan = ExecutionPlan(
            intent=intent.intent_type.value,
        )

        if intent.intent_type == IntentType.RENAME:

            source = intent.entities[0].value
            destination = intent.entities[1].value

            plan.steps.append(
                ExecutionStep(
                    action="rename",
                    parameters={
                        "source": source,
                        "destination": destination,
                    },
                )
            )

        elif intent.intent_type == IntentType.DELETE:

            target = intent.entities[0].value

            plan.requires_confirmation = True

            plan.steps.append(
                ExecutionStep(
                    action="delete",
                    parameters={
                        "target": target,
                    },
                )
            )

        elif intent.intent_type == IntentType.MOVE:

            source = intent.entities[0].value
            destination = intent.entities[1].value

            plan.steps.append(
                ExecutionStep(
                    action="move",
                    parameters={
                        "source": source,
                        "destination": destination,
                    },
                )
            )

        elif intent.intent_type == IntentType.SEARCH:

            query = intent.entities[0].value

            plan.steps.append(
                ExecutionStep(
                    action="search",
                    parameters={
                        "query": query,
                    },
                )
            )

        else:

            plan.safe_to_execute = False
            plan.reasoning = (
                f"No rule exists for '{intent.intent_type.value}'."
            )

        return plan