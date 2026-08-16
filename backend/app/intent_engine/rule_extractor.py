"""
Rule-Based Entity Extractor.

Extracts filesystem-related entities using regular expressions.
"""

from __future__ import annotations

import re

from app.intent_engine.enums import EntityType
from app.intent_engine.extractor import EntityExtractor
from app.intent_engine.models import IntentEntity


class RuleBasedExtractor(EntityExtractor):
    FILE_PATTERN = re.compile(
        r"\b[\w\-]+\.(txt|pdf|docx|doc|csv|json|py|java|cpp|md|png|jpg|jpeg)\b",
        re.IGNORECASE,
    )

    DIRECTORY_PATTERN = re.compile(
        r"\b(Downloads|Documents|Desktop|Pictures|Music|Videos)\b",
        re.IGNORECASE,
    )

    EXTENSION_PATTERN = re.compile(
    r"(?<![\w-])\.(txt|pdf|docx|doc|csv|json|py|java|cpp|md|png|jpg|jpeg)\b",
    re.IGNORECASE,
    )

    def extract(self, text: str) -> list[IntentEntity]:
        entities: list[IntentEntity] = []

        # Files
        for match in self.FILE_PATTERN.finditer(text):
            entities.append(
                IntentEntity(
                    type=EntityType.FILE,
                    value=match.group(),
                    confidence=1.0,
                )
            )

        # Directories
        for match in self.DIRECTORY_PATTERN.finditer(text):
            entities.append(
                IntentEntity(
                    type=EntityType.DIRECTORY,
                    value=match.group(),
                    confidence=0.95,
                )
            )

        # File extensions
        for match in self.EXTENSION_PATTERN.finditer(text):
            entities.append(
                IntentEntity(
                    type=EntityType.FILE_EXTENSION,
                    value=match.group(),
                    confidence=0.90,
                )
            )

        return entities