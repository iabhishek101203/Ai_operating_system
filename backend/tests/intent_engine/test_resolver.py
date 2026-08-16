from app.intent_engine.enums import (
    IntentStatus,
    IntentType,
)
from app.intent_engine.models import ParsedIntent
from app.intent_engine.rule_resolver import RuleBasedResolver


def test_valid_intent_is_resolved():
    resolver = RuleBasedResolver()

    intent = ParsedIntent(
        raw_text="Delete report.txt",
        normalized_text="delete report.txt",
        intent_type=IntentType.DELETE,
        status=IntentStatus.VALIDATED,
    )

    result = resolver.resolve(intent)

    assert result.status == IntentStatus.RESOLVED


def test_failed_intent_is_not_resolved():
    resolver = RuleBasedResolver()

    intent = ParsedIntent(
        raw_text="Delete",
        normalized_text="delete",
        intent_type=IntentType.DELETE,
        status=IntentStatus.FAILED,
    )

    result = resolver.resolve(intent)

    assert result.status == IntentStatus.FAILED