import pytest

from app.intent_engine.engine import IntentEngine


def test_intent_engine_is_abstract():
    with pytest.raises(TypeError):
        IntentEngine()