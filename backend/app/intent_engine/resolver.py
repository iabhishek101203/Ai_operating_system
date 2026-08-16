"""
AI Operating System - Intent Resolver

The resolver converts a validated and normalized ParsedIntent
into a fully resolved intent ready for execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.intent_engine.models import ParsedIntent


class IntentResolver(ABC):
    """
    Base interface for all intent resolvers.
    """

    @abstractmethod
    def resolve(self, intent: ParsedIntent) -> ParsedIntent:
        """
        Resolve entities into their canonical runtime representation.
        """
        raise NotImplementedError