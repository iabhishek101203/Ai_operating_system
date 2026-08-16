"""
Rule-Based Intent Validator.

Performs deterministic validation on ParsedIntent objects.
"""

from __future__ import annotations

from app.intent_engine.enums import (
    ClarificationReason,
    EntityType,
    IntentStatus,
    IntentType,
)
from app.intent_engine.models import ParsedIntent
from app.intent_engine.validator import IntentValidator


class RuleBasedValidator(IntentValidator):
    """
    Validates ParsedIntent objects using deterministic rules.
    """

    def validate(self, intent: ParsedIntent) -> ParsedIntent:
        files = [e for e in intent.entities if e.type == EntityType.FILE]
        directories = [
            e for e in intent.entities if e.type == EntityType.DIRECTORY
        ]

        # Unknown intent
        if intent.intent_type == IntentType.UNKNOWN:
            intent.status = IntentStatus.FAILED
            intent.clarification.required = True
            intent.clarification.reason = ClarificationReason.UNKNOWN
            intent.clarification.question = (
                "I couldn't understand your request."
            )
            return intent

        # Rename
        if intent.intent_type == IntentType.RENAME:
            if len(files) == 0:
                intent.status = IntentStatus.FAILED
                intent.clarification.required = True
                intent.clarification.reason = (
                    ClarificationReason.MISSING_FILENAME
                )
                intent.clarification.question = (
                    "Which file would you like to rename?"
                )
                return intent

            if len(files) == 1:
                intent.status = IntentStatus.FAILED
                intent.clarification.required = True
                intent.clarification.reason = (
                    ClarificationReason.MISSING_DESTINATION
                )
                intent.clarification.question = (
                    "What should the new filename be?"
                )
                return intent

        # Delete
        if intent.intent_type == IntentType.DELETE:
            if len(files) == 0 and len(directories) == 0:
                intent.status = IntentStatus.FAILED
                intent.clarification.required = True
                intent.clarification.reason = (
                    ClarificationReason.MISSING_FILENAME
                )
                intent.clarification.question = (
                    "Which file or directory should be deleted?"
                )
                return intent

        # Move
        if intent.intent_type == IntentType.MOVE:
            if len(files) == 0:
                intent.status = IntentStatus.FAILED
                intent.clarification.required = True
                intent.clarification.reason = (
                    ClarificationReason.MISSING_FILENAME
                )
                intent.clarification.question = (
                    "Which file should be moved?"
                )
                return intent

            if len(directories) == 0:
                intent.status = IntentStatus.FAILED
                intent.clarification.required = True
                intent.clarification.reason = (
                    ClarificationReason.MISSING_DESTINATION
                )
                intent.clarification.question = (
                    "Where should the file be moved?"
                )
                return intent

        # Search
        if intent.intent_type == IntentType.SEARCH:
            if not intent.entities:
                intent.status = IntentStatus.FAILED
                intent.clarification.required = True
                intent.clarification.reason = (
                    ClarificationReason.MISSING_FILENAME
                )
                intent.clarification.question = (
                    "What would you like to search for?"
                )
                return intent

        intent.status = IntentStatus.VALIDATED
        return intent