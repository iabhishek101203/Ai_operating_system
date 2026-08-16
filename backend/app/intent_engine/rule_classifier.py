"""
Rule-Based Intent Classifier.

A lightweight classifier used when no LLM is available.
Useful for testing, offline execution, and fallback behavior.
"""

from __future__ import annotations

import re

from app.intent_engine.classifier import IntentClassifier
from app.intent_engine.enums import IntentType


class RuleBasedClassifier(IntentClassifier):
    _RULES = [
        (IntentType.RENAME, r"\b(rename|change name|rename file)\b"),
        (IntentType.DELETE, r"\b(delete|remove|erase)\b"),
        (IntentType.MOVE, r"\b(move|transfer)\b"),
        (IntentType.SEARCH, r"\b(find|search|locate|look for)\b"),
    ]

    def classify(self, text: str) -> IntentType:
        text = text.lower().strip()

        for intent, pattern in self._RULES:
            if re.search(pattern, text):
                return intent

        return IntentType.UNKNOWN