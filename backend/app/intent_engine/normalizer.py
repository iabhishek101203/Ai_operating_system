"""
AI Operating System - Intent Normalizer
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.intent_engine.models import ParsedIntent


class IntentNormalizer(ABC):
    """
    Base interface for intent normalization.
    """

    @abstractmethod
    def normalize(self, intent: ParsedIntent) -> ParsedIntent:
        """
        Normalize extracted entities into a canonical form.
        """
        raise NotImplementedError