"""
AI Operating System - Entity Extractor

Defines the contract for all entity extractors.

An extractor identifies entities such as files, folders,
extensions, and project names from a user's request.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.intent_engine.models import IntentEntity


class EntityExtractor(ABC):
    """
    Base interface for all entity extractors.
    """

    @abstractmethod
    def extract(self, text: str) -> list[IntentEntity]:
        """
        Extract entities from natural language.

        Example:
            Input:
                "Rename report.txt to final.txt"

            Output:
                [
                    IntentEntity(FILE, "report.txt"),
                    IntentEntity(FILE, "final.txt")
                ]
        """
        raise NotImplementedError