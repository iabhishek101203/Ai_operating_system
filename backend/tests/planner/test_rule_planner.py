from app.intent_engine.enums import (
    EntityType,
    IntentStatus,
    IntentType,
)
from app.intent_engine.models import (
    IntentEntity,
    ParsedIntent,
)

from app.planner.rule_planner import RuleBasedPlanner


def test_rename_plan():

    planner = RuleBasedPlanner()

    intent = ParsedIntent(
        raw_text="Rename report.txt to final.txt",
        normalized_text="rename report.txt to final.txt",
        intent_type=IntentType.RENAME,
        status=IntentStatus.RESOLVED,
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

    plan = planner.create_plan(intent)

    assert len(plan.steps) == 1
    assert plan.steps[0].action == "rename"


def test_delete_plan():

    planner = RuleBasedPlanner()

    intent = ParsedIntent(
        raw_text="Delete report.txt",
        normalized_text="delete report.txt",
        intent_type=IntentType.DELETE,
        status=IntentStatus.RESOLVED,
        entities=[
            IntentEntity(
                type=EntityType.FILE,
                value="report.txt",
                confidence=1.0,
            )
        ],
    )

    plan = planner.create_plan(intent)

    assert plan.requires_confirmation is True
    assert plan.steps[0].action == "delete"


def test_unresolved_intent():

    planner = RuleBasedPlanner()

    intent = ParsedIntent(
        raw_text="Delete",
        normalized_text="delete",
        intent_type=IntentType.DELETE,
        status=IntentStatus.FAILED,
    )

    plan = planner.create_plan(intent)

    assert plan.safe_to_execute is False