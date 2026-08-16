from app.intent_engine.enums import IntentType
from app.intent_engine.rule_classifier import RuleBasedClassifier


def test_rule_classifier_rename():
    classifier = RuleBasedClassifier()

    result = classifier.classify(
        "Rename report.txt to final.txt"
    )

    assert result == IntentType.RENAME


def test_rule_classifier_delete():
    classifier = RuleBasedClassifier()

    result = classifier.classify(
        "Delete notes.txt"
    )

    assert result == IntentType.DELETE


def test_rule_classifier_search():
    classifier = RuleBasedClassifier()

    result = classifier.classify(
        "Find every PDF in Downloads"
    )

    assert result == IntentType.SEARCH


def test_rule_classifier_unknown():
    classifier = RuleBasedClassifier()

    result = classifier.classify(
        "Tell me a joke"
    )

    assert result == IntentType.UNKNOWN