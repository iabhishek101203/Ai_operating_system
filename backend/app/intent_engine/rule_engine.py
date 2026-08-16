"""
Rule-Based Intent Engine.

Coordinates all stages of the rule-based intent pipeline.
"""

from __future__ import annotations

from app.intent_engine.engine import IntentEngine
from app.intent_engine.models import ParsedIntent

from app.intent_engine.rule_classifier import RuleBasedClassifier
from app.intent_engine.rule_extractor import RuleBasedExtractor
from app.intent_engine.rule_validator import RuleBasedValidator
from app.intent_engine.rule_normalizer import RuleBasedNormalizer
from app.intent_engine.rule_resolver import RuleBasedResolver


class RuleBasedIntentEngine(IntentEngine):
    """
    Complete deterministic intent engine.
    """

    def __init__(self):
        self.classifier = RuleBasedClassifier()
        self.extractor = RuleBasedExtractor()
        self.validator = RuleBasedValidator()
        self.normalizer = RuleBasedNormalizer()
        self.resolver = RuleBasedResolver()

    def classify(self, text: str):
        return self.classifier.classify(text)

    def extract(self, text: str):
        return self.extractor.extract(text)

    def validate(self, intent: ParsedIntent):
        return self.validator.validate(intent)

    def normalize(self, intent: ParsedIntent):
        return self.normalizer.normalize(intent)

    def resolve(self, intent: ParsedIntent):
        return self.resolver.resolve(intent)

    def parse(self, text: str) -> ParsedIntent:
        """
        Full rule-based parsing pipeline.
        """

        intent_type = self.classify(text)

        entities = self.extract(text)

        intent = ParsedIntent(
            raw_text=text,
            normalized_text=text.lower().strip(),
            intent_type=intent_type,
            entities=entities,
        )

        intent = self.validate(intent)
        intent = self.normalize(intent)
        intent = self.resolve(intent)

        return intent