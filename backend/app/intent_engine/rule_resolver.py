"""
Rule-Based Intent Resolver.
"""

from __future__ import annotations

from app.intent_engine.enums import IntentStatus
from app.intent_engine.models import ParsedIntent
from app.intent_engine.resolver import IntentResolver


class RuleBasedResolver(IntentResolver):
    """
    Deterministic resolver implementation.

    Future versions will resolve:
    - Relative paths
    - User directories
    - Environment variables
    - Project aliases
    - File existence
    """

    def resolve(self, intent: ParsedIntent) -> ParsedIntent:
        # Don't resolve invalid intents
        if intent.status != IntentStatus.VALIDATED:
            return intent

        # Future logic goes here

        intent.status = IntentStatus.RESOLVED

        return intent