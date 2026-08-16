"""
AI Operating System - Intent Validator

Defines the contract for validating parsed intents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.intent_engine.models import ParsedIntent


class IntentValidator(ABC):
    """
    Base interface for all intent validators.
    """

    @abstractmethod
    def validate(self, intent: ParsedIntent) -> ParsedIntent:
        """
        Validate a parsed intent.

        Returns the updated ParsedIntent.
        """
        raise NotImplementedError