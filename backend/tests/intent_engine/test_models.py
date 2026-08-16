from app.intent_engine.enums import IntentType
from app.intent_engine.models import ParsedIntent


def test_create_parsed_intent():
    intent = ParsedIntent(
        raw_text="Rename demo.txt to final.txt",
        normalized_text="rename demo.txt to final.txt",
        intent_type=IntentType.RENAME,
        confidence=0.97,
    )

    assert intent.intent_type == IntentType.RENAME
    assert intent.raw_text.startswith("Rename")
    assert intent.confidence > 0.9