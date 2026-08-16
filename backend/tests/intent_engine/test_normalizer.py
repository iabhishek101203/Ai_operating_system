from app.intent_engine.enums import EntityType
from app.intent_engine.models import (
    IntentEntity,
    ParsedIntent,
)
from app.intent_engine.rule_normalizer import RuleBasedNormalizer


def test_directory_normalization():
    normalizer = RuleBasedNormalizer()

    intent = ParsedIntent(
        raw_text="move report.txt to downloads",
        normalized_text="move report.txt to downloads",
        entities=[
            IntentEntity(
                type=EntityType.DIRECTORY,
                value="downloads",
                confidence=1.0,
            )
        ],
    )

    result = normalizer.normalize(intent)

    assert result.entities[0].value == "Downloads"


def test_extension_normalization():
    normalizer = RuleBasedNormalizer()

    intent = ParsedIntent(
        raw_text="delete .PDF",
        normalized_text="delete .PDF",
        entities=[
            IntentEntity(
                type=EntityType.FILE_EXTENSION,
                value=".PDF",
                confidence=1.0,
            )
        ],
    )

    result = normalizer.normalize(intent)

    assert result.entities[0].value == ".pdf"


def test_filename_trim():
    normalizer = RuleBasedNormalizer()

    intent = ParsedIntent(
        raw_text="rename",
        normalized_text="rename",
        entities=[
            IntentEntity(
                type=EntityType.FILE,
                value=" report.txt ",
                confidence=1.0,
            )
        ],
    )

    result = normalizer.normalize(intent)

    assert result.entities[0].value == "report.txt"