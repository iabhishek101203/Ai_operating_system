"""
Rule-Based Intent Normalizer.
"""

from __future__ import annotations

from app.intent_engine.enums import EntityType
from app.intent_engine.models import ParsedIntent
from app.intent_engine.normalizer import IntentNormalizer


class RuleBasedNormalizer(IntentNormalizer):

    DIRECTORY_MAP = {
        "downloads": "Downloads",
        "documents": "Documents",
        "desktop": "Desktop",
        "pictures": "Pictures",
        "music": "Music",
        "videos": "Videos",
    }

    def normalize(self, intent: ParsedIntent) -> ParsedIntent:

        for entity in intent.entities:

            if entity.type == EntityType.FILE:
                entity.value = entity.value.strip()

            elif entity.type == EntityType.FILE_EXTENSION:
                entity.value = entity.value.lower()

            elif entity.type == EntityType.DIRECTORY:
                key = entity.value.lower()

                if key in self.DIRECTORY_MAP:
                    entity.value = self.DIRECTORY_MAP[key]

        return intent