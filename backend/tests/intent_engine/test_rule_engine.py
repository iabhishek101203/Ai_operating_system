from app.intent_engine.enums import (
    IntentStatus,
    IntentType,
)
from app.intent_engine.rule_engine import RuleBasedIntentEngine


def test_parse_rename():
    engine = RuleBasedIntentEngine()

    result = engine.parse(
        "Rename report.txt to final.txt"
    )

    assert result.intent_type == IntentType.RENAME
    assert result.status == IntentStatus.RESOLVED
    assert len(result.entities) >= 2


def test_parse_delete():
    engine = RuleBasedIntentEngine()

    result = engine.parse(
        "Delete report.txt"
    )

    assert result.intent_type == IntentType.DELETE
    assert result.status == IntentStatus.RESOLVED


def test_parse_unknown():
    engine = RuleBasedIntentEngine()

    result = engine.parse(
        "Tell me a joke"
    )

    assert result.intent_type == IntentType.UNKNOWN
    assert result.status == IntentStatus.FAILED