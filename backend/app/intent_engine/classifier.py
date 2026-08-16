"""
AI Operating System - Intent Classifier
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.intent_engine.enums import IntentType


class IntentClassifier(ABC):
    @abstractmethod
    def classify(self, text: str) -> IntentType:
        """
        Determine the primary intent of a user's request.
        """
        raise NotImplementedError