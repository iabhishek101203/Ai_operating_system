from app.intent_engine.enums import (
    EntityType,
    IntentStatus,
    IntentType,
)
from app.intent_engine.models import (
    IntentEntity,
    ParsedIntent,
)
from app.intent_engine.rule_validator import RuleBasedValidator


def test_valid_rename():
    validator = RuleBasedValidator()

    intent = ParsedIntent(
        raw_text="Rename report.txt to final.txt",
        normalized_text="rename report.txt to final.txt",
        intent_type=IntentType.RENAME,
        entities=[
            IntentEntity(
                type=EntityType.FILE,
                value="report.txt",
                confidence=1.0,
            ),
            IntentEntity(
                type=EntityType.FILE,
                value="final.txt",
                confidence=1.0,
            ),
        ],
    )

    validated = validator.validate(intent)

    assert validated.status == IntentStatus.VALIDATED
    assert validated.clarification.required is False


def test_invalid_rename():
    validator = RuleBasedValidator()

    intent = ParsedIntent(
        raw_text="Rename report.txt",
        normalized_text="rename report.txt",
        intent_type=IntentType.RENAME,
        entities=[
            IntentEntity(
                type=EntityType.FILE,
                value="report.txt",
                confidence=1.0,
            )
        ],
    )

    validated = validator.validate(intent)

    assert validated.status == IntentStatus.FAILED
    assert validated.clarification.required is True


def test_valid_delete():
    validator = RuleBasedValidator()

    intent = ParsedIntent(
        raw_text="Delete report.txt",
        normalized_text="delete report.txt",
        intent_type=IntentType.DELETE,
        entities=[
            IntentEntity(
                type=EntityType.FILE,
                value="report.txt",
                confidence=1.0,
            )
        ],
    )

    validated = validator.validate(intent)

    assert validated.status == IntentStatus.VALIDATED


def test_invalid_delete():
    validator = RuleBasedValidator()

    intent = ParsedIntent(
        raw_text="Delete",
        normalized_text="delete",
        intent_type=IntentType.DELETE,
    )

    validated = validator.validate(intent)

    assert validated.status == IntentStatus.FAILED
    assert validated.clarification.required is True


def test_valid_move():
    validator = RuleBasedValidator()

    intent = ParsedIntent(
        raw_text="Move report.txt to Downloads",
        normalized_text="move report.txt to downloads",
        intent_type=IntentType.MOVE,
        entities=[
            IntentEntity(
                type=EntityType.FILE,
                value="report.txt",
                confidence=1.0,
            ),
            IntentEntity(
                type=EntityType.DIRECTORY,
                value="Downloads",
                confidence=1.0,
            ),
        ],
    )

    validated = validator.validate(intent)

    assert validated.status == IntentStatus.VALIDATED


def test_unknown_intent():
    validator = RuleBasedValidator()

    intent = ParsedIntent(
        raw_text="Tell me a joke",
        normalized_text="tell me a joke",
        intent_type=IntentType.UNKNOWN,
    )

    validated = validator.validate(intent)

    assert validated.status == IntentStatus.FAILED
    assert validated.clarification.required is True